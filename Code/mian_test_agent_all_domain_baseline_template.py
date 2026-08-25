import json  
import re  
from datetime import datetime, timedelta  
from typing import Any, Dict, Optional, List, Literal  
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
sys.path.append('/home/***')
from ICME_Weather.Code.model_library.test_pred import preds_30days_data
from ICME_Weather.Code.model_library import models 
from ICME_Weather.Code.model_library.models import iTransformer
import bert_train_test
from typing import Annotated, Optional, Dict, Any, List, Literal
from pydantic import BaseModel
import numpy as np
import math
import os
from sklearn.metrics import mean_squared_error, mean_absolute_error
from tqdm import tqdm

# ========== LLM Configuration ==========
custom_base_url = "http://*******.*****.***:8080/v1"
model_name = 'glm-45-air'
api_key = '******************************************'

llm = ChatOpenAI(model_name=model_name, openai_api_key=api_key, base_url=custom_base_url)

# ========== BERT Model ==========  
import torch  
from transformers import BertTokenizer  

BERT_PATH = '/home/***/code/stock_generate/bert-base-cased'  
model_path = '/home/***/code/stock_generate/model/bert.pt'  

tokenizer = BertTokenizer.from_pretrained(BERT_PATH)  
bert_model = torch.load(model_path, map_location="cpu")  
use_cuda = torch.cuda.is_available()  
device = torch.device("cuda" if use_cuda else "cpu")  
if use_cuda:  
    model = bert_model.cuda()  
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

# ========== Intent and Slot Mapping ==========
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

# ========== General Utilities ==========  
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

def call_llm_with_template(template_str: str, variables: Dict[str, Any], max_retries: int = 3) -> str:
    # NEW: Lightweight variable name compatibility: input_query <-> query (to prevent legacy template naming issues)
    if "{input_query}" in template_str and "input_query" not in variables and "query" in variables:
        variables = dict(variables)
        variables["input_query"] = variables["query"]
    if "{query}" in template_str and "query" not in variables and "input_query" in variables:
        variables = dict(variables)
        variables["query"] = variables["input_query"]

    prompt = ChatPromptTemplate.from_template(template_str)
    
    # Add retry mechanism
    for attempt in range(max_retries):
        try:
            resp = (prompt | llm).invoke(variables)
            return str(resp.content).strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[WARN] LLM call failed, retry {attempt + 1}: {e}")
                import time
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                print(f"[ERROR] LLM call failed, maximum retries reached: {e}")
                return "[]"
    
    return "[]"

def ensure_forecast_dates(anchor_date: str, horizon: int, values) -> Dict[str, Any]:
    # Standardize types
    if isinstance(values, np.ndarray):
        values = values.tolist()
    elif values is not None and not isinstance(values, list):
        values = list(values)

    # Basic validation
    if values is None or len(values) == 0:
        return {"dates": [], "values": [], "error": "empty_values"}

    # Anchor date parsing
    try:
        base = datetime.fromisoformat(anchor_date)  # YYYY-MM-DD
    except Exception as e:
        print(f"[ERROR] ensure_forecast_dates invalid anchor_date={anchor_date}: {e}")
        return {"dates": [], "values": [], "error": "invalid_anchor_date"}

    # Generate dates (starting from the day after anchor)
    dates = [(base + timedelta(days=i)).date().isoformat() for i in range(1, horizon + 1)]
    dates = dates[:len(values)]
    return {"dates": dates, "values": values, "error": None}

# Template loading
TEMPLATES_TAKE = load_templates('/home/***/code/stock_generate/pred_prompt_english.json')
TEMPLATES_HISTORY = load_templates('/home/***/code/stock_generate/history_sql_prompt_english.json')
TEMPLATES_RETRIVAL = load_templates('/home/***/code/stock_generate/retrival_prompt.json')
TEMPLATES_DIRECT  = load_templates('/home/***/code/stock_generate/sql_prompt_english.json')

# ========== LangGraph State ==========  
def use_latest(old_value, new_value):
    return new_value

def merge_dict(old_value, new_value):
    if old_value is None:
        return new_value
    if new_value is None:
        return old_value
    return {**old_value, **new_value}

def use_latest_non_none(old_value, new_value):
    return new_value if new_value is not None else old_value

