import sys
sys.path.append('/home/***')
from ICME_Weather.Code.model_library.test_pred import preds_30days_data
from ICME_Weather.Code.model_library import models 
from ICME_Weather.Code.model_library.models import iTransformer
import torch
import numpy as np
from transformers import BertTokenizer
import pandas as pd
from torch import nn
from transformers import BertModel
from torch.optim import Adam
import re
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from tqdm import tqdm
from sklearn import metrics
import json
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import os
from tqdm import tqdm
import ast
import re
from rank_bm25 import BM25Okapi
import jieba
import math
from utils import *
from sklearn.metrics import mean_squared_error, mean_absolute_error
import datetime

custom_base_url = "http://fastapi.****.top:8080/v1"
model_name = '********'
api_key = '***********************************************'

llm = ChatOpenAI(model_name=model_name, openai_api_key=api_key, base_url=custom_base_url)

from sql_verify import PostgresQueryExecutor

def query_history_from_db(sql_query):
    try:
        dbname = 'postgres'
        executor = PostgresQueryExecutor(database=dbname)
        res = executor.execute_sql(sql_query or "")
        executor.close()

        if isinstance(res, tuple) and len(res) == 2:
            _, table_results = res
        elif isinstance(res, tuple) and len(res) == 1:
            table_results = res[0]
        else:
            table_results = res

        history_answer = []
        history_list = []
        
        for r in table_results or []:
            if isinstance(r, (list, tuple)) and len(r) >= 2:
                try:
                    date_str = str(r[0])
                    value = float(r[1])
                    history_answer.append([date_str, value])
                    history_list.append(value)
                except Exception as e:
                    print(f"Data conversion failed: {r}, error: {e}")
        
        return {
            "table_results": table_results,
            "history_answer": history_answer,
            "history_list": history_list,
            "row_count": len(table_results) if table_results else 0
        }
        
    except Exception as e:
        print(f"Database query failed: {e}")
        return {
            "table_results": None,
            "history_answer": [],
            "history_list": [],
            "row_count": 0,
            "error": str(e)
        }

def load_templates(template_file):
    with open(template_file, 'r', encoding='utf-8') as f:
        return json.load(f)



def call_llm_with_template(template_str, variables):
    if "{input_query}" in template_str and "input_query" not in variables and "query" in variables:
        variables = dict(variables)
        variables["input_query"] = variables["query"]
    if "{query}" in template_str and "query" not in variables and "input_query" in variables:
        variables = dict(variables)
        variables["query"] = variables["input_query"]
    
    prompt = ChatPromptTemplate.from_template(template_str)
    response = (prompt | llm).invoke(variables)
    return response.content if hasattr(response, 'content') else str(response)

def clean_sql_statement(sql):
    if not sql:
        return ""
    
    sql = re.sub(r'\s+', ' ', sql.strip())
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    if not sql.endswith(';'):
        sql = sql + ';'
    
    return sql

def extract_stock_table_name(query, intent, slots, raw_data=None):
    final_table_name = None
    intent_key = intent.strip() if intent else ""
    TEMPLATES_RETRIVAL = load_templates('/home/***/code/stock_generate/retrival_prompt.json') 
    
    if intent_key in TEMPLATES_RETRIVAL:
        template_str1 = TEMPLATES_RETRIVAL[intent_key]["description"]
        try:
            resp_pre = call_llm_with_template(template_str1, {
                "query": query,
                "intent": intent_key,
                "slots": json.dumps(slots or {}, ensure_ascii=False),
            })
            resp = extract_after_think(resp_pre)
            candidate = (resp or "").strip()
            if candidate:
                final_table_name = candidate
                print(f"[DEBUG] LLM retrieved table name: {final_table_name}")
        except Exception as e:
            print(f"[WARN] LLM table name retrieval failed: {e}")
    
    if not final_table_name and raw_data:
        final_table_name = raw_data.get("pred_tabel_caption")
        if final_table_name:
            print(f"[DEBUG] Table name obtained from raw_data: {final_table_name}")
    
    if not final_table_name:
        stock = slots.get("stock_name", "AAPL") if isinstance(slots, dict) else "AAPL"
        final_table_name = f'["{stock}"]'
        print(f"[DEBUG] Table name obtained from slots: {final_table_name}")
    
    return final_table_name

