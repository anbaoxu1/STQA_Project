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
from tqdm import tqdm

custom_base_url = "http://*******.*****.***:8080/v1"
model_name = 'glm-45-air'
api_key = '***************************************'

llm = ChatOpenAI(model_name=model_name, openai_api_key=api_key, base_url=custom_base_url)
 
import torch  
from transformers import BertTokenizer  

BERT_PATH = '/home/bbx/code/stock_generate/bert-base-cased'  
model_path = '/home/bbx/code/stock_generate/model/bert.pt'  

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
    if "{input_query}" in template_str and "input_query" not in variables and "query" in variables:
        variables = dict(variables)
        variables["input_query"] = variables["query"]
    if "{query}" in template_str and "query" not in variables and "input_query" in variables:
        variables = dict(variables)
        variables["query"] = variables["input_query"]

    prompt = ChatPromptTemplate.from_template(template_str)
    
    for attempt in range(max_retries):
        try:
            resp = (prompt | llm).invoke(variables)
            return str(resp.content).strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[WARN] LLM call failed, retry {attempt + 1}: {e}")
                import time
                time.sleep(2)
            else:
                print(f"[ERROR] LLM call failed, max retries reached: {e}")
                return "[]"
    
    return "[]"

def ensure_forecast_dates(anchor_date: str, horizon: int, values) -> Dict[str, Any]:
    if isinstance(values, np.ndarray):
        values = values.tolist()
    elif values is not None and not isinstance(values, list):
        values = list(values)

    if values is None or len(values) == 0:
        return {"dates": [], "values": [], "error": "empty_values"}

    try:
        base = datetime.fromisoformat(anchor_date)
    except Exception as e:
        print(f"[ERROR] ensure_forecast_dates invalid anchor_date={anchor_date}: {e}")
        return {"dates": [], "values": [], "error": "invalid_anchor_date"}

    dates = [(base + timedelta(days=i)).date().isoformat() for i in range(1, horizon + 1)]
    dates = dates[:len(values)]
    return {"dates": dates, "values": values, "error": None}

TEMPLATES_TAKE = load_templates('/home/bbx/code/stock_generate/pred_prompt_english.json')
TEMPLATES_HISTORY = load_templates('/home/bbx/code/stock_generate/history_sql_prompt_english.json')
TEMPLATES_RETRIVAL = load_templates('/home/bbx/code/stock_generate/retrival_prompt.json')
TEMPLATES_DIRECT  = load_templates('/home/bbx/code/stock_generate/sql_prompt_english.json')

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
    query: Annotated[str, use_latest]
    raw_data: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    intent: Annotated[Optional[str], use_latest_non_none] = None
    slots: Annotated[Optional[Dict[str, Any]], merge_dict] = None
    
    flow: Annotated[Optional[Literal["PredictFlow", "QueryFlow", "PredictReasoningFlow"]], use_latest] = None
    
    table_name: Annotated[Optional[str], use_latest] = None
    
    sql_statement: Annotated[Optional[str], use_latest] = None
    cleaned_sql: Annotated[Optional[str], use_latest] = None
    table_results: Annotated[Optional[Any], use_latest] = None
    predict_SQL_answer: Annotated[Optional[Any], use_latest] = None
    
    history_sql: Annotated[Optional[str], use_latest] = None
    history_cleaned_sql: Annotated[Optional[str], use_latest] = None
    history_data: Annotated[Optional[List[Any]], use_latest] = None
    history_rows: Annotated[Optional[List[Any]], use_latest] = None
    
    forecast_sql: Annotated[Optional[str], use_latest] = None
    forecast_cleaned_sql: Annotated[Optional[str], use_latest] = None
    pred_answer: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    date_parse: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    predict_answer: Annotated[Optional[str], use_latest] = None
    extracted_value: Annotated[Optional[Dict[str, Any]], use_latest] = None
    
    final_answer: Annotated[Optional[str], use_latest] = None

    class Config:
        arbitrary_types_allowed = True