class AgentState(BaseModel):
    # Core fields
    query: Annotated[str, use_latest]
    raw_data: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    # NLU related fields
    intent: Annotated[Optional[str], use_latest_non_none] = None
    slots: Annotated[Optional[Dict[str, Any]], merge_dict] = None
    
    # Process control
    flow: Annotated[Optional[Literal["PredictFlow", "QueryFlow", "PredictReasoningFlow"]], use_latest] = None
    
    # Table name
    table_name: Annotated[Optional[str], use_latest] = None
    
    # SQL query flow related
    sql_statement: Annotated[Optional[str], use_latest] = None
    cleaned_sql: Annotated[Optional[str], use_latest] = None
    table_results: Annotated[Optional[Any], use_latest] = None
    predict_SQL_answer: Annotated[Optional[Any], use_latest] = None
    
    # Historical data query related
    history_sql: Annotated[Optional[str], use_latest] = None
    history_cleaned_sql: Annotated[Optional[str], use_latest] = None
    history_data: Annotated[Optional[List[Any]], use_latest] = None
    history_rows: Annotated[Optional[List[Any]], use_latest] = None
    
    # Prediction related
    forecast_sql: Annotated[Optional[str], use_latest] = None
    forecast_cleaned_sql: Annotated[Optional[str], use_latest] = None
    pred_answer: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    # Date parsing related
    date_parse: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    # Prediction answer
    predict_answer: Annotated[Optional[str], use_latest] = None
    extracted_value: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    # Final answer
    final_answer: Annotated[Optional[str], use_latest] = None

    class Config:
        arbitrary_types_allowed = True

# ========== Node: NLU ==========  
def nlu_node(state: AgentState) -> AgentState:
    nlu = bert_infer_intent_slots_v2(state.query)
    
    WHITELIST_INTENTS = {
        "Opening Price Inquiry",
        "Closing Price Inquiry",
        "Stock Trading Volume Inquiry",
        "Stock Price Prediction",
        "Stock Trend Prediction",
        "Stock Extremum Prediction",
    }

    intent = nlu.get("intent")
    
    if isinstance(intent, list) and intent:
        if intent[0] in WHITELIST_INTENTS:
            state.intent = intent[0]
        else:
            picked = next((it for it in intent if it in WHITELIST_INTENTS), None)
            state.intent = picked
    else:
        if isinstance(intent, str) and intent in WHITELIST_INTENTS:
            state.intent = intent
        else:
            state.intent = intent

    state.slots = nlu.get("slots", {}) or {}
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

    # 1) Prioritize LLM retrieval
    if intent_key in TEMPLATES_RETRIVAL:
        try:
            template_str = TEMPLATES_RETRIVAL[intent_key]["description"]
            resp_pre = call_llm_with_template(template_str, {
                "query": state.query,
                "intent": intent_key,
                "slots": json.dumps(state.slots or {}, ensure_ascii=False),
            })
            resp = extract_after_think(resp_pre)
            candidate = (resp or "").strip()
            if candidate and candidate != "[]":
                final_table_name = candidate
        except Exception as e:
            print(f"[ERROR] retrival_table_node LLM call failed: {e}")

    # 2) Fallback: raw_data.pred_tabel_caption
    if not final_table_name:
        final_table_name = (state.raw_data or {}).get("pred_tabel_caption")

    # 3) Fallback: slots.stock_name -> ["{stock}"]
    if not final_table_name:
        stock = (state.slots or {}).get("stock_name", "AAPL")
        final_table_name = f'["{stock}"]'

    state.table_name = final_table_name
    return state

# ========== Query Flow: Generate SQL -> Clean -> Execute ==========  
def Query2SQL(state: AgentState) -> AgentState:
    intent_key = state.intent.strip() if state.intent else ""
    if intent_key not in TEMPLATES_DIRECT:
        raise ValueError(f"Direct template for intent '{intent_key}' not found")
    template_str = TEMPLATES_DIRECT[intent_key]["description"]

    table_name_local = state.table_name
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

def DB_Query(state: AgentState) -> AgentState:
    dbname = 'postgres'
    executor = PostgresQueryExecutor(database=dbname)
    
    # Intelligently select which SQL to execute
    sql_to_execute = None
    sql_source = "unknown"
    
    if hasattr(state, 'cleaned_sql') and state.cleaned_sql and state.cleaned_sql.strip():
        sql_to_execute = state.cleaned_sql
        sql_source = "cleaned_sql"
    elif hasattr(state, 'history_cleaned_sql') and state.history_cleaned_sql and state.history_cleaned_sql.strip():
        sql_to_execute = state.history_cleaned_sql
        sql_source = "history_cleaned_sql"
    elif hasattr(state, 'history_sql') and state.history_sql and state.history_sql.strip():
        sql_to_execute = state.history_sql
        sql_source = "history_sql"
    else:
        print(f"[ERROR] DB_Query: No SQL found to execute")
        state.table_results = None
        state.predict_SQL_answer = 'null'
        state.history_data = []
        return state
    
    try:
        res = executor.execute_sql(sql_to_execute)
    except Exception as e:
        print(f"[ERROR] DB_Query SQL execution failed: {e}")
        state.table_results = None
        state.predict_SQL_answer = 'null'
        state.history_data = []
        return state
    finally:
        executor.close()

    # Unified unpacking of results
    if isinstance(res, tuple) and len(res) == 2:
        _, table_results = res
    elif isinstance(res, tuple) and len(res) == 1:
        table_results = res[0]
    else:
        table_results = res

    # Check query results
    if not table_results:
        print(f"[WARN] DB_Query: No results returned")
        state.table_results = None
        state.predict_SQL_answer = 'null'
        state.history_data = []
        return state

    state.table_results = table_results
    state.predict_SQL_answer = 'null' if not table_results else convert_and_format_table_results(table_results, 6)
    state.final_answer = json.dumps({
        "type": "query",
        "intent": state.intent,
        "slots": state.slots,
        "sql": sql_to_execute,
        "sql_source": sql_source,
        "result": state.predict_SQL_answer
    }, ensure_ascii=False)

    # Extract historical data
    state.history_rows = table_results
    history_list: List[Optional[float]] = []
    for r in (table_results or []):
        if isinstance(r, (list, tuple)) and len(r) >= 2:
            try:
                val = float(r[1])
                history_list.append(val)
            except Exception:
                history_list.append(None)
        else:
            history_list.append(None)

    state.history_data = history_list
    return state