def extract_after_think_router(resp):
    if isinstance(resp, dict):
        return resp
    if not isinstance(resp, str):
        if hasattr(resp, 'content'):
            resp = resp.content
        else:
            resp = str(resp)
    if '</think>' in resp:
        return resp.split('</think>', 1)[1].strip()
    return resp

def clean_sql_statement(sql_statement):
    cleaned_sql = re.sub(r'```sql|```', '', sql_statement, flags=re.IGNORECASE)
    cleaned_sql = cleaned_sql.strip()
    cleaned_sql = re.sub(r'^(SQL:)\s*', '', cleaned_sql, flags=re.IGNORECASE)
    return cleaned_sql.strip()
def generate_history_sql(query, intent, slots, raw_data=None):
    """Generate historical SQL query statement"""
    print(f"[DEBUG] Attempting to generate SQL for intent '{intent}'")
    intent_clean = intent.strip()
    raw_templates = load_templates('/home/***/code/stock_generate/history_sql_prompt_english.json')
    TEMPLATES_HISTORY = {k.strip(): v for k, v in raw_templates.items()}
    
    if intent_clean not in TEMPLATES_HISTORY:
        print(f"[ERROR] Intent '{intent_clean}' not found in history_sql_prompt_english.json! Cannot generate SQL.")
        return None  
    table_name = extract_stock_table_name(query, intent, slots, raw_data)
    if isinstance(table_name, list) and len(table_name) > 0:
        table_name = table_name[0]  
    print(f"[DEBUG] Final table name string used: {table_name}")

    template_str2 = TEMPLATES_HISTORY[intent_clean]["description"]
    
    resp = call_llm_with_template(template_str2, {
        "query": query,
        "intent": intent_clean,
        "slots": json.dumps(slots or {}, ensure_ascii=False),
        "table_name": table_name
    })
    
    print(f"[DEBUG] Complete LLM-generated response: {resp}")
    
    history_sql = extract_after_think(resp)
    
    if not history_sql:
        print("[ERROR] Unable to extract SQL statement from LLM response")
        return None
        
    cleaned_sql = clean_sql_statement(history_sql)
    
    print(f"[DEBUG] Generated raw SQL: {history_sql}")
    print(f"[DEBUG] Cleaned SQL: {cleaned_sql}")
        
    return cleaned_sql

class PredictResultStorage:
    def __init__(self, file_name='/home/***/code/stock_generate/test-with-BERT_pred_pred_extracted_history_only1.json'):
        self.current_data = {}
        self.file_name = file_name

    def set_predict_tabel_name(self, predict_tabel_name):
        self.current_data["predict_tabel_name"] = predict_tabel_name
        
    def set_true_tabel_name(self, true_tabel_name):
        self.current_data["true_tabel_name"] = true_tabel_name

    def set_uuid(self, uuid):
        self.current_data["uuid"] = uuid

    def save_data(self):
        if os.path.exists(self.file_name):
            with open(self.file_name, 'r+') as f:
                data = json.load(f)
                data.append(self.current_data)
                f.seek(0)
                json.dump(data, f, indent=4)
        else:
            with open(self.file_name, 'w') as f:
                json.dump([self.current_data], f, indent=4)
        self.current_data = {}

prompt_file_name = '/home/***/code/stock_generate/pred_prompt_english.json'
with open(prompt_file_name, 'r', encoding='utf-8') as f:
    templates = json.load(f)

json_file = '/home/***/code/stock_generate/test-with-BERT_pred_pred_extracted_history_only1.json'
with open(json_file, 'r', encoding='utf-8') as f:
    datas = json.load(f)

CHECKPOINT_PATH = "/home/***/dataset/ground_wf_sql/predict_checkpoint_trans_qwen-8b_ground_wf_sql.json"
OUTPUT_JSONL = "/home/***/dataset/ground_wf_sql/predict_outputs_trans_qwen-8b_ground_wf_sql.json"
MERGED_OUTPUT_JSON = "/home/***/dataset/ground_wf_sql/predict_outputs_merged_trans_qwen-8b_ground_wf_sql.json"