def nlu_node(state: AgentState) -> AgentState:
    nlu = bert_infer_intent_slots_v2(state.query)
    
    print(f"[DEBUG] nlu_node RAW NLU OUTPUT: {nlu}")
    print(f"[DEBUG] nlu_node query: '{state.query}'")
    
    WHITELIST_INTENTS = {
        "Opening Price Inquiry",
        "Closing Price Inquiry",
        "Stock Trading Volume Inquiry",
        "Stock Price Prediction",
        "Stock Trend Prediction",
        "Stock Extremum Prediction",
    }

    intent = nlu.get("intent")
    print(f"[DEBUG] nlu_node raw intent: {intent}, type: {type(intent)}")
    
    print(f"[DEBUG] nlu_node complete nlu structure:")
    for key, value in nlu.items():
        print(f"  {key}: {value} (type: {type(value)})")

    if isinstance(intent, list) and intent:
        print(f"[DEBUG] nlu_node processing intent list: {intent}")
        if intent[0] in WHITELIST_INTENTS:
            state.intent = intent[0]
            print(f"[DEBUG] nlu_node selected first whitelist intent: {intent[0]}")
        else:
            picked = next((it for it in intent if it in WHITELIST_INTENTS), None)
            print(f"[DEBUG] nlu_node searched whitelist, picked: {picked}")
            state.intent = picked
            if picked is None:
                print(f"[DEBUG] nlu_node WARNING: No whitelist intent found in: {intent}")
    else:
        print(f"[DEBUG] nlu_node intent is not list or empty list")
        if isinstance(intent, str) and intent in WHITELIST_INTENTS:
            state.intent = intent
            print(f"[DEBUG] nlu_node selected string whitelist intent: {intent}")
        else:
            state.intent = intent
            print(f"[DEBUG] nlu_node WARNING: String intent not in whitelist or not string: {intent}")

    state.slots = nlu.get("slots", {}) or {}
    print(f"[DEBUG] nlu_node FINAL: state.intent={state.intent}, slots={state.slots}")

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
    print(f"[INFO] retrival_table_node: state.intent={state.intent}, slots={state.slots}")
    final_table_name = None

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

    if not final_table_name:
        final_table_name = (state.raw_data or {}).get("pred_tabel_caption")

    if not final_table_name:
        stock = (state.slots or {}).get("stock_name", "AAPL")
        final_table_name = f'["{stock}"]'

    state.table_name = final_table_name
    print(f"[INFO] retrival_table_node FINAL table_name: {final_table_name}")
    return state

def Query2SQL(state: AgentState) -> AgentState:
    intent_key = state.intent.strip() if state.intent else ""
    print(f"[INFO] Query2SQL: state.intent={state.intent}, slots={state.slots}")
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
    
    print(f"[INFO] DB_Query using {sql_source}: {sql_to_execute[:100]}...")
    
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

    if isinstance(res, tuple) and len(res) == 2:
        _, table_results = res
    elif isinstance(res, tuple) and len(res) == 1:
        table_results = res[0]
    else:
        table_results = res

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

    print(f"history_list length: {len(history_list)}, valid values: {len([x for x in history_list if x is not None])}")
    state.history_data = history_list

    return state

def History2SQL(state: AgentState) -> AgentState:
    intent_key = state.intent.strip() if state.intent else ""
    print(f"[INFO] History2SQL: state.intent={state.intent}, slots={state.slots}")
    
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
            print(f"[WARN] History2SQL generated empty SQL, using default")
            stock = (state.slots or {}).get("stock_name", "AAPL")
            history_sql = f'SELECT date, open FROM "{stock}" ORDER BY date DESC LIMIT 49'
        
        state.history_sql = history_sql
        state.history_cleaned_sql = history_sql
        print(f"[INFO] History2SQL generated SQL: {history_sql}")
        
    except Exception as e:
        print(f"[ERROR] History2SQL failed: {e}")
        stock = (state.slots or {}).get("stock_name", "AAPL")
        default_sql = f'SELECT date, open FROM "{stock}" ORDER BY date DESC LIMIT 49'
        state.history_sql = default_sql
        state.history_cleaned_sql = default_sql
        
    return state

def TS_Forecasting(state: AgentState) -> AgentState:
    hist = state.history_data or []
    print(f"[DEBUG][TS_Forecasting] hist_len={len(hist)} | head={hist[:5]}")

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

    print(f"[DEBUG][TS_Forecasting] raw_pred_values={pred_values} type={type(pred_values)}")

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
    print(f"[DEBUG][TS_Forecasting] anchor={anchor}")

    result = ensure_forecast_dates(anchor, 15, pred_values)
    print(f"[DEBUG][TS_Forecasting] ensure -> dates[{len(result.get('dates', []))}] values[{len(result.get('values', []))}] error={result.get('error')}")

    state.pred_answer = result
    print(f"[DEBUG][TS_Forecasting] OUT pred_answer={state.pred_answer}")
    return state

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

