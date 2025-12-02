#测试before加了误差过滤
import json  
import re  
from datetime import datetime, timedelta  
from typing import Any, Dict, Optional, List, Literal, Union  
from typing import Annotated
from langgraph.graph import add_messages
from pydantic import BaseModel  
from langgraph.graph import StateGraph, END  
from langchain.prompts import ChatPromptTemplate  
from langchain_openai import ChatOpenAI
from sql_verify import PostgresQueryExecutor
import torch
from typing import Dict, Any, List, Tuple
import sys
sys.path.append('/home/bbx')
from ICME_Weather.Code.model_library.test_pred import preds_30days_data
from ICME_Weather.Code.model_library import models 
from ICME_Weather.Code.model_library.models import iTransformer
import bert_train_test
from typing import Annotated, Optional, Dict, Any, List, Literal
from pydantic import BaseModel
import numpy as np
import math
import os
from tqdm import tqdm
from sklearn.metrics import mean_squared_error, mean_absolute_error

# custom_base_url = "http://fastapi.bnuzh.top:8080/v1"
# model_name = 'glm-45v'
# api_key = 'sk-FastAPIlS1S0plLVt0g0FXG4bGSk1xlT0zm0COvk3Gl6PKBq'

# custom_base_url = "http://fastapi.bnuzh.top:8080/v1"
# model_name = 'gpt-oss-120b'
# api_key = 'sk-FastAPIlS1S0plLVt0g0FXG4bGSk1xlT0zm0COvk3Gl6PKBq'

# custom_base_url = "http://fastapi.bnuzh.top:8080/v1"
# model_name = 'qwen3-30b-a3b'
# api_key = 'sk-FastAPIlS1S0plLVt0g0FXG4bGSk1xlT0zm0COvk3Gl6PKBq'

custom_base_url = "http://fastapi.bnuzh.top:8080/v1"
model_name = 'glm-45-air'
api_key = 'sk-FastAPIlS1S0plLVt0g0FXG4bGSk1xlT0zm0COvk3Gl6PKBq'

# custom_base_url = "http://fastapi.bnuzh.top:8080/v1"
# model_name = 'qwen3-8b'
# api_key = 'sk-FastAPIlS1S0plLVt0g0FXG4bGSk1xlT0zm0COvk3Gl6PKBq'

# custom_base_url = "http://fastapi.bnuzh.top:8080/v1"
# model_name = 'qwq-32b'
# api_key = 'sk-FastAPIlS1S0plLVt0g0FXG4bGSk1xlT0zm0COvk3Gl6PKBq'

llm = ChatOpenAI(model_name=model_name, openai_api_key=api_key, base_url=custom_base_url)

# ========== BERT（可选）==========  
import torch  
from transformers import BertTokenizer  

BERT_PATH = '/home/bbx/code/stock_generate/bert-base-cased'  
model_path = '/home/bbx/code/stock_generate/model/bert.pt'  

tokenizer = BertTokenizer.from_pretrained(BERT_PATH)  
bert_model = torch.load(model_path, map_location="cpu")  
use_cuda = torch.cuda.is_available()  
device = torch.device("cuda" if use_cuda else "cpu")  
if use_cuda:  
    bert_model = bert_model.cuda()  
bert_model.eval()  

slots_num = {  
    'O': 0,  
    'B-year': 1,  
    'I-year': 2,  
    'B-month': 3,  
    'I-month': 4,  
    'B-day': 5,  
    'I-day': 6,  
    'B-stock_name': 7,  
    'I-stock_name': 8,
    'B-time': 9,
    'I-time': 10,
    'B-number': 11  
} 

# ========== 意图与槽位映射 ==========

def intent2label() -> Dict[str, int]:
    return {
        'Opening Price Inquiry': 0,
        'Closing Price Inquiry': 1,
        'Stock Trading Volume Inquiry': 2,
        'Stock Price Prediction': 3,
        'Stock Trend Prediction': 4,
        'Stock Extremum Prediction': 5
    }

label2intent: Dict[int, str] = {v: k for k, v in intent2label().items()}
label_map_slots: Dict[int, str] = {v: k for k, v in slots_num.items()}

def id_to_slot_label(slot_id: int) -> str:
    return label_map_slots.get(slot_id, 'O')

def decode_intents(outputs) -> Tuple[List[int], int]:
    intent_probility = outputs[0].view(-1)
    _, intent_idx = torch.topk(intent_probility, k=2, dim=0)
    intent_idx = intent_idx.cpu()
    intent_num_probility = outputs[1].argmax().item()
    if intent_num_probility == 0:
        intent_idx = intent_idx[:1]
    return intent_idx.tolist(), intent_num_probility

def decode_slots(outputs, tokens_len: int) -> List[int]:
    slots_probility = outputs[2].argmax(dim=2).view(-1)
    pred_slots_num = slots_probility[1:tokens_len-1].cpu().tolist()
    return pred_slots_num

def replace_hashes_and_convert(tokens, replacement=''):  
    tokens_str = ' '.join(tokens)  
    tokens_str_replaced = tokens_str.replace('##', replacement)  
    new_tokens = tokens_str_replaced.split()  
    return new_tokens

def restore_keywords_from_tokens(tokens, token_slot):  
    keywords = []  
    current_tokens = []  
    current_label = None  
    for token, slot in zip(tokens, token_slot):  
        if slot.startswith('B-'):  
            if current_tokens and current_label:  
                keywords.append((''.join(current_tokens), current_label))  
            current_label = slot[2:]  
            current_tokens = [token]  
        elif slot.startswith('I-') and current_label == slot[2:]:  
            current_tokens.append(token)  
        else:  
            if current_tokens and current_label:  
                keywords.append((''.join(current_tokens), current_label))  
                current_tokens = []  
                current_label = None  
    if current_tokens and current_label:  
        keywords.append((''.join(current_tokens), current_label))  
    return keywords 

def postprocess_slot_keywords(question_tokens: List[str], pred_slot_labels: List[str]) -> Dict[str, Any]:
    new_token_list = replace_hashes_and_convert(question_tokens)
    fragments = restore_keywords_from_tokens(new_token_list, pred_slot_labels)
    slots_struct: Dict[str, Any] = {}
    for text, label in fragments:
        text_norm = text.strip()
        if not text_norm:
            continue
        if label in ("year", "month", "day"):
            text_norm = re.sub(r"[^0-9]", "", text_norm)
        slots_struct[label] = text_norm
    y, m, d = slots_struct.get("year"), slots_struct.get("month"), slots_struct.get("day")
    if y and m and d:
        try:
            slots_struct["date"] = datetime(int(y), int(m), int(d)).date().isoformat()
        except Exception:
            pass
    return slots_struct