def load_checkpoint_ids(path=CHECKPOINT_PATH):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except Exception:
                return set()
    return set()

def save_checkpoint_ids(done_ids, path=CHECKPOINT_PATH):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sorted(list(done_ids)), f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def append_jsonl(record, path=OUTPUT_JSONL):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def load_existing_outputs(path=OUTPUT_JSONL):
    results = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    sid = obj.get("Sample_ID")
                    if sid is not None:
                        results[sid] = obj
                except Exception:
                    pass
    return results

def get_sample_id(d):
    return d.get("Sample_ID") or d.get("uuid") or d.get("id") or str(abs(hash(json.dumps(d, ensure_ascii=False))))

def extract_after_think(resp):
    if not isinstance(resp, str):
        if hasattr(resp, 'content'):
            resp = resp.content
        else:
            resp = str(resp)
    
    if '</think>' in resp:
        resp = resp.split('</think>', 1)[1].strip()
    if '<Answer>' in resp and '</Answer>' in resp:
        answer_match = re.search(r'<Answer>(.*?)</Answer>', resp, re.DOTALL)
        if answer_match:
            return answer_match.group(1).strip()
    
    if '<Answer>:' in resp:
        return resp.split('<Answer>:', 1)[1].strip()
    
    if 'Answer:' in resp:
        return resp.split('Answer:', 1)[1].strip()
    
    return resp.strip()