def Forecast_Selection(state: AgentState) -> AgentState:
    pa = state.pred_answer or {}
    print("[DEBUG][Forecast_Selection] IN pred_answer:", state.pred_answer)
    if not pa.get("dates") or not pa.get("values"):
        return state

    intent_key = (state.intent or "").strip()
    print(f"[INFO] Forecast_Selection: state.intent={state.intent}, slots={state.slots}")
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
    print("[DEBUG][resp_pre_pre] LLM raw resp:", resp_pre_pre)
    resp_pre = extract_after_think(resp_pre_pre)
    print("[DEBUG][resp_pre] LLM raw resp:", resp_pre)

    state.predict_answer = resp_pre
    return state

def Forecast_Reasoning(state: AgentState) -> AgentState:
    pa = state.pred_answer or {}
    print("[DEBUG][Forecast_Reasoning] IN pred_answer:", state.pred_answer)
    if not pa.get("dates") or not pa.get("values"):
        return state

    intent_key = (state.intent or "").strip()
    print(f"[INFO] Forecast_Reasoning: state.intent={state.intent}, slots={state.slots}")
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
    print("[DEBUG][Forecast_Reasoning] LLM raw resp:", resp_pre)
    state.predict_answer = resp_pre
    return state

UNIFIED_PLANNER_PROMPT = """
You are a unified planning and tool-aware system for a stock QA/forecast agent. Your job: (1) plan the task by selecting a flow from the user intent and generating the ordered node steps; (2) strictly follow the tool (node) manual below when producing the plan. Return exactly one single-line JSON plan.

Allowed nodes (exact names only):
retrival_table_node
Query2SQL
DB_Query
History2SQL
TS_Forecasting
Forecast_Selection
Forecast_Reasoning

Allowed flows and exact step orders:
QueryFlow: retrival_table_node -> Query2SQL -> DB_Query
PredictFlow: retrival_table_node -> History2SQL -> DB_Query -> TS_Forecasting -> Forecast_Selection
PredictReasoningFlow: retrival_table_node -> History2SQL -> DB_Query -> TS_Forecasting -> Forecast_Reasoning

Intent-to-flow mapping:
PredictFlow:
"Stock Price Prediction"
PredictReasoningFlow:
"Stock Trend Prediction"
"Stock Extremum Prediction"
QueryFlow:
"Opening Price Inquiry"
"Closing Price Inquiry"
"Stock Trading Volume Inquiry"

Tool manual (what each node does, and how it connects):
retrival_table_node
Purpose: Determine the correct data source/table(s) and key fields based on user query and context (e.g., ticker, date range, OHLCV).
Input needs (from context_json/user_query): ticker(s), timeframe/date constraints, metric type (open/close/volume), language hints.
Output (to next node): a structured selection result (table identifiers, column mapping, constraints).
Notes: Do not fetch data here; only resolve metadata and schema.

Query2SQL
Purpose: Build a concrete SQL (or equivalent query) for current intent using the resolved schema from retrival_table_node.
Input: selected table/columns, filters (ticker, date range), aggregation spec if needed.
Output: validated SQL string (safe, parameterized if possible).
Notes: Ensure WHERE conditions reflect user constraints; include ordering/limit if relevant.

DB_Query
Purpose: Execute the built SQL to retrieve factual data.
Input: SQL string.
Output: tabular records (e.g., rows with timestamp, open/close/high/low/volume).
Notes: Handle empty results (surface gracefully). No predictive logic here.

History2SQL
Purpose: Build a historical data retrieval query suitable for time series modeling (sufficient window length).
Input: ticker, feature set (OHLCV), lookback window, frequency (e.g., daily).
Output: SQL optimized for modeling (sorted by time, continuous where possible).
Notes: Include data quality filters; ensure consistent indexing.

TS_Forecasting
Purpose: Apply a time series model to historical data to forecast the target (price/trend/extremum).
Input: cleaned historical series from DB_Query, modeling params (horizon, target).
Output: forecast values and/or trend signals; may include confidence intervals.
Notes: No external tools beyond provided data. Keep method abstract (model-agnostic) unless otherwise specified.

Forecast_Selection
Purpose: Produce the final prediction answer for end users (concise numeric/target output).
Input: forecast from TS_Forecasting.
Output: finalized answer (e.g., next-day price level).
Notes: No lengthy reasoning; prioritize clarity and actionable result.

Forecast_Reasoning
Purpose: Produce a reasoning-oriented prediction answer (explain trend/extremum prediction).
Input: forecast signals from TS_Forecasting.
Output: concise reasoning summary supporting the forecast.
Notes: Keep reasoning structured (drivers, recent patterns, caution).

Planning rules (unified routing + orchestration):
Select exactly one flow solely from the given intent using the mapping above.
Build the steps array strictly following the exact step order of the chosen flow.
Do not add, remove, or reorder nodes. Names are case-sensitive and must match exactly.
The plan should be minimal yet complete; do not insert extra fields.

Input variables (provided by the caller):
intent: string
user_query: string
context_json: string (JSON-encoded state, including ticker/date/metric/etc.)

Output policy (strict):
Return exactly one single-line JSON: {"flow":"","steps":[{"name":"..."}, ...]}
No extra text, no code fences, no prefixes, no additional lines.
If the intent is unsupported, return: {"error":"Unsupported intent"} (single-line JSON).

Validation:
The steps must exactly match the order for the selected flow.
Each step object must only have the key "name" with a valid node name.
""".strip()