def bert_infer_intent_slots_v2(query: str) -> Dict[str, Any]:
    encoded = tokenizer(query, return_tensors='pt')
    input_ids = encoded['input_ids'].to(device)
    attention_mask = encoded['attention_mask'].to(device)
    tokens = tokenizer.convert_ids_to_tokens(encoded['input_ids'][0])
    tokens_len = encoded['input_ids'].shape[1]

    with torch.no_grad():
        outputs = bert_model(input_ids, attention_mask)

    intent_indices, intent_num_label = decode_intents(outputs)
    intents_map = intent2label()
    inv_intents_map = {v: k for k, v in intents_map.items()}
    intents = [inv_intents_map.get(i, f"Intent_{i}") for i in intent_indices]

    slot_ids = decode_slots(outputs, tokens_len=tokens_len)
    slot_labels = [id_to_slot_label(i) for i in slot_ids]
    slots_struct = postprocess_slot_keywords(tokens[1:tokens_len-1], slot_labels)

    return {
        "intent": intents if len(intents) > 1 else intents[0],
        "intent_num": intent_num_label,
        "slots": slots_struct,
        "token_slots": slot_labels
    }

# ========== 通用工具 ==========  
def load_templates(path: str) -> dict:  
    with open(path, 'r', encoding='utf-8') as f:  
        raw = json.load(f)  
    fixed = {}  
    for k, v in raw.items():  
        fixed[k.strip()] = v  
    return fixed  

def safe_json(text: str) -> Dict[str, Any]:  
    try:  
        return json.loads(text)  
    except Exception:  
        return {}  

def call_llm_with_template(template_str: str, variables: Dict[str, Any]) -> str:
    # NEW: 轻量变量名兼容：input_query <-> query（防止历史模板遗留命名）
    if "{input_query}" in template_str and "input_query" not in variables and "query" in variables:
        variables = dict(variables)
        variables["input_query"] = variables["query"]
    if "{query}" in template_str and "query" not in variables and "input_query" in variables:
        variables = dict(variables)
        variables["query"] = variables["input_query"]

    # 注意：不为 pred_answer 做兜底注入，保证它只在预测流最终节点存在
    prompt = ChatPromptTemplate.from_template(template_str)
    resp = (prompt | llm).invoke(variables)
    return str(resp.content).strip() 

def ensure_forecast_dates(anchor_date: str, horizon: int, values) -> Dict[str, Any]:
    # 统一类型
    if isinstance(values, np.ndarray):
        values = values.tolist()
    elif values is not None and not isinstance(values, list):
        values = list(values)

    # 基础校验
    if values is None or len(values) == 0:
        return {"dates": [], "values": [], "error": "empty_values"}

    # 锚点解析
    try:
        base = datetime.fromisoformat(anchor_date)  # YYYY-MM-DD
    except Exception as e:
        print(f"[ERROR] ensure_forecast_dates invalid anchor_date={anchor_date}: {e}")
        return {"dates": [], "values": [], "error": "invalid_anchor_date"}

    # 生成日期（从锚点次日开始）
    dates = [(base + timedelta(days=i)).date().isoformat() for i in range(1, horizon + 1)]
    dates = dates[:len(values)]
    return {"dates": dates, "values": values, "error": None}

# 模板加载
TEMPLATES_TAKE = load_templates('/home/bbx/code/stock_generate/pred_prompt_english.json')       # 仅预测流使用：最终结果生成
TEMPLATES_HISTORY = load_templates('/home/bbx/code/stock_generate/history_sql_prompt_english.json')   # 历史SQL（预测流） 
TEMPLATES_RETRIVAL = load_templates('/home/bbx/code/stock_generate/retrival_prompt.json')        # 检索表名  
TEMPLATES_DIRECT  = load_templates('/home/bbx/code/stock_generate/sql_prompt_english.json')      # 查询模块直接SQL  

# ========== LangGraph 状态 ==========  

# 定义 reducer 函数：总是使用最新值
def use_latest(old_value, new_value):
    """Reducer that always uses the latest value"""
    return new_value

# 定义 reducer 函数：合并字典
def merge_dict(old_value, new_value):
    """Reducer that merges dictionaries"""
    if old_value is None:
        return new_value
    if new_value is None:
        return old_value
    return {**old_value, **new_value}

# 改造后的 AgentState，所有字段都使用 Annotated 允许多次写入
class AgentState(BaseModel):
    # 核心字段 - 使用 Annotated 允许多次写入，取最后值
    query: Annotated[str, use_latest]
    raw_data: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    # NLU 相关字段
    intent: Annotated[Optional[str], use_latest] = None
    slots: Annotated[Optional[Dict[str, Any]], merge_dict] = None  # 槽位可能需要合并
    
    # 流程控制
    flow: Annotated[Optional[Literal["PredictFlow", "QueryFlow", "PredictReasoningFlow"]], use_latest] = None
    
    # 表名
    table_name: Annotated[Optional[str], use_latest] = None
    
    # SQL 查询流相关
    sql_statement: Annotated[Optional[str], use_latest] = None
    cleaned_sql: Annotated[Optional[str], use_latest] = None
    table_results: Annotated[Optional[Any], use_latest] = None
    predict_SQL_answer: Annotated[Optional[Any], use_latest] = None
    
    # 历史数据查询相关
    history_sql: Annotated[Optional[str], use_latest] = None
    history_cleaned_sql: Annotated[Optional[str], use_latest] = None
    history_data: Annotated[Optional[List[Any]], use_latest] = None
    history_rows: Annotated[Optional[List[Any]], use_latest] = None
    history_answer: Annotated[Optional[List[List[Union[str, float]]]], use_latest] = None
    
    # 预测相关
    forecast_sql: Annotated[Optional[str], use_latest] = None
    forecast_cleaned_sql: Annotated[Optional[str], use_latest] = None
    pred_answer: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    # 日期解析相关
    date_parse: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    # 预测答案
    predict_answer: Annotated[Optional[str], use_latest] = None
    extracted_value: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    # 最终答案
    final_answer: Annotated[Optional[str], use_latest] = None

    class Config:
        # Pydantic v2 配置
        arbitrary_types_allowed = True


# ========== 节点：NLU ==========  
def nlu_node(state: AgentState) -> AgentState:
    # 总是使用 BERT 模型基于 query 进行预测
    nlu = bert_infer_intent_slots_v2(state.query)

    WHITELIST_INTENTS = {
        "Opening Price Inquiry",
        "Closing Price Inquiry",
        "Stock Trading Volume Inquiry",
        "Stock Price Prediction",
        "Stock Trend Prediction",
        "Stock Extremum Prediction",
    }
    DEFAULT_INTENT = "Opening Price Inquiry"

    intent = nlu.get("intent")

    # 只有当 intent 属于白名单时，才执行“多意图取第一个”的逻辑
    if isinstance(intent, list) and intent:
        # 如果列表中第一个就在白名单里，则取第一个
        if intent[0] in WHITELIST_INTENTS:
            state.intent = intent[0]
        else:
            # 列表中存在多个，尝试从列表中找一个属于白名单的
            picked = next((it for it in intent if it in WHITELIST_INTENTS), None)
            # 找到了就用该白名单意图；找不到就回退到默认
            state.intent = picked if picked is not None else DEFAULT_INTENT
    else:
        # intent 不是列表时：命中白名单则用之，否则回退默认
        if isinstance(intent, str) and intent in WHITELIST_INTENTS:
            state.intent = intent
        else:
            state.intent = DEFAULT_INTENT

    # 槽位字典
    state.slots = nlu.get("slots", {}) or {}
    return state