def process_pred_answer(pred_answer, stock_name, start='2023-11-25'):
    if pred_answer is None or len(pred_answer) != 30:
        return None
    start_date = datetime.date.fromisoformat(start)
    result = []
    for i in range(30):
        date_str = (start_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        value = float(pred_answer[i])
        result.append([stock_name, date_str, value])
    return result

def normalize_colon_and_case(s: str) -> str:
    return s.replace("：", ":").replace("ANSWER", "Answer").replace("answer", "Answer")

import math
from datetime import datetime, timedelta

def ensure_forecast_dates(anchor_date, days_count, pred_values):
    try:
        if isinstance(anchor_date, str):
            anchor = datetime.fromisoformat(anchor_date)
        else:
            anchor = anchor_date
            
        dates = []
        values = []
        current_date = anchor
        
        for i in range(days_count):
            current_date = current_date + timedelta(days=1)
            dates.append(current_date.strftime("%Y-%m-%d"))
            
            if i < len(pred_values):
                values.append(float(pred_values[i]))
            else:
                values.append(float(pred_values[-1]) if pred_values else 0.0)
                
        return {"dates": dates, "values": values, "error": None}
        
    except Exception as e:
        return {"dates": [], "values": [], "error": f"date_generation_failed: {str(e)}"}

def process_weekend_values(date_value_pairs):
    processed_dates = []
    processed_values = []
    
    for date_str, value in date_value_pairs:
        try:
            date_obj = datetime.fromisoformat(date_str)
            if date_obj.weekday() in [5, 6]:
                processed_values.append(0.0)
                print(f"[DEBUG] Weekend processing: {date_str} (Weekday{date_obj.weekday()+1}) -> 0.0")
            else:
                processed_values.append(value)
            processed_dates.append(date_str)
        except Exception as e:
            print(f"[WARN] Date parsing failed {date_str}: {e}")
            processed_dates.append(date_str)
            processed_values.append(value)
    
    return processed_dates, processed_values

done_ids = load_checkpoint_ids()
existing_outputs = load_existing_outputs()

for data in tqdm(datas, desc="Predicting"):
    sid = get_sample_id(data)

    if sid in done_ids:
        if sid in existing_outputs:
            for k, v in existing_outputs[sid].items():
                if k not in data:
                    data[k] = v
        continue

    try:
        intent = data['Intent']
        skip_intents = [
            'Stock Price Prediction',
            'Stock Trend Prediction',
            'Stock Extremum Prediction'
        ]
        if intent in skip_intents:
            query = data['question']
            slots = data['BERT_pred_slots']
            answer_true = data['answer']
            template_str = templates[intent]["description"]
            
            history_answer = []
            history_list = []
            history_sql = ""
            
            try:
                history_sql = generate_history_sql(query, intent, slots)
                print(f"[{sid}] Generated SQL: {history_sql}")
                
                db_result = query_history_from_db(history_sql)
                if db_result.get("error"):
                    print(f"[{sid}] Database query failed: {db_result['error']}")
                    history_list = data.get('extracted_history', [])
                    history_answer = data.get('history_answer', [])
                else:
                    history_answer = db_result["history_answer"] 
                    history_list = db_result["history_list"]     
                    print(f"[{sid}] Retrieved {len(history_answer)} historical records from database")
                
                data['generated_history_sql'] = history_sql
                data['db_history_answer'] = history_answer
                data['db_history_list'] = history_list
                data['db_row_count'] = db_result.get("row_count", 0)
                
            except Exception as e:
                print(f"[{sid}] Historical data retrieval failed: {e}")
                history_list = data.get('extracted_history', [])
                history_answer = data.get('history_answer', [])
                print(f"[{sid}] Using original data, obtained {len(history_answer)} historical records")
            
            pred_answer = None
            if isinstance(history_list, list) and len(history_list) == 49:
                pred_answer = preds_30days_data(history_list)
                print(f"[{sid}] Prediction using database historical data, data length: {len(history_list)}")

            pred_data = {"dates": [], "values": [], "error": None}
            
            if pred_answer is None:
                data['predict_answer'] = "Market closed"
                pred_data = {"dates": [], "values": [], "error": "trading_suspended"}
                print(f"Sample {sid}: Market closed")
            else:
                if hasattr(pred_answer, "tolist"):
                    pred_values = pred_answer.tolist()
                elif not isinstance(pred_answer, list):
                    pred_values = list(pred_answer)
                else:
                    pred_values = pred_answer

                if (len(pred_values) == 0 or 
                    any(v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) 
                        for v in pred_values)):
                    pred_data = {"dates": [], "values": [], "error": "invalid_forecast_values"}
                else:
                    anchor = None
                    if isinstance(slots, dict):
                        anchor = slots.get("end_date") or slots.get("date") 
                    anchor = anchor or "2023-11-24"
                    
                    print(f"[DEBUG][{sid}] anchor={anchor}, pred_values_len={len(pred_values)}")
                    
                    result = ensure_forecast_dates(anchor, 15, pred_values)
                    
                    if result.get("error"):
                        pred_data = result
                    else:
                        if intent == 'Stock Price Prediction':
                            pred_data = {
                                "dates": result["dates"], 
                                "values": result["values"], 
                                "error": None
                            }
                            print(f"[DEBUG][{sid}] Price prediction - raw values: dates[{len(result['dates'])}] values={result['values'][:3]}...")
                        elif intent in ['Stock Trend Prediction', 'Stock Extremum Prediction']:
                            dates, values = process_weekend_values(
                                list(zip(result["dates"], result["values"]))
                            )
                            pred_data = {
                                "dates": dates, 
                                "values": values, 
                                "error": None
                            }
                            print(f"[DEBUG][{sid}] Trend/Extremum prediction - after weekend zeroing: dates[{len(dates)}] values={values[:3]}...")
                        else:
                            pred_data = {
                                "dates": result["dates"], 
                                "values": result["values"], 
                                "error": None
                            }
                
                prompt = ChatPromptTemplate.from_template(template_str)
                chain = prompt | llm
                
                response = chain.invoke({
                    "input_query": query,
                    "Slot": slots,
                    "Intent": intent,
                    "pred_answer": pred_data,  
                    "extracted_history": history_answer 
                })
                
                res = extract_after_think(response.content)
                print(f"[{sid}] {res}")
                content = str(res).strip()
                print(f"[{sid}] {content}")
                text = normalize_colon_and_case(content)
                print(f"[{sid}] text: {text}")
                
                if "Answer:" in text:
                    parts = text.split("Answer:")
                    data['predict_answer'] = parts[1].strip() if len(parts) > 1 else content
                else:
                    data['predict_answer'] = content

                print(f"[{sid}] predict_answer: {data['predict_answer']}")

            data['pred_data'] = pred_data
            print(f"[{sid}] pred_data: {data['pred_data']}")

        else:
            data['pred_data'] = {"dates": [], "values": [], "error": "intent_not_supported"}

    except KeyboardInterrupt:
        print(f"Interrupted at Sample_ID={sid}. Saving checkpoint and exiting...")
        save_checkpoint_ids(done_ids)
        raise
    except Exception as e:
        data['predict_answer'] = f"[ERROR] {e}"
        data['pred_data'] = {"dates": [], "values": [], "error": f"processing_failed: {str(e)}"}
        print(f"[ERROR][{sid}] {e}")

    out_rec = {
        "Sample_ID": sid,
        "predict_answer": data.get("predict_answer"),
        "pred_data": data.get("pred_data"),
        "BERT_pred_intent": data.get("BERT_pred_intent"),
        "question": data.get("question"),
        "answer": data.get("answer"),
        "generated_history_sql": data.get("generated_history_sql", ""),
        "db_history_answer_count": len(history_answer) if 'history_answer' in locals() else 0,
        "db_history_list_count": len(history_list) if 'history_list' in locals() else 0,
        "db_row_count": data.get("db_row_count", 0)
    }
    append_jsonl(out_rec)

    done_ids.add(sid)
    if len(done_ids) % 20 == 0:
        save_checkpoint_ids(done_ids)