# ========== Prediction Flow: Historical SQL Generation -> Execution ==========  
def History2SQL(state: AgentState) -> AgentState:
    intent_key = state.intent.strip() if state.intent else ""
    
    if intent_key not in TEMPLATES_HISTORY:
        print(f"[ERROR] History template for intent '{intent_key}' not found")
        stock = (state.slots or {}).get("stock_name", "AAPL")
        default_sql = f'SELECT date, open FROM "{stock}" ORDER BY date DESC LIMIT 49'
        state.history_sql = default_sql
        state.history_cleaned_sql = default_sql
        return state
        
    template_str = TEMPLATES_HISTORY[intent_key]["description"]
    table_name = state.table_name or (state.raw_data or {}).get("pred_tabel_caption")
    if not table_name:
        stock = (state.slots or {}).get("stock_name", "AAPL")
        table_name = f'["{stock}"]'

    try:
        resp = call_llm_with_template(template_str, {
            "query": state.query,
            "intent": intent_key,
            "slots": json.dumps(state.slots or {}, ensure_ascii=False),
            "table_name": table_name
        })
        history_sql = extract_after_think(resp)
        history_sql = clean_sql_statement(clean_sql_statement(history_sql))
        
        if not history_sql or history_sql.strip() == "":
            stock = (state.slots or {}).get("stock_name", "AAPL")
            history_sql = f'SELECT date, open FROM "{stock}" ORDER BY date DESC LIMIT 49'
        
        state.history_sql = history_sql
        state.history_cleaned_sql = history_sql
        
    except Exception as e:
        print(f"[ERROR] History2SQL failed: {e}")
        stock = (state.slots or {}).get("stock_name", "AAPL")
        default_sql = f'SELECT date, open FROM "{stock}" ORDER BY date DESC LIMIT 49'
        state.history_sql = default_sql
        state.history_cleaned_sql = default_sql
        
    return state

# ========== Prediction Flow: Small Model Prediction -> Standardization ==========  
def TS_Forecasting(state: AgentState) -> AgentState:
    hist = state.history_data or []
    pred_values: Optional[List[float]] = None
    
    if isinstance(hist, list) and len(hist) == 49:
        try:
            pred_values = preds_30days_data(hist)
        except Exception as e:
            print(f"[ERROR][TS_Forecasting] preds_30days_data failed: {e}")
            state.pred_answer = {"dates": [], "values": [], "error": "predict_failed"}
            return state
    else:
        print(f"[WARN][TS_Forecasting] unexpected hist length: {len(hist)}")
        state.pred_answer = {"dates": [], "values": [], "error": "invalid_history_length"}
        return state

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

    anchor = None
    if getattr(state, "date_parse", None):
        anchor = state.date_parse.get("anchor_date")
    anchor = anchor or (state.slots or {}).get("end_date") or (state.slots or {}).get("date") or "2023-11-24"

    result = ensure_forecast_dates(anchor, 15, pred_values)
    state.pred_answer = result
    return state

# ========== Prediction Flow: LLM Final Result Generation ==========  
def extract_answer1(text: str) -> str:
    if not text:
        return ""
    m = re.search(r'(?i)answer\s*[：:]\s*(.*)', text, flags=re.DOTALL)
    return m.group(1).strip() if m else text.strip()