# ========== 节点：Router ==========
ROUTER_PROMPT = """
You are a routing planner for a stock QA/forecast agent.
Only output a single-line JSON object like {{\"flow\":\"QueryFlow\"}}.
Do not add any prefix (e.g., json, JSON, Result:), and do not use code fences.
Start with {{ and end with }}.
Output ONLY a single-line valid JSON object. No extra text. 

Task:
- Decide the processing flow based ONLY on the given intent.

Allowed flows:
- "PredictFlow"
- "QueryFlow"
- "PredictReasoningFlow"

Mapping rules:
- PredictFlow:
  - "Stock Price Prediction"
- PredictReasoningFlow:
  - "Stock Trend Prediction"
  - "Stock Extremum Prediction"
- QueryFlow:
  - "Opening Price Inquiry"
  - "Closing Price Inquiry"
  - "Stock Trading Volume Inquiry"

Input:
- intent: {intent}

JSON schema (exact keys only):
flow ∈ {{"PredictFlow", "QueryFlow", "PredictReasoningFlow"}}

Example (format only):
{{"flow":"QueryFlow"}}
"""

ALLOWED_FLOWS = ("PredictFlow", "QueryFlow", "PredictReasoningFlow")
DEFAULT_FLOW = "QueryFlow"

def extract_flow_from_raw(raw: str) -> str:
    """
    从 LLM 原始输出中稳健提取 flow：
    1) 直接 JSON 解析
    2) 正则提取首个 JSON 对象再解析
    3) 关键词判断
    4) 默认值
    """
    if not raw:
        return DEFAULT_FLOW

    # 1) 尝试直接解析 JSON
    try:
        obj = json.loads(raw)
        f = (obj.get("flow") or "").strip()
        if f in ALLOWED_FLOWS:
            return f
    except Exception:
        pass

    # 2) 正则抓取第一个 {...} 再解析
    m = re.search(r'\{.*?\}', raw, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            f = (obj.get("flow") or "").strip()
            if f in ALLOWED_FLOWS:
                return f
        except Exception:
            pass

    # 3) 关键词兜底（保守）
    low = raw.lower()
    if "predictflow" in low or "predict" in low:
        return "PredictFlow"
    if "queryflow" in low or "query" in low or "inquiry" in low:
        return "QueryFlow"

    # 4) 最终默认
    return DEFAULT_FLOW
def extract_after_think_router(resp):
    """
    - 若为 dict：原样返回
    - 若为 str：去掉 </think> 之前的内容，保留后半段
    """
    if isinstance(resp, dict):
        return resp
    # 自动转为字符串
    if not isinstance(resp, str):
        if hasattr(resp, 'content'):
            resp = resp.content
        else:
            resp = str(resp)
    if '</think>' in resp:
        return resp.split('</think>', 1)[1].strip()
    return resp
def _extract_first_json_object(text: str) -> str:
    """
    从包含噪声的文本中提取首个完整 JSON 对象字符串：
    - 去除 <think>...</think>
    - 去除 ```json ... ``` 或 ``` ... ``` 代码块包裹（若存在）
    - 去除开头的提示性前缀（如 'JSON', 'Result:' 等）（尽量克制）
    - 从第一个 '{' 开始，做括号配对直到匹配 '}'
    提示：此函数不进行任何容错修复（如单引号转双引号），只做结构提取。
    """
    s = text

    # 1) 去除 <think>...</think>
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL).strip()

    # 2) 若存在代码块 ```...```，优先取代码块内部
    m = re.search(r"```(?:json)?\s*(.*?)```", s, flags=re.DOTALL | re.IGNORECASE)
    if m:
        s = m.group(1).strip()

    # 3) 去掉常见前缀（克制处理，不替换内容，只清掉极少量符号性前缀）
    s = re.sub(r"^(?:json\s*:?\s*|result\s*:?\s*|output\s*:?\s*)", "", s, flags=re.IGNORECASE).strip()

    # 4) 从第一个 '{' 开始配对提取
    start = s.find('{')
    if start == -1:
        raise ValueError("[Router] No JSON object start '{' found.")
    depth = 0
    end = None
    for i, ch in enumerate(s[start:], start=start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        raise ValueError("[Router] JSON braces not balanced; missing closing '}'.")

    return s[start:end+1].strip()


def parse_router_output_strict(raw: str) -> str:
    """
    Strictly parse Router LLM output:
    - Only accept valid JSON: {"flow":"..."}
    - Clean minimal noise and extract the first JSON object
    - No fallback or keyword guessing
    - If invalid -> raise ValueError
    """
    if raw is None:
        raise ValueError("[Router] Empty response from LLM")

    text = str(raw).strip()
    # 提取首个 JSON 对象（不容错、不替换引号）
    json_str = _extract_first_json_object(text)

    try:
        obj = json.loads(json_str)
    except Exception as e:
        preview = json_str[:200].replace("\n", " ")
        raise ValueError(f"[Router] LLM output is not valid JSON: {preview} ...") from e

    if not isinstance(obj, dict):
        preview = json_str[:200].replace("\n", " ")
        raise ValueError(f"[Router] JSON root is not an object: {preview} ...")

    flow = (obj.get("flow") or "").strip()
    if flow not in ALLOWED_FLOWS:
        raise ValueError(f"[Router] Invalid 'flow' value: {flow}. Allowed: {ALLOWED_FLOWS}")

    return flow

def router_node_by_intent(state: AgentState) -> AgentState:
    router_vars = {
        "intent": (state.intent or "").strip(),
    }
    resp = call_llm_with_template(ROUTER_PROMPT, router_vars)

    # Strict parsing: no fallback
    flow = parse_router_output_strict(resp)

    print(f"[Router] flow={flow}")
    state.flow = flow
    return state

def clean_sql_statement(sql_statement):
    cleaned_sql = re.sub(r'```sql|```', '', sql_statement, flags=re.IGNORECASE)
    cleaned_sql = cleaned_sql.strip()
    cleaned_sql = re.sub(r'^(SQL:)\s*', '', cleaned_sql, flags=re.IGNORECASE)
    return cleaned_sql.strip()

def extract_after_think(resp):
    if not isinstance(resp, str):
        if hasattr(resp, 'content'):
            resp = resp.content
        else:
            resp = str(resp)
    if '</think>' in resp:
        return resp.split('</think>', 1)[1].strip()
    return resp.strip()

def retrival_table_node(state: AgentState) -> AgentState:
    intent_key = state.intent.strip() if state.intent else ""
    final_table_name = None

    # 1) 优先 LLM 检索
    if intent_key in TEMPLATES_RETRIVAL:
        template_str = TEMPLATES_RETRIVAL[intent_key]["description"]
        resp_pre = call_llm_with_template(template_str, {
            "query": state.query,
            "intent": intent_key,
            "slots": json.dumps(state.slots or {}, ensure_ascii=False),
        })
        resp = extract_after_think(resp_pre)
        candidate = (resp or "").strip()
        if candidate:
            final_table_name = candidate

    # 2) 兜底：raw_data.pred_tabel_caption
    if not final_table_name:
        final_table_name = (state.raw_data or {}).get("pred_tabel_caption")

    # 3) 兜底：slots.stock_name -> ["{stock}"]
    if not final_table_name:
        stock = (state.slots or {}).get("stock_name", "AAPL")
        final_table_name = f'["{stock}"]'

    # 只写一次
    state.table_name = final_table_name
    return state

# ========== 查询流：生成 SQL -> 清洗 -> 执行 ==========  
def build_sql_node(state: AgentState) -> AgentState:
    intent_key = state.intent.strip() if state.intent else ""
    if intent_key not in TEMPLATES_DIRECT:
        raise ValueError(f"Direct template for intent '{intent_key}' not found")
    template_str = TEMPLATES_DIRECT[intent_key]["description"]

    table_name_local = state.table_name  # 只读
    resp = call_llm_with_template(template_str, {
        "query": state.query,
        "intent": intent_key,
        "slots": json.dumps(state.slots or {}, ensure_ascii=False),
        "table_name": table_name_local
    })
    sql_statement = extract_after_think(resp)
    cleaned_sql = clean_sql_statement(clean_sql_statement(sql_statement))

    state.sql_statement = sql_statement
    state.cleaned_sql = cleaned_sql
    return state

def convert_and_format_table_results(table_results, precision=6):
    if not table_results or not isinstance(table_results, (list, tuple)):
        return []
    result = []
    for row in table_results:
        if not isinstance(row, (list, tuple)):
            continue
        new_row = []
        for val in row:
            if isinstance(val, float):
                val_str = str(val)
                if '.' in val_str and len(val_str.split('.')[1]) > precision:
                    new_row.append(round(val, precision))
                else:
                    new_row.append(val)
            elif isinstance(val, (int, str)):
                new_row.append(val)
            else:
                new_row.append(str(val))
        result.append(new_row)
    return result

def db_query_node(state: AgentState) -> AgentState:  
    dbname = 'postgres'  
    executor = PostgresQueryExecutor(database=dbname)  
    res = executor.execute_sql(state.cleaned_sql or "")  
    executor.close()  

    if isinstance(res, tuple) and len(res) == 2:  
        _, table_results = res  
    elif isinstance(res, tuple) and len(res) == 1:  
        table_results = res[0]  
    else:  
        table_results = res  

    state.table_results = table_results  
    state.predict_SQL_answer = 'null' if not table_results else convert_and_format_table_results(table_results, 6)  
    state.final_answer = json.dumps({  
        "type": "query",  
        "intent": state.intent,  
        "slots": state.slots,  
        "sql": state.cleaned_sql,  
        "result": state.predict_SQL_answer  
    }, ensure_ascii=False)  
    return state  

# ========== 预测流：历史 SQL 生成 -> 执行 ==========  
def build_history_sql_node(state: AgentState) -> AgentState:
    intent_key = state.intent.strip() if state.intent else ""
    if intent_key not in TEMPLATES_HISTORY:
        raise ValueError(f"History template for intent '{intent_key}' not found")
    template_str = TEMPLATES_HISTORY[intent_key]["description"]

    table_name = state.table_name or (state.raw_data or {}).get("pred_tabel_caption")
    if not table_name:
        stock = (state.slots or {}).get("stock_name", "AAPL")##############
        table_name = f'["{stock}"]'

    resp = call_llm_with_template(template_str, {
        "query": state.query,             # UPDATED：统一 query
        "intent": intent_key,
        "slots": json.dumps(state.slots or {}, ensure_ascii=False),
        "table_name": table_name
    })
    history_sql = extract_after_think(resp)
    history_sql = clean_sql_statement(clean_sql_statement(history_sql))

    state.history_sql = history_sql
    state.history_cleaned_sql = history_sql
    return state

def db_history_node(state: AgentState) -> AgentState:  
    dbname = 'postgres'  
    executor = PostgresQueryExecutor(database=dbname)  
    res = executor.execute_sql(state.history_cleaned_sql or "")  
    executor.close()  

    if isinstance(res, tuple) and len(res) == 2:  
        _, table_results = res  
    elif isinstance(res, tuple) and len(res) == 1:  
        table_results = res[0]  
    else:  
        table_results = res  

    state.history_rows = table_results  
    
    # 原有的 history_data 处理（数值列表）
    history_list = []  
    for r in table_results or []:  
        if isinstance(r, (list, tuple)) and len(r) >= 2:  
            try:  
                val = float(r[1])  
            except Exception:  
                val = None  
            history_list.append(val)
    print(f"history_list: {history_list}")  
    state.history_data = history_list  
    
    # ========== 新增：history_answer 处理 ==========
    history_answer = []
    for r in table_results or []:
        if isinstance(r, (list, tuple)) and len(r) >= 2:
            try:
                date_str = str(r[0])  # 日期
                value_str = str(r[1])  # 数值
                # 尝试转换为浮点数
                value = float(value_str)
                # 添加到history_answer，保持 [日期, 数值] 格式
                history_answer.append([date_str, value])
                print(f"[DEBUG] 添加到history_answer: {date_str} -> {value}")
            except Exception as e:
                print(f"[WARN] 数据转换失败: {r}, 错误: {e}")
                # 可以选择跳过或使用默认值
                # history_answer.append([str(r[0]), 0.0])  # 如果需要默认值可以取消注释
    
    print(f"history_answer: {history_answer}")
    state.history_answer = history_answer
    # ========== 新增结束 ==========
    
    return state
# ========== 预测流：小模型预测 -> 标准化 ==========  
def ts_predict_node(state: AgentState) -> AgentState:
    hist = state.history_data or []
    print(f"[DEBUG][TSPredict] hist_len={len(hist)} | head={hist[:5]}")

    pred_values: Optional[List[float]] = None
    if isinstance(hist, list) and len(hist) == 49:
        try:
            pred_values = preds_30days_data(hist)
        except Exception as e:
            print(f"[ERROR][TSPredict] preds_30days_data failed: {e}")
            state.pred_answer = {"dates": [], "values": [], "error": "predict_failed"}
            return state
    else:
        print(f"[WARN][TSPredict] unexpected hist length: {len(hist)}")
        state.pred_answer = {"dates": [], "values": [], "error": "invalid_history_length"}
        return state

    print(f"[DEBUG][TSPredict] raw_pred_values={pred_values} type={type(pred_values)}")

    # 值校验与类型统一
    if pred_values is None:
        state.pred_answer = {"dates": [], "values": [], "error": "no_pred_values"}
        return state

    if hasattr(pred_values, "tolist"):
        pred_values = pred_values.tolist()
    elif not isinstance(pred_values, list):
        pred_values = list(pred_values)

    if len(pred_values) == 0:
        state.pred_answer = {"dates": [], "values": [], "error": "empty_pred_values"}
        return state

    if any(v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) for v in pred_values):
        state.pred_answer = {"dates": [], "values": [], "error": "invalid_forecast_values"}
        return state

    # anchor 优先使用 date_parse
    anchor = None
    if getattr(state, "date_parse", None):
        anchor = state.date_parse.get("anchor_date")
    anchor = anchor or (state.slots or {}).get("end_date") or (state.slots or {}).get("date") or "2023-11-24"
    print(f"[DEBUG][TSPredict] anchor={anchor}")

    # 生成结果
    result = ensure_forecast_dates(anchor, 15, pred_values)
    print(f"[DEBUG][TSPredict] ensure -> dates[{len(result.get('dates', []))}] values[{len(result.get('values', []))}] error={result.get('error')}")
    
    # 根据意图决定是否进行周末替换
    intent = (state.intent or "").strip()
    need_weekend_replacement = intent in ["Stock Trend Prediction", "Stock Extremum Prediction"]
    
    print(f"[DEBUG][TSPredict] intent={intent}, need_weekend_replacement={need_weekend_replacement}")
    
    if need_weekend_replacement and result.get("dates") and result.get("values"):
        processed_dates = []
        processed_values = []
        
        for date_str, value in zip(result["dates"], result["values"]):
            try:
                # 解析日期
                date_obj = datetime.fromisoformat(date_str)
                # 判断是否为周六(5)或周日(6)
                if date_obj.weekday() in [5, 6]:  # 5=Saturday, 6=Sunday
                    processed_values.append(0.0)
                    print(f"[DEBUG][TSPredict] 周末处理: {date_str} (星期{date_obj.weekday()+1}) -> 0.0")
                else:
                    processed_values.append(value)
                processed_dates.append(date_str)
            except Exception as e:
                print(f"[WARN][TSPredict] 日期解析失败 {date_str}: {e}")
                processed_dates.append(date_str)
                processed_values.append(value)
        
        # 更新处理后的结果
        result["dates"] = processed_dates
        result["values"] = processed_values
        print(f"[DEBUG][TSPredict] 周末处理后: values={processed_values}")
    else:
        print(f"[DEBUG][TSPredict] 跳过周末处理，意图为: {intent}")
    
    state.pred_answer = result
    print(f"[DEBUG][TSPredict] OUT pred_answer={state.pred_answer}")
    return state