save_checkpoint_ids(done_ids)

existing_outputs = load_existing_outputs()
merged = []
for d in datas:
    sid = get_sample_id(d)
    if sid in existing_outputs:
        d.update(existing_outputs[sid])
    merged.append(d)

with open(MERGED_OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)
print(f"Saved merged outputs to: {MERGED_OUTPUT_JSON}")

from sklearn.metrics import mean_squared_error, mean_absolute_error, precision_score, recall_score, f1_score, accuracy_score

regression_intents = ['Stock Price Prediction']
classification_intents = ['Stock Trend Prediction', 'Stock Extremum Prediction']

def flatten_floats(data):
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
    if isinstance(value, list):
        if len(value) == 1:
            return normalize_single_value(value[0])
        else:
            return [str(item).strip() for item in value]
    
    value_str = str(value).strip()
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
        parts = [p.strip() for p in value_str.split('\n') if p.strip()]
        if len(parts) > 1:
            return parts
        elif len(parts) == 1:
            return parts[0]
    
    if ',' in value_str or (' ' in value_str and len(value_str.split()) > 1):
        parts = re.split(r'[\s,]+', value_str.strip())
        valid_parts = [p.strip() for p in parts if p.strip() and p.strip() not in [',', ' ']]
        if len(valid_parts) > 1:
            return valid_parts
        elif len(valid_parts) == 1:
            return valid_parts[0]
    
    return value_str

def is_multi_value(data):
    if data is None:
        return False
    processed = normalize_single_value(data)
    return isinstance(processed, list) and len(processed) > 1

def preprocess_data(data):
    return normalize_single_value(data)

def calc_col_prf(pred, gold):
    pred_processed = preprocess_data(pred)
    gold_processed = preprocess_data(gold)
    
    if not is_multi_value(pred) and not is_multi_value(gold):
        if pred_processed == gold_processed:
            return 1, 0, 0
        else:
            return 0, 1, 1
    
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

def calc_acc(pred, gold):
    pred_processed = preprocess_data(pred)
    gold_processed = preprocess_data(gold)
    
    if not is_multi_value(pred) and not is_multi_value(gold):
        return 1 if pred_processed == gold_processed else 0
    
    pred_list = pred_processed if isinstance(pred_processed, list) else [pred_processed]
    gold_list = gold_processed if isinstance(gold_processed, list) else [gold_processed]
    
    return 1 if sorted(pred_list) == sorted(gold_list) else 0

def calc_prf1(tp, fp, fn):
    P = tp / (tp + fp) if (tp + fp) else 0
    R = tp / (tp + fn) if (tp + fn) else 0
    F1 = 2 * P * R / (P + R) if (P + R) else 0
    return P, R, F1

y_true_reg, y_pred_reg = [], []
y_true_cls, y_pred_cls = [], []
total = 0

P_list, R_list, F1_list = [], [], []
acc_count = 0
tp_total = fp_total = fn_total = 0
error_threshold = 50
high_error_count = 0