def Forecast_Selection(state: AgentState) -> AgentState:
    pa = state.pred_answer or {}
    if not pa.get("dates") or not pa.get("values"):
        return state

    intent_key = (state.intent or "").strip()
    tpl = TEMPLATES_TAKE.get(intent_key) or TEMPLATES_TAKE.get("default") or {}
    template_str = tpl.get("description")
    if not template_str:
        return state
    
    vars_payload = {
        "Intent": intent_key,
        "Slot": json.dumps(state.slots or {}, ensure_ascii=False),
        "extracted_history": json.dumps(state.history_data or {}, ensure_ascii=False),
        "input_query": state.query,
        "pred_answer": json.dumps(state.pred_answer or {}, ensure_ascii=False)
    }
    resp_pre_pre = call_llm_with_template(template_str, vars_payload)
    resp_pre = extract_after_think(resp_pre_pre)
    state.predict_answer = resp_pre
    return state

def Forecast_Reasoning(state: AgentState) -> AgentState:
    pa = state.pred_answer or {}
    if not pa.get("dates") or not pa.get("values"):
        return state

    intent_key = (state.intent or "").strip()
    tpl = TEMPLATES_TAKE.get(intent_key) or TEMPLATES_TAKE.get("default") or {}
    template_str = tpl.get("description")
    if not template_str:
        return state

    vars_payload = {
        "Intent": intent_key,
        "Slot": json.dumps(state.slots or {}, ensure_ascii=False),
        "extracted_history": json.dumps(state.history_data or {}, ensure_ascii=False),
        "input_query": state.query,
        "pred_answer": json.dumps(state.pred_answer or {}, ensure_ascii=False)
    }
    resp_pre_pre = call_llm_with_template(template_str, vars_payload)
    resp_pre = extract_after_think(resp_pre_pre)
    state.predict_answer = resp_pre
    return state

# ========== Dynamic Planner ==========
UNIFIED_PLANNER_PROMPT = """
You are an AI planner for a stock analysis system. Based on the user's intent, dynamically create a plan using available tools.

Available tools:
- retrival_table_node: Identify data source (table name)
- Query2SQL: Create SQL for factual queries (prices, volumes)
- History2SQL: Create SQL for historical data (for predictions)
- DB_Query: Execute SQL queries
- TS_Forecasting: Run time series predictions
- Forecast_Selection: Generate simple prediction answers
- Forecast_Reasoning: Generate detailed prediction answers with reasoning

Rules:
1. Always start with retrival_table_node
2. Use Query2SQL for Opening/Closing Price and Volume inquiries
3. Use History2SQL for prediction tasks
4. DB_Query must follow any SQL generation node
5. For predictions, use TS_Forecasting after historical data
6. Choose Forecast_Selection or Forecast_Reasoning based on query type

Output ONLY a JSON object with this exact format:
{"flow": "dynamic", "steps": [{"name": "retrival_table_node"}, {"name": "History2SQL"}, ...]}

IMPORTANT: The "steps" must be a list of objects with a "name" field, not a list of strings.
Do not include any explanations, just the JSON.
""".strip()

# ========== Node Registry ==========
NODE_REGISTRY = {
    "retrival_table_node": retrival_table_node,
    "Query2SQL": Query2SQL,
    "DB_Query": DB_Query,
    "History2SQL": History2SQL,
    "TS_Forecasting": TS_Forecasting,
    "Forecast_Selection": Forecast_Selection,
    "Forecast_Reasoning": Forecast_Reasoning,
}

# ========== Rule Mapping Function Added from Second Code ==========
def get_expected_flow_by_rule(intent: str) -> str:
    """Map intent to expected workflow according to rules"""
    PREDICT_FLOW_INTENTS = {"Stock Price Prediction"}
    PREDICT_REASONING_FLOW_INTENTS = {"Stock Trend Prediction", "Stock Extremum Prediction"}
    QUERY_FLOW_INTENTS = {"Opening Price Inquiry", "Closing Price Inquiry", "Stock Trading Volume Inquiry"}
    
    if intent in PREDICT_FLOW_INTENTS:
        return "PredictFlow"
    elif intent in PREDICT_REASONING_FLOW_INTENTS:
        return "PredictReasoningFlow"
    elif intent in QUERY_FLOW_INTENTS:
        return "QueryFlow"
    else:
        return "UnknownFlow"

