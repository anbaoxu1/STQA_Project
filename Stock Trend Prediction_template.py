import os  
import pandas as pd  
import json  
import random
from template_pred_plus import template_data
from tqdm import tqdm
import sql_verify
from collections import OrderedDict
import re
from time_period import fuzzy_times_future,time_period_future,time_period_future_future,festival_date,time_period_past
from BIO import BIO_fuzzy_times_future,BIO_time_period_future,BIO_time_period_future_future,BIO_festival_date,BIO_last_date,BIO_past_date
from test_split import bert_split 
from concurrent.futures import ThreadPoolExecutor

data_path = "/home/bbx/dataset/split_datasets/test_dataset"  
# data_path = "/home/bbx/dataset/val_dataset"
stock_data = {}  

csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]  
for filename in tqdm(csv_files):  
    file_path = os.path.join(data_path, filename)  
    stock_name = filename.replace(".csv", "").upper()  
    stock_data[stock_name] = pd.read_csv(file_path)  

def split(sentence):
    return sentence.split()
def generate_bio_slots_from_question(question):  
    words = bert_split(question) 
    bio_tags = ["O"] * len(words)  
  
    stock_name_pattern = r"^[A-Z]{1,3}$"  
    stock_name_pattern_I = r"^##[A-Z]{1,2}$"  
    stock_name_pattern_year = r'^\d{3,4}$'  
    stock_name_pattern_year_I = r"^##[1-9]{1,5}$"  
    stock_name_pattern_month = r'^(0[1-9]|1[0-2])$'  
    stock_name_pattern_day = r'^(0[1-9]|[12][0-9]|3[0-1])$'  
    
    year_found = False  
    month_found = False  

    for i, word in enumerate(words):  
        if re.match(stock_name_pattern, word):   
            bio_tags[i] = "B-stock_name"  

        if re.match(stock_name_pattern_I, word): 
            bio_tags[i] = "I-stock_name"
                
        if re.match(stock_name_pattern_year, word): 
            bio_tags[i] = "B-year" 
            year_found = True 

        if year_found and re.match(stock_name_pattern_month, word):  
            bio_tags[i] = "B-month"   
            month_found = True 

        if month_found and re.match(stock_name_pattern_day, word):  
            bio_tags[i] = "B-day" 
            
        if re.match(stock_name_pattern_year_I, word): 
            bio_tags[i] = "I-year"  

    if "B-month" not in bio_tags:  
        for i in range(len(bio_tags)):  
            if bio_tags[i] == "B-day":  
                bio_tags[i] = "B-month" 
                break 

    phrase = ' '.join(words)  
    
    for key in BIO_time_period_future:
        if key in phrase:
            idx = phrase.index(key)  
            start_idx = len(split(phrase[:idx]))  
            for j in range(len(BIO_time_period_future[key])):  
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_time_period_future[key][j]

    for key in BIO_fuzzy_times_future:
        if key in phrase:
            idx = phrase.index(key)
            start_idx = len(split(phrase[:idx]))
            for j in range(len(BIO_fuzzy_times_future[key])):
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_fuzzy_times_future[key][j]


    for key in BIO_time_period_future_future:
        if key in phrase:
            idx = phrase.index(key)
            start_idx = len(split(phrase[:idx]))
            for j in range(len(BIO_time_period_future_future[key])):
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_time_period_future_future[key][j]
    
    for key in BIO_festival_date:
        if key in phrase:
            idx = phrase.index(key)
            start_idx = len(split(phrase[:idx]))
            for j in range(len(BIO_festival_date[key])):
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_festival_date[key][j]

    for key in BIO_last_date:
        if key in phrase:
            idx = phrase.index(key)
            start_idx = len(split(phrase[:idx]))
            for j in range(len(BIO_last_date[key])):
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_last_date[key][j]

    for key in BIO_past_date:
        if key in phrase:
            idx = phrase.index(key)
            start_idx = len(split(phrase[:idx]))
            for j in range(len(BIO_past_date[key])):
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_past_date[key][j]                

    return bio_tags            