# ========== 预测流：LLM 最终结果生成（仅预测流使用的 TEMPLATES_TAKE）==========  
def safe_json_parse(text: str):
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        try:
            s, e = text.find("{"), text.rfind("}")
            if s != -1 and e != -1 and e > s:
                data = json.loads(text[s:e+1])
                return data if isinstance(data, dict) else None
        except Exception:
            pass
        return None

def extract_answer(text: str) -> str | None:
    """
    从文本中提取 'Answer：' 或 'Answer:' 后的内容。
    - 忽略大小写
    - 支持中文/英文冒号
    - 去掉前后空白
    - 默认提取到文本末尾
    """
    if not text:
        return None
    # 匹配 Answer 后跟任意空白 + 冒号（: 或 ：）+ 内容
    m = re.search(r'(?i)answer\s*[：:]\s*(.*)', text, flags=re.DOTALL)
    if not m:
        return None
    return m.group(1).strip()
def take_predict_final_node(state: AgentState) -> AgentState:
    # 仅当有预测序列时才调用
    pa = state.pred_answer or {}
    print("[DEBUG][TakePredictFinal] IN pred_answer:", state.pred_answer)
    if not pa.get("dates") or not pa.get("values"):
        # 保留 Python 路径兜底
        return state

    intent_key = (state.intent or "").strip()
    tpl = TEMPLATES_TAKE.get(intent_key) or TEMPLATES_TAKE.get("default") or {}
    template_str = tpl.get("description")
    if not template_str:
        # 没有模板则继续 Python 路径
        return state
    # 调 LLM
    vars_payload = {
        "input_query": state.query,
        "Intent": intent_key,
        "Slot": json.dumps(state.slots or {}, ensure_ascii=False),
        "pred_answer": json.dumps(state.pred_answer or {}, ensure_ascii=False)
    }
    resp_pre_pre = call_llm_with_template(template_str, vars_payload)
    print("[DEBUG][resp_pre_pre] LLM raw resp:", resp_pre_pre)
    resp_pre = extract_after_think(resp_pre_pre)
    print("[DEBUG][resp_pre] LLM raw resp:", resp_pre)


    state.predict_answer = resp_pre
    return state