NODE_REGISTRY = {
    "retrival_table_node": retrival_table_node,
    "Query2SQL": Query2SQL,
    "DB_Query": DB_Query,
    "History2SQL": History2SQL,
    "TS_Forecasting": TS_Forecasting,
    "Forecast_Selection": Forecast_Selection,
    "Forecast_Reasoning": Forecast_Reasoning,
}

def build_unified_plan(state, llm):
    context_json = json.dumps(
        state.dict() if hasattr(state, "dict") else state.__dict__,
        ensure_ascii=False, default=str
    )
    user_prompt = (
        f"intent: {state.intent}\n"
        f"user_query: {state.query}\n"
        f"context_json: {context_json}\n"
    )
    
    full_prompt = f"{UNIFIED_PLANNER_PROMPT}\n\n{user_prompt}"
    
    resp = llm.invoke(full_prompt)
    plan_raw = str(resp.content).strip()
    print(f"[DEBUG][UnifiedPlanner] OUT plan: {plan_raw}")
    return json.loads(plan_raw)

def executor_node(state: "AgentState") -> "AgentState":
    plan = build_unified_plan(state, llm)
    print(f"[DEBUG][UnifiedPlanner] IN plan: {plan}")
    for step in plan["steps"]:
        name = step["name"]
        fn = NODE_REGISTRY[name]
        state = fn(state)
    return state

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

TEST_PATH = "/home/bbx/dataset/test_pred.json"

def calc_acc(pred, gold):
    return 1 if pred == gold else 0

def calc_col_prf(pred: List, gold: List) -> Tuple[int, int, int]:
    tp = 0
    gold_copy = gold.copy()
    for row in pred:
        if row in gold_copy:
            tp += 1
            gold_copy.remove(row)
        else:
            pass
    fp = len(pred) - tp
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

def flatten_floats(x: Any) -> List[float]:
    if x is None:
        return []
    if isinstance(x, dict):
        vals = x.get("values")
        if isinstance(vals, list):
            out = []
            for v in vals:
                try:
                    out.append(float(v))
                except Exception:
                    pass
            return out
        if "target_value" in x:
            try:
                return [float(x["target_value"])]
            except Exception:
                return []
        if "answer" in x:
            return flatten_floats(x["answer"])
        return []
    if isinstance(x, list):
        out = []
        for item in x:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                try:
                    out.append(float(item[1]))
                except Exception:
                    pass
            elif isinstance(item, (int, float)):
                out.append(float(item))
            elif isinstance(item, str):
                try:
                    out.append(float(item))
                except Exception:
                    pass
        return out
    if isinstance(x, (int, float)):
        return [float(x)]
    if isinstance(x, str):
        try:
            return [float(x)]
        except Exception:
            return []
    return []