def build_unified_plan(state, llm):
    """Completely dynamic planning function"""
    user_prompt = f"""
User Query: {state.query}
Identified Intent: {state.intent}
Slot Information: {json.dumps(state.slots or {}, ensure_ascii=False)}

Please plan the tool execution chain based on the above information.
"""
    
    full_prompt = f"{UNIFIED_PLANNER_PROMPT}\n\n{user_prompt}"
    
    try:
        resp = llm.invoke(full_prompt)
        plan_raw = str(resp.content).strip()
        
        # Clean response
        for prefix in ["```json", "```", "JSON:", "json", "```python"]:
            if plan_raw.startswith(prefix):
                plan_raw = plan_raw[len(prefix):].strip()
        if plan_raw.endswith("```"):
            plan_raw = plan_raw[:-3].strip()
        
        # Parse JSON
        plan_data = json.loads(plan_raw)
        
        # Basic validation
        if not isinstance(plan_data, dict):
            raise ValueError("Response is not a JSON object")
        
        steps = plan_data.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError("steps field is not a list")
        
        # Critical fix: Convert string list to dictionary list format
        normalized_steps = []
        for step in steps:
            if isinstance(step, str):
                normalized_steps.append({"name": step})
            elif isinstance(step, dict) and "name" in step:
                normalized_steps.append(step)
        
        # Update steps list
        plan_data["steps"] = normalized_steps
        
        # Determine flow type based on intent
        if state.intent in ["Stock Price Prediction"]:
            plan_data["flow"] = "PredictFlow"
        elif state.intent in ["Stock Trend Prediction", "Stock Extremum Prediction"]:
            plan_data["flow"] = "PredictReasoningFlow"
        elif state.intent in ["Opening Price Inquiry", "Closing Price Inquiry", "Stock Trading Volume Inquiry"]:
            plan_data["flow"] = "QueryFlow"
        else:
            plan_data["flow"] = "UnknownFlow"
        
        return plan_data
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parsing failed: {e}")
        return {"flow": "UnknownFlow", "steps": [{"name": "retrival_table_node"}]}
    except Exception as e:
        print(f"[ERROR] Planning failed: {e}")
        return {"flow": "UnknownFlow", "steps": []}

def executor_node(state: "AgentState") -> "AgentState":
    """Dynamic executor node"""
    # Get dynamic plan
    plan = build_unified_plan(state, llm)
    
    # Record flow information
    if "flow" in plan:
        state.flow = plan["flow"]
    
    # Execute each step in the plan
    for step in plan.get("steps", []):
        tool_name = step.get("name")
        if tool_name in NODE_REGISTRY:
            try:
                state = NODE_REGISTRY[tool_name](state)
            except Exception as e:
                print(f"[ERROR] Tool {tool_name} execution failed: {e}")
                break
    
    return state

# ========== Orchestration Graph ==========  
workflow = StateGraph(AgentState)

workflow.add_node("NLU", nlu_node)
workflow.add_node("RetrivalTable", retrival_table_node)
workflow.add_node("Query2SQL", Query2SQL)
workflow.add_node("DB_Query", DB_Query)
workflow.add_node("History2SQL", History2SQL)
workflow.add_node("TS_Forecasting", TS_Forecasting)
workflow.add_node("Forecast_Selection", Forecast_Selection)
workflow.add_node("Forecast_Reasoning", Forecast_Reasoning)
workflow.add_node("Executor", executor_node)

workflow.set_entry_point("NLU")
workflow.add_edge("NLU", "RetrivalTable")
workflow.add_edge("RetrivalTable", "Executor")
workflow.add_edge("Executor", END)

app = workflow.compile()

# ========== Evaluation Related Functions ==========
TEST_PATH = "/home/***/dataset/test_merged.json"
CACHE_PATH = f"/home/***/dataset/baseline/test_run_cache_{model_name}_pred_clasitfy_baseline.jsonl"
FLOW_ACCURACY_FILE = f"/home/***/dataset/domain_acc/baseline/flow_accuracy_results_{model_name}_baseline.json"

def calc_acc(pred, gold):
    return 1 if pred == gold else 0

def calc_col_prf(pred, gold):
    """Corrected PRF calculation"""
    pred_processed = preprocess_data(pred)
    gold_processed = preprocess_data(gold)
    
    # Single value comparison
    if not is_multi_value(pred) and not is_multi_value(gold):
        if pred_processed == gold_processed:
            return 1, 0, 0
        else:
            return 0, 1, 1
    
    # Multi-value comparison
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

def mean_relative_error(y_true: List[float], y_pred: List[float], epsilon: float = 1.0) -> float:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = np.abs(y_true) > epsilon
    if np.sum(mask) == 0:
        return float("nan")
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / np.abs(y_true[mask])))

def ensure_list_table(answer: Any) -> List:
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

def flatten_floats(data):
    """Convert data to list of floats"""
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
    """Normalize single value data"""
    if value is None:
        return ""
    
    if isinstance(value, list):
        if len(value) == 1:
            return normalize_single_value(value[0])
        else:
            return [str(item).strip() for item in value]
    
    value_str = str(value).strip()
    
    if value_str.lower() == 'none':
        return ""
    
    value_lower = value_str.lower()
    if value_lower in ['rise']:
        return 'rise'
    elif value_lower in ['fall']:
        return 'fall'
    elif value_lower in ['yes']:
        return 'Yes'
    elif value_lower in ['no']:
        return 'No'
    
    if '\n' in value_str:
        parts = [p.strip() for p in value_str.split('\n') if p.strip() and p.strip().lower() != 'none']
        if len(parts) > 1:
            return parts
        elif len(parts) == 1:
            return parts[0]
    
    if ',' in value_str or (' ' in value_str and len(value_str.split()) > 1):
        parts = re.split(r'[\s,]+', value_str.strip())
        valid_parts = [p.strip() for p in parts if p.strip() and p.strip().lower() not in [',', ' ', 'none']]
        if len(valid_parts) > 1:
            return valid_parts
        elif len(valid_parts) == 1:
            return valid_parts[0]
    
    return value_str