def take_predict_reason_final_node(state: AgentState) -> AgentState:
    pa = state.pred_answer or {}
    print("[DEBUG][TakePredictReasoningFinal] IN pred_answer:", state.pred_answer)
    if not pa.get("dates") or not pa.get("values"):
        return state

    intent_key = (state.intent or "").strip()
    tpl = TEMPLATES_TAKE.get(intent_key) or TEMPLATES_TAKE.get("default") or {}
    template_str = tpl.get("description")
    if not template_str:
        return state

    vars_payload = {
        "input_query": state.query,
        "Slot": json.dumps(state.slots or {}, ensure_ascii=False),
        "Intent": intent_key,
        "extracted_history": json.dumps(state.history_answer or {}, ensure_ascii=False),
        "pred_answer": json.dumps(state.pred_answer or {}, ensure_ascii=False)
    }
    resp_pre_pre = call_llm_with_template(template_str, vars_payload)
    print("[DEBUG][TakePredictReasoningFinal_pre] LLM raw resp:", resp_pre_pre)
    resp_pre = extract_after_think(resp_pre_pre)
    print("[DEBUG][TakePredictReasoningFinal] LLM raw resp:", resp_pre)
    state.predict_answer = resp_pre
    return state
#执行器
def executor_node(state: AgentState) -> AgentState:
    """
    严格执行器：
    - QueryFlow: RetrivalTable -> BuildSQL -> DBQuery
    - PredictFlow: RetrivalTable -> BuildHistorySQL -> DBHistory -> TSPredict -> TakePredictFinal
    - PredictReasoningFlow: 与 PredictFlow 一致
    """
    flow = (state.flow or "").strip()
    if flow not in ("QueryFlow", "PredictFlow", "PredictReasoningFlow"):
        raise ValueError(f"[Executor] Invalid state.flow: {state.flow}")

    if flow == "QueryFlow":
        state = build_sql_node(state)
        state = db_query_node(state)
        return state

    elif flow == "PredictFlow":
        state = build_history_sql_node(state)
        state = db_history_node(state)
        state = ts_predict_node(state)
        state = take_predict_final_node(state)
        return state
    
    elif flow == "PredictReasoningFlow":
        state = build_history_sql_node(state)
        state = db_history_node(state)
        state = ts_predict_node(state)
        state = take_predict_reason_final_node(state)
        return state

# ========== 编排图 ==========  
workflow = StateGraph(AgentState)  

# 口语理解与分析流  
workflow.add_node("NLU", nlu_node)  
workflow.add_node("Router", router_node_by_intent)  
workflow.add_node("RetrivalTable", retrival_table_node)

# 查询流  
workflow.add_node("BuildSQL", build_sql_node)  
workflow.add_node("DBQuery", db_query_node)

# 预测流（历史 + 小模型 + 两种后处理路径）
workflow.add_node("BuildHistorySQL", build_history_sql_node)
workflow.add_node("DBHistory", db_history_node)
workflow.add_node("TSPredict", ts_predict_node)
# NEW: 预测流 LLM 最终生成
workflow.add_node("TakePredictFinal", take_predict_final_node)