def extract_top_label(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip().lower()
    if isinstance(x, dict):
        for key in ["label", "trend", "class", "prediction", "answer"]:
            if key in x:
                return extract_top_label(x[key])
        return ""
    if isinstance(x, list) and x and isinstance(x[0], str):
        return x[0].strip().lower()
    return ""

def avg(lst: List[float]) -> float:
    return sum(lst)/len(lst) if lst else 0.0

CACHE_PATH = "/home/bbx/dataset/test_run_cache_qwen3_30b_pred.jsonl"

def load_test_as_datas_resume():
    if not os.path.exists(TEST_PATH):
        raise FileNotFoundError(f"test file not found: {TEST_PATH}")
    with open(TEST_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError("test.json should be a JSON array.")

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

    with open(CACHE_PATH, "a", encoding="utf-8") as fout:
        for i, item in enumerate(tqdm(items, desc="Processing test items(resume)")):
            sid = str(item.get("Sample_ID", str(i)))
            if sid in done_ids:
                continue

            q = item.get("question", "")
            ans = item.get("answer")
            intent = item.get("Intent") or item.get("intent") or ""
            
            print(f"\n[DEBUG] ===== Processing Sample {sid} =====")
            print(f"[DEBUG] Query: '{q}'")
            print(f"[DEBUG] Expected Intent: '{intent}'")
            
            try:
                out = app.invoke({"query": q, "raw_data": item})
                
                final_intent = out.get('intent', 'MISSING')
                print(f"[DEBUG] FINAL RESULT - intent: {final_intent}")
                
                rec = {
                    "Sample_ID": sid,
                    "question": q,
                    "answer": ans,
                    "Intent": intent,
                    "predict_SQL_answer": out.get("predict_SQL_answer"),
                    "predict_answer": out.get("predict_answer"),
                    "pred_answer": out.get("pred_answer"),
                    "intent": final_intent,
                    "flow": out.get("flow"),
                }
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)[:200]}"
                rec = {
                    "Sample_ID": sid,
                    "question": q,
                    "error": error_msg,
                    "predict_answer": "ERROR",
                    "predict_SQL_answer": "ERROR"
                }
                print(f"[DEBUG] ERROR processing sample {sid}: {error_msg}")

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"[DEBUG] ===== End Sample {sid} =====\n")

    all_datas = []
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                all_datas.append(json.loads(line))
            except Exception:
                pass
    return all_datas

def extract_answer(pred: str) -> str:
    if not isinstance(pred, str):
        return pred
    m = re.search(r'(?i)Answer[:：]\s*(.*)', pred, flags=re.DOTALL)
    return m.group(1).strip() if m else pred.strip()

def evaluate_by_intent(datas: List[Dict[str, Any]]):
    regression_intents = {"Stock Price Prediction"}
    classification_pred_intents = {"Stock Trend Prediction", "Stock Extremum Prediction"}
    historical_intents = {"Stock Trading Volume Inquiry", "Closing Price Inquiry", "Opening Price Inquiry"}

    y_true_reg, y_pred_reg = [], []

    P_list_pred, R_list_pred, F1_list_pred = [], [], []

    P_list_hist, R_list_hist, F1_list_hist = [], [], []
    acc_count = 0
    total_predict = 0
    total_query = 0
    acc_count_predict = 0
    for data in datas:
        intent = (data.get("Intent") or "").strip()

        if intent in regression_intents:
            gold = data.get("answer")
            pred_source = data.get("predict_answer")
            y_true_vals = flatten_floats(gold)
            y_pred_vals = flatten_floats(pred_source)

            if len(y_true_vals) == len(y_pred_vals) and len(y_true_vals) > 0:
                y_true_reg.extend(y_true_vals)
                y_pred_reg.extend(y_pred_vals)
            else:
                print(f"[Regression] Length mismatch/empty: id={data.get('Sample_ID')}, y_true={y_true_vals}, y_pred={y_pred_vals}")

        elif intent in classification_pred_intents:
            gold = data.get("answer")
            pred_pre = data.get("predict_answer")
            pred = extract_answer(pred_pre)
            print(f"[Classification] id={data.get('Sample_ID')}, answer={gold}, predict={pred}")
            label_true = extract_top_label(gold)
            label_pred = extract_top_label(pred)

            pred_list = [label_pred] if label_pred else []
            gold_list = [label_true] if label_true else []

            tp, fp, fn = calc_col_prf(pred_list, gold_list)
            P, R, F1 = calc_prf1(tp, fp, fn)
            acc = calc_acc(pred_list, gold_list)
            total_predict += 1
            acc_count_predict += acc
            P_list_pred.append(P); R_list_pred.append(R); F1_list_pred.append(F1)

        elif intent in historical_intents:
            answer_value = data.get("answer")
            answer_predict = data.get("predict_SQL_answer")
            print(f"[History query] id={data.get('Sample_ID')}, answer={answer_value}, predict={answer_predict}")
            gold_table = ensure_list_table(answer_value)
            pred_table = ensure_list_table(answer_predict)
            tp, fp, fn = calc_col_prf(pred_table, gold_table)
            P, R, F1 = calc_prf1(tp, fp, fn)
            total_query+= 1
            acc = calc_acc(pred_table, gold_table)
            acc_count += acc
            P_list_hist.append(P); R_list_hist.append(R); F1_list_hist.append(F1)

        else:
            print(f"[WARN] Unknown Intent: {intent}, Sample_ID={data.get('Sample_ID')}")

    if y_true_reg and y_pred_reg:
        y_true_reg_arr = np.array(y_true_reg, dtype=float)
        y_pred_reg_arr = np.array(y_pred_reg, dtype=float)
        mse = float(np.mean((y_true_reg_arr - y_pred_reg_arr) ** 2))
        mae = float(np.mean(np.abs(y_true_reg_arr - y_pred_reg_arr)))
        mre = mean_relative_error(y_true_reg_arr, y_pred_reg_arr, epsilon=1.0)
        print("Regression (Stock Price Prediction):")
        print(f" MSE: {mse:.8f}")
        print(f" MAE: {mae:.8f}")
        print(f" MRE: {mre:.8f}")
    else:
        print("Regression (Stock Price Prediction): No valid samples or value mismatch")

    print("Classification (Stock Trend/Extremum Prediction):")
    print(f" P={avg(P_list_pred):.4f}, R={avg(R_list_pred):.4f}, F1={avg(F1_list_pred):.4f}")
    print(f"acc_predict={acc_count_predict/total_predict}")
    print("History query (Volume/Closing/Opening):")
    print(f" P={avg(P_list_hist):.4f}, R={avg(R_list_hist):.4f}, F1={avg(F1_list_hist):.4f}")
    print(f"acc={acc_count/total_query}")