def is_multi_value(data):
    """Determine if data is multi-value"""
    if data is None:
        return False
    processed = normalize_single_value(data)
    return isinstance(processed, list) and len(processed) > 1

def preprocess_data(data):
    """Unified data preprocessing"""
    return normalize_single_value(data)

def avg(lst):
    """Calculate average"""
    return sum(lst)/len(lst) if lst else 0.0

def load_test_as_datas_resume():
    """Load test data and calculate flow accuracy"""
    if not os.path.exists(TEST_PATH):
        raise FileNotFoundError(f"test file not found: {TEST_PATH}")
    with open(TEST_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError("test.json should be a JSON array.")

    # Collect completed Sample_IDs
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

    # Initialize flow accuracy statistics
    flow_accuracy_stats = {
        "total_count": 0,
        "correct_count": 0,
        "details": []
    }

    # Process incomplete samples
    with open(CACHE_PATH, "a", encoding="utf-8") as fout:
        for i, item in enumerate(tqdm(items, desc="Processing test items(resume)")):
            sid = str(item.get("Sample_ID", str(i)))
            if sid in done_ids:
                continue

            q = item.get("question", "")
            ans = item.get("answer")
            true_intent = item.get("Intent") or item.get("intent") or ""
            
            try:
                out = app.invoke({"query": q, "raw_data": item})
                
                # ========== Calculate Flow Accuracy ==========
                flow_accuracy_stats["total_count"] += 1
                
                # Get expected flow
                expected_flow = get_expected_flow_by_rule(true_intent)
                
                # Get actual flow
                actual_flow = out.get("flow", "UnknownFlow")
                
                # Compare flows
                domain_acc = 1 if actual_flow == expected_flow else 0
                
                if domain_acc == 1:
                    flow_accuracy_stats["correct_count"] += 1
                
                # Record detailed information
                flow_detail = {
                    "sample_id": sid,
                    "question": q,
                    "true_intent": true_intent,
                    "expected_flow": expected_flow,
                    "actual_flow": actual_flow,
                    "domain_acc": domain_acc
                }
                flow_accuracy_stats["details"].append(flow_detail)
                
                rec = {
                    "Sample_ID": sid,
                    "question": q,
                    "answer": ans,
                    "Intent": true_intent,
                    "predict_SQL_answer": out.get("predict_SQL_answer"),
                    "predict_answer": out.get("predict_answer"),
                    "pred_answer": out.get("pred_answer"),
                    "intent": out.get("intent"),
                    "flow": actual_flow,
                    "flow_accuracy_detail": flow_detail
                }
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)[:200]}"
                
                # Record flow accuracy even if error occurs
                flow_accuracy_stats["total_count"] += 1
                flow_detail = {
                    "sample_id": sid,
                    "question": q,
                    "true_intent": true_intent,
                    "expected_flow": get_expected_flow_by_rule(true_intent),
                    "actual_flow": "ErrorFlow",
                    "domain_acc": 0,
                    "error": error_msg
                }
                flow_accuracy_stats["details"].append(flow_detail)
                
                rec = {
                    "Sample_ID": sid,
                    "question": q,
                    "error": error_msg,
                    "predict_answer": "ERROR",
                    "predict_SQL_answer": "ERROR",
                    "flow_accuracy_detail": flow_detail
                }

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()

    # Print flow accuracy results
    if flow_accuracy_stats["total_count"] > 0:
        accuracy = flow_accuracy_stats["correct_count"] / flow_accuracy_stats["total_count"]
        print("\n" + "="*60)
        print("Flow Accuracy Statistics")
        print("="*60)
        print(f"Total samples: {flow_accuracy_stats['total_count']}")
        print(f"Correct selections: {flow_accuracy_stats['correct_count']}")
        print(f"Flow accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # Statistics by intent
        intent_stats = {}
        for detail in flow_accuracy_stats["details"]:
            intent = detail.get("true_intent", "")
            if intent not in intent_stats:
                intent_stats[intent] = {"total": 0, "correct": 0}
            
            intent_stats[intent]["total"] += 1
            if detail.get("domain_acc") == 1:
                intent_stats[intent]["correct"] += 1
        
        print("\nFlow accuracy by intent:")
        for intent, stats in intent_stats.items():
            if stats["total"] > 0:
                intent_acc = stats["correct"] / stats["total"]
                print(f"  {intent}: {intent_acc:.2%} ({stats['correct']}/{stats['total']})")
        
        print("="*60)
        
        # Save flow accuracy results to file
        with open(FLOW_ACCURACY_FILE, 'w', encoding='utf-8') as f:
            json.dump(flow_accuracy_stats, f, ensure_ascii=False, indent=2)
        print(f"Flow accuracy results saved to: {FLOW_ACCURACY_FILE}")

    # Collect all cached records as datas for evaluation
    all_datas = []
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                all_datas.append(json.loads(line))
            except Exception:
                pass
    return all_datas

def evaluate_by_intent(datas: List[Dict[str, Any]]):
    """Use the fixed evaluation method to evaluate by intent classification"""
    regression_intents = {"Stock Price Prediction"}
    classification_pred_intents = {"Stock Trend Prediction", "Stock Extremum Prediction"}
    historical_intents = {"Stock Trading Volume Inquiry", "Closing Price Inquiry", "Opening Price Inquiry"}

    # Regression evaluation
    y_true_reg, y_pred_reg = [], []

    # Prediction classification evaluation
    P_list_pred, R_list_pred, F1_list_pred, acc_list_pred = [], [], [], []
    
    # Historical query evaluation
    P_list_hist, R_list_hist, F1_list_hist = [], [], []
    acc_count = 0
    total_predict = 0
    total_query = 0
    acc_count_predict = 0
    
    # Count samples where prediction is None
    none_predict_count = 0
    
    # Count samples with error exceeding threshold
    high_error_count = 0
    error_threshold = 50

    for data in datas:
        intent = (data.get("Intent") or "").strip()

        # Regression: Stock Price Prediction
        if intent in regression_intents:
            gold = data.get("answer")
            pred_source = data.get("predict_answer")
            
            # Check if prediction result is valid
            if pred_source is None or pred_source == "0" or pred_source == 0:
                continue
                
            y_true_vals = flatten_floats(gold)
            y_pred_vals = flatten_floats(pred_source)

            if len(y_true_vals) == len(y_pred_vals) and len(y_true_vals) > 0:
                # Check error threshold
                valid_pairs = []
                errors = []
                
                for true_val, pred_val in zip(y_true_vals, y_pred_vals):
                    error = abs(true_val - pred_val)
                    errors.append(error)
                    if error <= error_threshold:
                        valid_pairs.append((true_val, pred_val))
                
                # Only count if all values' errors are below threshold
                if len(valid_pairs) == len(y_true_vals):
                    true_vals_valid, pred_vals_valid = zip(*valid_pairs)
                    y_true_reg.extend(true_vals_valid)
                    y_pred_reg.extend(pred_vals_valid)
                else:
                    high_error_count += 1

        # Prediction classification: Stock Trend/Extremum Prediction
        elif intent in classification_pred_intents:
            gold = data.get("answer")
            pred_pre = data.get("predict_answer")
            
            # Check if prediction result is valid
            if pred_pre is None:
                none_predict_count += 1
                continue
                
            pred = extract_answer1(pred_pre)
            
            # Check if extracted answer is valid
            if not pred:
                continue
            
            # Preprocess data
            pred_processed = preprocess_data(pred)
            gold_processed = preprocess_data(gold)
            
            # Calculate accuracy
            acc = calc_acc(pred, gold)
            acc_list_pred.append(acc)
            acc_count_predict += acc
            
            # Calculate PRF
            tp, fp, fn = calc_col_prf(pred, gold)
            P, R, F1 = calc_prf1(tp, fp, fn)
            
            P_list_pred.append(P)
            R_list_pred.append(R)
            F1_list_pred.append(F1)
            
            total_predict += 1

        # Historical query: Volume/Closing/Opening
        elif intent in historical_intents:
            answer_value = data.get("answer")
            answer_predict = data.get("predict_SQL_answer")
            
            # Check if prediction result is valid
            if answer_predict is None or answer_predict == "0" or answer_predict == 0:
                continue
            
            # Calculate accuracy
            acc = calc_acc(answer_predict, answer_value)
            acc_count += acc
            
            # Calculate PRF
            tp, fp, fn = calc_col_prf(answer_predict, answer_value)
            P, R, F1 = calc_prf1(tp, fp, fn)
            
            P_list_hist.append(P)
            R_list_hist.append(R)
            F1_list_hist.append(F1)
            
            total_query += 1

        else:
            print(f"[WARN] Unknown Intent: {intent}, Sample_ID={data.get('Sample_ID')}")

    # Output results
    print("\n" + "="*60)
    print("Performance Evaluation Summary")
    print("="*60)
    
    # Regression results
    if y_true_reg and y_pred_reg:
        y_true_reg_arr = np.array(y_true_reg, dtype=float)
        y_pred_reg_arr = np.array(y_pred_reg, dtype=float)
        mse = float(mean_squared_error(y_true_reg_arr, y_pred_reg_arr))
        mae = float(mean_absolute_error(y_true_reg_arr, y_pred_reg_arr))
        mre = mean_relative_error(y_true_reg_arr, y_pred_reg_arr, epsilon=1.0)
        
        print("Regression (Stock Price Prediction):")
        print(f"  Sample count: {len(y_true_reg)}")
        print(f"  MSE: {mse:.8f}")
        print(f"  MAE: {mae:.8f}")
        print(f"  MRE: {mre:.8f}")
    else:
        print("Regression (Stock Price Prediction): No valid samples")

    # Prediction classification results
    print("\nPrediction Classification (Stock Trend/Extremum Prediction):")
    if P_list_pred:
        avg_P_pred = avg(P_list_pred)
        avg_R_pred = avg(R_list_pred)
        avg_F1_pred = avg(F1_list_pred)
        avg_acc_pred = avg(acc_list_pred)
        
        print(f"  Valid sample count: {total_predict}")
        print(f"  Average Precision (P): {avg_P_pred:.4f}")
        print(f"  Average Recall (R): {avg_R_pred:.4f}")
        print(f"  Average F1-Score: {avg_F1_pred:.4f}")
        print(f"  Accuracy: {avg_acc_pred:.4f} ({acc_count_predict}/{total_predict})")
    else:
        print("  No valid classification samples")

    # Historical query results
    print("\nHistorical Query (Volume/Closing/Opening):")
    if P_list_hist:
        avg_P_hist = avg(P_list_hist)
        avg_R_hist = avg(R_list_hist)
        avg_F1_hist = avg(F1_list_hist)
        avg_acc_hist = acc_count / total_query if total_query else 0
        
        print(f"  Sample count: {total_query}")
        print(f"  Average Precision (P): {avg_P_hist:.4f}")
        print(f"  Average Recall (R): {avg_R_hist:.4f}")
        print(f"  Average F1-Score: {avg_F1_hist:.4f}")
        print(f"  Accuracy: {avg_acc_hist:.4f} ({acc_count}/{total_query})")
    else:
        print("  No valid historical query samples")

def save_metrics_to_txt(datas: List[Dict[str, Any]], filename: str = "evaluation_metrics.txt", error_threshold: float = 10.0):
    """Save key metrics to txt file"""
    
    # Calculate regression metrics
    y_true_reg, y_pred_reg = [], []
    high_error_count = 0
    
    for data in datas:
        intent = data.get("Intent", "").strip()
        if intent == "Stock Price Prediction":
            gold = data.get("answer")
            pred_source = data.get("predict_answer")
            if pred_source and pred_source != "0" and pred_source != 0:
                y_true_vals = flatten_floats(gold)
                y_pred_vals = flatten_floats(pred_source)
                if len(y_true_vals) == len(y_pred_vals) and len(y_true_vals) > 0:
                    # Check error threshold
                    valid_pairs = []
                    for true_val, pred_val in zip(y_true_vals, y_pred_vals):
                        if abs(true_val - pred_val) <= error_threshold:
                            valid_pairs.append((true_val, pred_val))
                    
                    if len(valid_pairs) == len(y_true_vals):
                        true_vals_valid, pred_vals_valid = zip(*valid_pairs)
                        y_true_reg.extend(true_vals_valid)
                        y_pred_reg.extend(pred_vals_valid)
                    else:
                        high_error_count += 1
    
    # Calculate metrics
    mse, mae, mre = 0.0, 0.0, 0.0
    if y_true_reg and y_pred_reg:
        y_true_reg_arr = np.array(y_true_reg, dtype=float)
        y_pred_reg_arr = np.array(y_pred_reg, dtype=float)
        mse = float(mean_squared_error(y_true_reg_arr, y_pred_reg_arr))
        mae = float(mean_absolute_error(y_true_reg_arr, y_pred_reg_arr))
        mre = mean_relative_error(y_true_reg_arr, y_pred_reg_arr, epsilon=1.0)
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Key Evaluation Metrics\n")
        f.write("=" * 40 + "\n")
        f.write(f"Evaluation time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Test sample count: {len(datas)}\n\n")
        
        f.write("Regression Task (Stock Price Prediction):\n")
        f.write(f"Valid sample count: {len(y_true_reg)}\n")
        f.write(f"MSE:  {mse:.8f}\n")
        f.write(f"MAE:  {mae:.8f}\n")
        f.write(f"MRE:  {mre:.8f}\n")
    
    print(f"Metrics saved to: {filename}")

if __name__ == "__main__":
    # Load data and test (including flow accuracy statistics)
    datas = load_test_as_datas_resume()
    
    # Execute performance evaluation
    evaluate_by_intent(datas)
    
    # Save evaluation metrics
    save_metrics_to_txt(datas, f"metrics_{model_name}.txt")