for data in merged:
    pred_source = data.get('predict_answer')
    gold = data.get('answer')
    intent = data.get('BERT_pred_intent')
    
    if intent in regression_intents:
        gold = data.get("answer")
        pred_source = data.get("predict_answer")
            
        if pred_source is None or pred_source == "0" or pred_source == 0:
            print(f"[Regression skipped] id={data.get('Sample_ID')}: predict_answer is empty or 0")
            continue
                
        y_true_vals = flatten_floats(gold)
        y_pred_vals = flatten_floats(pred_source)

        if len(y_true_vals) == len(y_pred_vals) and len(y_true_vals) > 0:
            valid_pairs = []
            errors = []
                
            for true_val, pred_val in zip(y_true_vals, y_pred_vals):
                error = abs(true_val - pred_val)
                errors.append(error)
                if error <= error_threshold:
                    valid_pairs.append((true_val, pred_val))
                else:
                    print(f"[High error skipped] id={data.get('Sample_ID')}: error {error:.2f} > {error_threshold}")
                
            if len(valid_pairs) == len(y_true_vals):
                true_vals_valid, pred_vals_valid = zip(*valid_pairs)
                print(f"[Regression detailed comparison] id={data.get('Sample_ID')}")
                print(f"  True values: {true_vals_valid}")
                print(f"  Predicted values: {pred_vals_valid}")
                print(f"  Errors: {errors}")
                    
                y_true_reg.extend(true_vals_valid)
                y_pred_reg.extend(pred_vals_valid)
            else:
                high_error_count += 1
                print(f"[Regression skipped] id={data.get('Sample_ID')}: {len(valid_pairs)}/{len(y_true_vals)} values have error less than {error_threshold}")
        else:
            print(f"[Regression] Length mismatch/empty: id={data.get('Sample_ID')}, y_true={y_true_vals}, y_pred={y_pred_vals}")
    
    elif intent in classification_intents:
        print(f"Intent: {intent}")
        print(f"Raw prediction: {repr(pred_source)}")
        print(f"Raw true value: {repr(gold)}")
        pred_processed = preprocess_data(pred_source)
        gold_processed = preprocess_data(gold)
        print(f"Processed prediction: {repr(pred_processed)} (Type: {type(pred_processed)}, Multi-value: {is_multi_value(pred_source)})")
        print(f"Processed true value: {repr(gold_processed)} (Type: {type(gold_processed)}, Multi-value: {is_multi_value(gold)})")
        acc = calc_acc(pred_source, gold)
        acc_count += acc
        total += 1

        tp, fp, fn = calc_col_prf(pred_source, gold)
        P, R, F1 = calc_prf1(tp, fp, fn)
        P_list.append(P)
        R_list.append(R)
        F1_list.append(F1)
        
        if is_multi_value(pred_source) or is_multi_value(gold):
            print(f"Multi-value sample result - Acc: {acc}, P: {P:.4f}, R: {R:.4f}, F1: {F1:.4f}")
        print("-" * 50)

avg_P = sum(P_list) / len(P_list) if P_list else 0
avg_R = sum(R_list) / len(R_list) if R_list else 0
avg_F1 = sum(F1_list) / len(F1_list) if F1_list else 0
avg_acc = acc_count / total if total else 0

def mean_relative_error(y_true, y_pred, epsilon=1):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    mask = np.abs(y_true) > epsilon
    if np.sum(mask) == 0:
        return np.nan
    return np.mean(np.abs(y_true[mask] - y_pred[mask]) / np.abs(y_true[mask])) 

if y_true_reg and y_pred_reg:
    print("Regression intent statistics:")
    print(f" MSE: {mean_squared_error(y_true_reg, y_pred_reg):.8f}")
    print(f" MAE: {mean_absolute_error(y_true_reg, y_pred_reg):.8f}")
    print(f" MRE: {mean_relative_error(y_true_reg, y_pred_reg):.8f}")

print(f"Avg Acc: {avg_acc:.4f}")
print(f'PRF1 per-sample average: P={avg_P:.4f}, R={avg_R:.4f}, F1={avg_F1:.4f}')