# 入口与主干
workflow.add_node("Executor", executor_node)

workflow.set_entry_point("NLU")
workflow.add_edge("NLU", "Router")         # router_node_by_intent（基于 Prompt 设置 state.flow）
workflow.add_edge("Router", "RetrivalTable")
workflow.add_edge("RetrivalTable", "Executor")
workflow.add_edge("Executor", END)


# 查询链
workflow.add_edge("BuildSQL", "DBQuery")
workflow.add_edge("DBQuery", END)

# 预测链（两条路径并行后都指向 END）
workflow.add_edge("BuildHistorySQL", "DBHistory")
workflow.add_edge("DBHistory", "TSPredict")
# 分叉：TSPredict -> LLM 最终生成
workflow.add_edge("TSPredict", "TakePredictFinal")
# 两条路径任意一条完成都可 END（这里简单都接 END）
workflow.add_edge("TakePredictFinal", END)

app = workflow.compile()


# TEST_PATH = "/home/bbx/dataset/test_pred_merged.json"
TEST_PATH = "/home/bbx/dataset/test_merged_query_0_1050_test.json"

# ====== 基础指标 ======
def calc_acc(pred, gold):
    """修正后的准确率计算"""
    pred_processed = preprocess_data(pred)
    gold_processed = preprocess_data(gold)
    
    # 单值直接比较
    if not is_multi_value(pred) and not is_multi_value(gold):
        return 1 if pred_processed == gold_processed else 0
    
    # 多值比较（忽略顺序）
    pred_list = pred_processed if isinstance(pred_processed, list) else [pred_processed]
    gold_list = gold_processed if isinstance(gold_processed, list) else [gold_processed]
    
    return 1 if sorted(pred_list) == sorted(gold_list) else 0


def calc_col_prf(pred, gold):
    """修正后的PRF计算"""
    pred_processed = preprocess_data(pred)
    gold_processed = preprocess_data(gold)
    
    # 单值比较
    if not is_multi_value(pred) and not is_multi_value(gold):
        if pred_processed == gold_processed:
            return 1, 0, 0  # TP=1, FP=0, FN=0
        else:
            return 0, 1, 1  # TP=0, FP=1, FN=1
    
    # 多值比较（确保都是列表格式）
    pred_list = pred_processed if isinstance(pred_processed, list) else [pred_processed]
    gold_list = gold_processed if isinstance(gold_processed, list) else [gold_processed]
    
    tp = 0
    gold_copy = gold_list.copy()
    
    for item in pred_list:
        if item in gold_copy:
            tp += 1
            gold_copy.remove(item)
    
    fp = len(pred_list) - tp
    fn = len(gold_copy)
    
    return tp, fp, fn

def calc_prf1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    P = tp / (tp + fp) if (tp + fp) else 0.0
    R = tp / (tp + fn) if (tp + fn) else 0.0
    F1 = 2 * P * R / (P + R) if (P + R) else 0.0
    return P, R, F1

def mean_relative_error(y_true, y_pred, epsilon=1):
    """计算平均相对误差"""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = np.abs(y_true) > epsilon
    if np.sum(mask) == 0:
        return float("nan")
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / np.abs(y_true[mask])))


# ====== 统一数据规范化 ======
def ensure_list_table(answer: Any) -> List:
    """
    历史查询的表格答案统一为 list（list-of-rows）。兼容 'null' 字符串等。
    """
    if answer is None:
        return []
    if isinstance(answer, str):
        if answer.lower() == "null":
            return []
        try:
            val = json.loads(answer)
            return val if isinstance(val, list) else []
        except Exception:
            return []
    if isinstance(answer, list):
        return answer
    return []

# ====== 回归值提取（按你的数据结构做了通用兼容）=====
def flatten_floats(data):
    """将数据转换为浮点数列表"""
    vals = []
    if isinstance(data, (int, float)):
        vals.append(float(data))
    elif isinstance(data, str):
        for seg in re.split(r'[\s,]+', data.strip()):
            if seg:
                try:
                    vals.append(float(seg))
                except ValueError:
                    pass
    elif isinstance(data, list):
        for item in data:
            vals.extend(flatten_floats(item))
    return vals

def normalize_single_value(value):
    """标准化单值数据 - 修复None处理"""
    if value is None:
        return ""
    
    if isinstance(value, list):
        if len(value) == 1:
            return normalize_single_value(value[0])
        else:
            # 多值列表，返回原样
            return [str(item).strip() for item in value]
    
    value_str = str(value).strip()
    
    # 处理None字符串
    if value_str.lower() == 'none':
        return ""
    
    # 保持原始标签格式，不进行大小写转换
    value_lower = value_str.lower()
    if value_lower in ['rise']:
        return 'rise'
    elif value_lower in ['fall']:
        return 'fall'
    elif value_lower in ['yes']:
        return 'Yes'
    elif value_lower in ['no']:
        return 'No'
    
    # 处理换行符分隔的多值数据
    if '\n' in value_str:
        parts = [p.strip() for p in value_str.split('\n') if p.strip() and p.strip().lower() != 'none']
        if len(parts) > 1:
            return parts
        elif len(parts) == 1:
            return parts[0]
    
    # 如果是逗号或空格分隔的多值
    if ',' in value_str or (' ' in value_str and len(value_str.split()) > 1):
        parts = re.split(r'[\s,]+', value_str.strip())
        valid_parts = [p.strip() for p in parts if p.strip() and p.strip().lower() not in [',', ' ', 'none']]
        if len(valid_parts) > 1:
            return valid_parts
        elif len(valid_parts) == 1:
            return valid_parts[0]
    
    return value_str

def is_multi_value(data):
    """判断是否为多值数据"""
    if data is None:
        return False
    processed = normalize_single_value(data)
    return isinstance(processed, list) and len(processed) > 1

def preprocess_data(data):
    """统一预处理数据"""
    return normalize_single_value(data)


# 新增：专门处理多日期答案的函数
def extract_date_labels(text: str) -> List[str]:
    """从文本中提取所有日期标签"""
    if not isinstance(text, str):
        return []
    
    # 匹配日期格式 YYYY-MM-DD
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    dates = re.findall(date_pattern, text)
    return [date.strip() for date in dates]

def is_date_answer(answer: str) -> bool:
    """判断是否为日期答案"""
    dates = extract_date_labels(answer)
    return len(dates) > 0

def is_trend_answer(answer: str) -> bool:
    """判断是否为趋势答案"""
    answer_lower = answer.lower().strip()
    return answer_lower in ['rise', 'fall', 'unchange', 'yes', 'no']