def generate_qa_data(stock_data, template, num_samples=200):  
    qa_data = []  
    stock_names = list(stock_data.keys())   

    def process_sample(i):   
        stock_name = random.choice(stock_names)  
        stock_name1 = random.choice(stock_names)  
        stock_name2 = random.choice(stock_names)   

        data = stock_data[stock_name]  
 
        data['date'] = pd.to_datetime(data['date'])  

        filtered_data = data[(data['date'] >= '2023-11-25') & (data['date'] <= '2023-12-09')]  

        if filtered_data.empty:  
            return None  

        date_sample = random.choice(filtered_data['date'].dt.strftime('%Y-%m-%d').tolist())  
        date_sample1 = random.choice(filtered_data['date'].dt.strftime('%Y-%m-%d').tolist())  
        date_sample2 = random.choice(filtered_data['date'].dt.strftime('%Y-%m-%d').tolist())  

        time_period_future_key = random.choice(list(time_period_future.keys()))
        time_period_future_future_key = random.choice(list(time_period_future_future.keys()))
        festival_date_key = random.choice(list(festival_date.keys()))
        fuzzy_time_future_key = random.choice(list(fuzzy_times_future.keys()))
        time_period_past_key = random.choice(list(time_period_past.keys()))

        time_period_value = time_period_future[time_period_future_key][0]
        time_period_future_future_value = time_period_future_future[time_period_future_future_key][0]
        festival_date_value = festival_date[festival_date_key][0]
        fuzzy_time_value = fuzzy_times_future[fuzzy_time_future_key][0]
        time_period_past_value = time_period_past[time_period_past_key][0]

        sql_statement = template["SQL_target"].replace("{Stockname}", stock_name) \
            .replace("{Stockname1}", stock_name1) \
            .replace("{Stockname2}", stock_name2) \
            .replace("{Time}", date_sample) \
            .replace("{Time1}", date_sample1) \
            .replace("{Time2}", date_sample2) \
            .replace("{Time_period1}", time_period_value) \
            .replace("{Time_period2}", time_period_future_future_value) \
            .replace("{Festival_time}", festival_date_value) \
            .replace("{Fuzzy_time}", fuzzy_time_value) \
            .replace("{Time_period3}", time_period_past_value)
        
        history_sql = template["HISTORY_SQL"].replace("{Stockname}", stock_name).replace("{Stockname1}", stock_name1).replace("{Stockname2}", stock_name2).replace("{Time}", date_sample).replace("{Time1}", date_sample1).replace("{Time2}", date_sample2).replace("{Fuzzy_time}", fuzzy_time_value)
        
        question = template["question"] \
            .replace("{Stockname}", stock_name) \
            .replace("{Stockname1}", stock_name1) \
            .replace("{Stockname2}", stock_name2) \
            .replace("{Time}", date_sample) \
            .replace("{Time1}", date_sample1) \
            .replace("{Time2}", date_sample2) \
            .replace("{Time_period1}", time_period_future_key) \
            .replace("{Time_period2}", time_period_future_future_key) \
            .replace("{Festival_time}", festival_date_key) \
            .replace("{Fuzzy_time}", fuzzy_time_future_key) \
            .replace("{Time_period3}", time_period_past_key)
  
        result = sql_verify.find_answer(sql_statement)
        if result:  
            answer_str = ' '.join(str(item) for item in result[0]) 
        else:  
            answer_str = "Trading Halt"  
        
        print(f"answer: {answer_str}")  
        if answer_str == "Trading Halt":  
            return None  
 
        result_history = sql_verify.find_answer(history_sql)  
        if result_history:  
            history_answer_str = result_history
        else:  
            history_answer_str = "Trading Halt"  
        bio_annotation = generate_bio_slots_from_question(question)  
        return {  
                "Sample_ID": f"{i+1:05d}",  
                "stock_name": stock_name,    
                "sql_statement": sql_statement,  
                "question": question,  
                "answer": answer_str,  
                "bio_annotation": " ".join(bio_annotation),  
                "Intent": "Stock Trend Prediction",
                "bert_split": " ".join(bert_split(question)),
                "history_sql": history_sql,
                "history_answer": history_answer_str,   
            }
    while len(qa_data) < num_samples: 
        with ThreadPoolExecutor() as executor:  
            results = list(executor.map(process_sample, range(num_samples)))  
 
        qa_data.extend([result for result in results if result is not None])  
 
    qa_data = qa_data[:num_samples]  
    for i in range(len(qa_data)):  
        qa_data[i]["Sample_ID"] = f"{i + 1:05d}"

    return qa_data   

def save_to_json(data, file_name="qa_data.json"):  
    with open(file_name, "w", encoding="utf-8") as f:  
        json.dump(data, f, ensure_ascii=False, indent=4)  

def main():  
    for i in range(5,11):
        try:
            template = template_data[i]  

            qa_data = generate_qa_data(stock_data, template, num_samples=1000)  
 
            save_to_json(qa_data, file_name=f"/home/bbx/dataset/output_test_dataset_predict/qa_data{i+1}.json")  
            print("QA data has been saved to qa_data.json file!")    
        except:
            continue 

if __name__ == "__main__":  
    main()     