HIST_INTENTS = {"Stock Trading Volume Inquiry", "Closing Price Inquiry", "Opening Price Inquiry"}

def evaluate_sql_exec_and_correctness(datas: List[Dict[str, Any]]):
    hist_samples = [d for d in datas if (d.get("Intent") or "").strip() in HIST_INTENTS]

    if not hist_samples:
        print("[ESR/Acc] History query samples empty, skip statistics")
        return

    esr_den = len(hist_samples)
    esr_num = sum(1 for d in hist_samples if d.get("exec_success") is True)
    ESR = esr_num / esr_den if esr_den else 0.0
    print(f"ESR (Executable Success Rate): {ESR:.2%} ({esr_num}/{esr_den})")

    succ_samples = [d for d in hist_samples if d.get("exec_success") is True]
    if not succ_samples:
        print("SQL accuracy Acc: No successfully executed samples")
        return

    acc_cnt = 0
    P_list, R_list, F1_list = [], [], []

    for d in succ_samples:
        gold_table = ensure_list_table(d.get("answer"))
        pred_table = ensure_list_table(d.get("predict_SQL_answer"))

        acc = calc_acc(pred_table, gold_table)
        acc_cnt += acc

        tp, fp, fn = calc_col_prf(pred_table, gold_table)
        P, R, F1 = calc_prf1(tp, fp, fn)
        P_list.append(P); R_list.append(R); F1_list.append(F1)

    AvgAcc = acc_cnt / len(succ_samples)
    print(f"SQL accuracy Acc (only successfully executed samples): {AvgAcc:.4f}")
    print(f"PRF1 average per sample (only successfully executed samples): P={sum(P_list)/len(P_list):.4f}, R={sum(R_list)/len(R_list):.4f}, F1={sum(F1_list)/len(F1_list):.4f}")

def check_llm_service_status():
    try:
        test_prompt = "Hello"
        resp = llm.invoke(test_prompt)
        print(f"[INFO] LLM service status: Normal")
        return True
    except Exception as e:
        print(f"[ERROR] LLM service status: Abnormal - {e}")
        return False

if __name__ == "__main__":
    if not check_llm_service_status():
        print("[WARN] LLM service abnormal, but continue execution (using fault-tolerant mode)")
    
    datas = load_test_as_datas_resume()
    evaluate_by_intent(datas)
    evaluate_sql_exec_and_correctness(datas)