def evaluate_classification_by_type(gold: str, pred: str) -> Tuple[float, float, float, int]:
    """根据答案类型评估分类任务 - 修复空值处理"""
    if pred is None:
        pred = ""
    
    # 处理趋势分类（rise/fall/unchange/yes/no）
    if is_trend_answer(gold):
        gold_label = gold.lower().strip()
        pred_label = pred.lower().strip()
        
        if gold_label == pred_label:
            return 1.0, 1.0, 1.0, 1
        else:
            return 0.0, 0.0, 0.0, 0
    
    # 处理日期匹配 - 修复多值比较
    elif is_date_answer(gold) or is_date_answer(pred):
        gold_dates = set(extract_date_labels(gold))
        pred_dates = set(extract_date_labels(pred))
        
        # 如果都是空集，认为正确
        if not gold_dates and not pred_dates:
            return 1.0, 1.0, 1.0, 1
        # 如果预测为空但真实有值，错误
        elif not pred_dates and gold_dates:
            return 0.0, 0.0, 0.0, 0
        # 如果真实为空但预测有值，错误
        elif not gold_dates and pred_dates:
            return 0.0, 0.0, 0.0, 0
        
        # 计算精确率、召回率、F1
        tp = len(gold_dates & pred_dates)
        fp = len(pred_dates - gold_dates)
        fn = len(gold_dates - pred_dates)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # 准确率：完全匹配才算正确
        acc = 1 if (gold_dates == pred_dates) else 0
        
        return precision, recall, f1, acc
    
    # 其他未知类型 - 直接字符串比较
    else:
        gold_clean = str(gold).strip().lower() if gold else ""
        pred_clean = str(pred).strip().lower() if pred else ""
        
        if gold_clean == pred_clean:
            return 1.0, 1.0, 1.0, 1
        else:
            return 0.0, 0.0, 0.0, 0
def avg(lst):
    """计算平均值"""
    return sum(lst)/len(lst) if lst else 0.0

# ====== 读取 test.json 并构造 datas ======
CACHE_PATH = "/home/bbx/dataset/main/trans/test_run_cache_glm-45-air_pred_new_main_query.jsonl"  # 每条样本一行

def load_test_as_datas_resume():
    if not os.path.exists(TEST_PATH):
        raise FileNotFoundError(f"test file not found: {TEST_PATH}")
    with open(TEST_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError("test.json should be a JSON array.")

    # 1) 收集已完成 Sample_ID
    done_ids = set()
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    if "Sample_ID" in rec:
                        done_ids.add(str(rec["Sample_ID"]))
                except Exception:
                    pass

    # 2) 处理未完成样本，随处理随写入缓存
    with open(CACHE_PATH, "a", encoding="utf-8") as fout:
        for i, item in enumerate(tqdm(items, desc="Processing test items(resume)")):
            sid = str(item.get("Sample_ID", str(i)))
            if sid in done_ids:
                continue

            q = item.get("question", "")
            ans = item.get("answer")
            intent = item.get("Intent") or item.get("intent") or ""

            try:
                out = app.invoke({"query": q, "raw_data": item})
                rec = {
                    "Sample_ID": sid,
                    "question": q,
                    "answer": ans,
                    "Intent": intent,
                    "predict_SQL_answer": out.get("predict_SQL_answer"),
                    "predict_answer": out.get("predict_answer"),
                    "pred_answer": out.get("pred_answer"),
                    "intent": out.get("intent"),
                    "flow": out.get("flow"),
                }
            except Exception as e:
                # 失败也写入，便于定位问题和下次筛选重试
                rec = {
                    "Sample_ID": sid,
                    "question": q,
                    "error": f"{type(e).__name__}: {e}"
                }

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()

    # 3) 汇总所有缓存记录作为 datas 返回，用于评测
    all_datas = []
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                all_datas.append(json.loads(line))
            except Exception:
                pass
    return all_datas

def extract_answer1(pred: str) -> str:
    """从预测答案中提取内容 - 修复None处理"""
    if pred is None:
        return ""
    if not isinstance(pred, str):
        return str(pred)
    # 匹配 "Answer:" 或 "Answer："（支持大小写），提取其后的内容
    m = re.search(r'(?i)Answer[:：]\s*(.*)', pred, flags=re.DOTALL)
    return m.group(1).strip() if m else pred.strip()
# ====== 主评测：按 Intent 分三类 ======

def evaluate_by_intent(datas: List[Dict[str, Any]]):
    """使用修复后的评测方法按意图分类评估"""
    regression_intents = {"Stock Price Prediction"}
    classification_pred_intents = {"Stock Trend Prediction", "Stock Extremum Prediction"}
    historical_intents = {"Stock Trading Volume Inquiry", "Closing Price Inquiry", "Opening Price Inquiry"}

    # 回归评估
    y_true_reg, y_pred_reg = [], []

    # 预测分类评估
    P_list_pred, R_list_pred, F1_list_pred, acc_list_pred = [], [], [], []
    
    # 历史查询评估
    P_list_hist, R_list_hist, F1_list_hist = [], [], []
    acc_count = 0
    total_predict = 0
    total_query = 0
    acc_count_predict = 0
    
    # 按类型统计
    trend_count = 0
    date_count = 0
    other_count = 0
    
    # 统计预测为None的样本
    none_predict_count = 0
    
    for data in datas:
        intent = (data.get("Intent") or "").strip()

        # 回归：Stock Price Prediction
        if intent in regression_intents:
            gold = data.get("answer")
            pred_source = data.get("predict_answer")
            
            # 检查预测结果是否有效
            if pred_source is None or pred_source == "0" or pred_source == 0:
                print(f"[回归跳过] id={data.get('Sample_ID')}: predict_answer为空或0")
                continue
                
            y_true_vals = flatten_floats(gold)
            y_pred_vals = flatten_floats(pred_source)

            if len(y_true_vals) == len(y_pred_vals) and len(y_true_vals) > 0:
                print(f"[回归详细对比] id={data.get('Sample_ID')}")
                print(f"  真实值: {y_true_vals}")
                print(f"  预测值: {y_pred_vals}")
                print(f"  差值: {[abs(t-p) for t,p in zip(y_true_vals, y_pred_vals)]}")
                
                y_true_reg.extend(y_true_vals)
                y_pred_reg.extend(y_pred_vals)
            else:
                print(f"[回归] 长度不一致/为空: id={data.get('Sample_ID')}, y_true={y_true_vals}, y_pred={y_pred_vals}")

        # 预测分类：Stock Trend/Extremum Prediction
        elif intent in classification_pred_intents:
            gold = data.get("answer")
            pred_pre = data.get("predict_answer")
            
            # 检查预测结果是否有效
            if pred_pre is None:
                print(f"[预测分类跳过] id={data.get('Sample_ID')}: predict_answer为None")
                none_predict_count += 1
                continue
                
            pred = extract_answer1(pred_pre)
            
            # 检查提取后的答案是否有效
            if not pred:
                print(f"[预测分类跳过] id={data.get('Sample_ID')}: 提取后的answer为空")
                continue
            
            print(f"[预测分类] id={data.get('Sample_ID')}")
            print(f"  原始预测: {repr(pred_pre)}")
            print(f"  提取后预测: {repr(pred)}")
            print(f"  真实答案: {repr(gold)}")
            
            # 预处理数据
            pred_processed = preprocess_data(pred)
            gold_processed = preprocess_data(gold)
            
            print(f"  处理后预测: {repr(pred_processed)} (类型: {type(pred_processed)}, 多值: {is_multi_value(pred)})")
            print(f"  处理后真实: {repr(gold_processed)} (类型: {type(gold_processed)}, 多值: {is_multi_value(gold)})")
            
            # 计算准确率
            acc = calc_acc(pred, gold)
            acc_list_pred.append(acc)
            acc_count_predict += acc
            
            # 计算PRF
            tp, fp, fn = calc_col_prf(pred, gold)
            P, R, F1 = calc_prf1(tp, fp, fn)
            
            P_list_pred.append(P)
            R_list_pred.append(R)
            F1_list_pred.append(F1)
            
            # 统计类型
            if is_trend_answer(gold):
                trend_count += 1
            elif is_date_answer(gold):
                date_count += 1
            else:
                other_count += 1
            
            total_predict += 1
            
            # 显示多值样本的比较结果
            if is_multi_value(pred) or is_multi_value(gold):
                print(f"  多值样本结果 - Acc: {acc}, P: {P:.4f}, R: {R:.4f}, F1: {F1:.4f}")
            print("-" * 50)

        # 历史查询：Volume/Closing/Opening
        elif intent in historical_intents:
            answer_value = data.get("answer")
            answer_predict = data.get("predict_SQL_answer")
            
            # 检查预测结果是否有效
            if answer_predict is None or answer_predict == "0" or answer_predict == 0:
                print(f"[历史查询跳过] id={data.get('Sample_ID')}: predict_SQL_answer为空或0")
                continue
                
            print(f"[历史查询] id={data.get('Sample_ID')}, answer={answer_value}, predict={answer_predict}")
            
            # 使用新的评估方法
            pred_processed = preprocess_data(answer_predict)
            gold_processed = preprocess_data(answer_value)
            
            # 计算准确率
            acc = calc_acc(answer_predict, answer_value)
            acc_count += acc
            
            # 计算PRF
            tp, fp, fn = calc_col_prf(answer_predict, answer_value)
            P, R, F1 = calc_prf1(tp, fp, fn)
            
            P_list_hist.append(P)
            R_list_hist.append(R)
            F1_list_hist.append(F1)
            
            total_query += 1

        else:
            print(f"[WARN] 未知 Intent: {intent}, Sample_ID={data.get('Sample_ID')}")

    # 输出结果
    print("\n" + "="*60)
    print("评估结果汇总")
    print("="*60)
    
    # 统计信息
    print(f"预测为None的样本数: {none_predict_count}")
    
    # 回归结果
    if y_true_reg and y_pred_reg:
        y_true_reg_arr = np.array(y_true_reg, dtype=float)
        y_pred_reg_arr = np.array(y_pred_reg, dtype=float)
        mse = float(mean_squared_error(y_true_reg_arr, y_pred_reg_arr))
        mae = float(mean_absolute_error(y_true_reg_arr, y_pred_reg_arr))
        mre = mean_relative_error(y_true_reg_arr, y_pred_reg_arr, epsilon=1.0)
        
        print("回归（Stock Price Prediction）:")
        print(f"  样本数量: {len(y_true_reg)}")
        print(f"  MSE: {mse:.8f}")
        print(f"  MAE: {mae:.8f}")
        print(f"  MRE: {mre:.8f}")
    else:
        print("回归（Stock Price Prediction）: 无有效样本或数值不匹配")

    # 预测分类结果
    print("\n预测分类（Stock Trend/Extremum Prediction）:")
    if P_list_pred:
        avg_P_pred = avg(P_list_pred)
        avg_R_pred = avg(R_list_pred)
        avg_F1_pred = avg(F1_list_pred)
        avg_acc_pred = avg(acc_list_pred)
        
        print(f"  样本分布: 趋势类={trend_count}, 日期类={date_count}, 其他={other_count}")
        print(f"  有效样本数: {total_predict}")
        print(f"  平均精确率 (P): {avg_P_pred:.4f}")
        print(f"  平均召回率 (R): {avg_R_pred:.4f}")
        print(f"  平均F1分数: {avg_F1_pred:.4f}")
        print(f"  准确率: {avg_acc_pred:.4f} ({acc_count_predict}/{total_predict})")
    else:
        print("  无有效分类样本")

    # 历史查询结果
    print("\n历史查询（Volume/Closing/Opening）:")
    if P_list_hist:
        avg_P_hist = avg(P_list_hist)
        avg_R_hist = avg(R_list_hist)
        avg_F1_hist = avg(F1_list_hist)
        avg_acc_hist = acc_count / total_query if total_query else 0
        
        print(f"  样本数量: {total_query}")
        print(f"  平均精确率 (P): {avg_P_hist:.4f}")
        print(f"  平均召回率 (R): {avg_R_hist:.4f}")
        print(f"  平均F1分数: {avg_F1_hist:.4f}")
        print(f"  准确率: {avg_acc_hist:.4f} ({acc_count}/{total_query})")
    else:
        print("  无有效历史查询样本")
# 添加保存结果到txt文件的函数
def save_metrics_to_txt(datas: List[Dict[str, Any]], filename: str = "evaluation_metrics.txt"):
    """保存关键指标到txt文件"""
    # 这里调用evaluate_by_intent并捕获结果，或者重新计算
    # 为了简单，我们直接重新计算关键指标
    
    # 计算回归指标
    y_true_reg, y_pred_reg = [], []
    for data in datas:
        intent = data.get("Intent", "").strip()
        if intent == "Stock Price Prediction":
            gold = data.get("answer")
            pred_source = data.get("predict_answer")
            if pred_source and pred_source != "0" and pred_source != 0:
                y_true_vals = flatten_floats(gold)
                y_pred_vals = flatten_floats(pred_source)
                if len(y_true_vals) == len(y_pred_vals) and len(y_true_vals) > 0:
                    y_true_reg.extend(y_true_vals)
                    y_pred_reg.extend(y_pred_vals)
    
    # 计算指标
    mse, mae, mre = 0.0, 0.0, 0.0
    if y_true_reg and y_pred_reg:
        y_true_reg_arr = np.array(y_true_reg, dtype=float)
        y_pred_reg_arr = np.array(y_pred_reg, dtype=float)
        mse = float(mean_squared_error(y_true_reg_arr, y_pred_reg_arr))
        mae = float(mean_absolute_error(y_true_reg_arr, y_pred_reg_arr))
        mre = mean_relative_error(y_true_reg_arr, y_pred_reg_arr, epsilon=1.0)
    
    # 保存到文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("关键评测指标\n")
        f.write("=" * 40 + "\n")
        f.write(f"评测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"模型: {model_name}\n")
        f.write(f"测试样本数: {len(datas)}\n\n")
        
        f.write("回归任务 (Stock Price Prediction):\n")
        f.write(f"有效样本数: {len(y_true_reg)}\n")
        f.write(f"MSE:  {mse:.8f}\n")
        f.write(f"MAE:  {mae:.8f}\n")
        f.write(f"MRE:  {mre:.8f}\n")
    
    print(f"指标已保存到: {filename}")
if __name__ == "__main__":
    datas = load_test_as_datas_resume()
    evaluate_by_intent(datas)
    save_metrics_to_txt(datas, f"metrics_{model_name}.txt")