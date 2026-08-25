import os  
import pandas as pd  
import json  
import random
from template import template_data
from tqdm import tqdm
import sql_verify
import re
from test_split import bert_split 
from time_period import time_period,fuzzy_times_old,time_period_past,festival_date
from BIO import BIO_fuzzy_times,BIO_time_period,BIO_time_period_past,BIO_festival_date
from concurrent.futures import ThreadPoolExecutor  

data_path = "/home/***/dataset/split_datasets/train_dataset"  
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
    
    for key in BIO_time_period:
        if key in phrase:
            idx = phrase.index(key) 
            start_idx = len(split(phrase[:idx]))  
            for j in range(len(BIO_time_period[key])):  
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_time_period[key][j]

    for key in BIO_fuzzy_times:
        if key in phrase:
            idx = phrase.index(key)
            start_idx = len(split(phrase[:idx]))
            for j in range(len(BIO_fuzzy_times[key])):
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_fuzzy_times[key][j]

    for key in BIO_time_period_past:
        if key in phrase:
            idx = phrase.index(key)
            start_idx = len(split(phrase[:idx]))
            for j in range(len(BIO_time_period_past[key])):
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_time_period_past[key][j]
    
    for key in BIO_festival_date:
        if key in phrase:
            idx = phrase.index(key)
            start_idx = len(split(phrase[:idx]))
            for j in range(len(BIO_festival_date[key])):
                if start_idx + j < len(bio_tags):
                    bio_tags[start_idx + j] = BIO_festival_date[key][j]

    return bio_tags
       
test_questions = [  
    "What are the maximum opening prices for SWX during the past three days?",  
]  

for question in test_questions:  
    bio_tags = generate_bio_slots_from_question(question)  
    print(f"Question: '{question}'")  
    print(f"BIO Tags: {bio_tags}\n") 


def extract_stock_names_from_question(question, stock_name, stock_name1, stock_name2):
    stock_names = set()
    if stock_name and stock_name in question:
        stock_names.add(stock_name)
    if stock_name1 and stock_name1 in question:
        stock_names.add(stock_name1)
    if stock_name2 and stock_name2 in question:
        stock_names.add(stock_name2)
    return ", ".join(stock_names)
 
def generate_qa_data(stock_data, template, num_samples=200):  

    qa_data = []  
    stock_names = list(stock_data.keys())  

    def process_sample(i):   
        stock_name = random.choice(stock_names)

        stock_name1 = random.choice(stock_names)  
        stock_name2 = random.choice(stock_names)   

        data = stock_data[stock_name]  

        data['date'] = pd.to_datetime(data['date'])  
 
        filtered_data = data[(data['date'] >= '2020-01-01') & (data['date'] <= '2023-11-24')]  
        filtered_data_1_3 = data[(data['date'] >= '2023-11-01') & (data['date'] <= '2023-11-16')]
        filtered_data_1_2 = data[(data['date'] >= '2023-11-17') & (data['date'] <= '2023-11-24')]
        if filtered_data.empty:  
            return None  

        date_sample = random.choice(filtered_data['date'].dt.strftime('%Y-%m-%d').tolist())  
        date_sample1 = random.choice(filtered_data_1_2['date'].dt.strftime('%Y-%m-%d').tolist())  
        date_sample2 = random.choice(filtered_data_1_3['date'].dt.strftime('%Y-%m-%d').tolist())  

        time_period_key = random.choice(list(time_period.keys()))
        time_period_past_key = random.choice(list(time_period_past.keys()))
        fuzzy_time_key = random.choice(list(fuzzy_times_old.keys()))
        festival_date_key = random.choice(list(festival_date.keys()))

        time_period_value = time_period[time_period_key][0]
        time_period_past_value = time_period_past[time_period_past_key][0]
        fuzzy_time_value = fuzzy_times_old[fuzzy_time_key][0]
        festival_date_value = festival_date[festival_date_key][0]

        sql_statement = template["SQL"].replace("{Stockname}", stock_name) \
            .replace("{Stockname1}", stock_name1) \
            .replace("{Stockname2}", stock_name2) \
            .replace("{Time}", date_sample) \
            .replace("{Time_1}", date_sample1) \
            .replace("{Time_2}", date_sample2) \
            .replace("{Period_1}", time_period_past_value) \
            .replace("{Period_2}", time_period_value) \
            .replace("{Fuzzy_time}", fuzzy_time_value) \
            .replace("{Holiday_time}", festival_date_value)
        
        history_sql = template["HISTORY_SQL"].replace("{Stockname}", stock_name) \
            .replace("{Stockname1}", stock_name1) \
            .replace("{Stockname2}", stock_name2) \
            .replace("{Time}", date_sample) \
            .replace("{Time_1}", date_sample1) \
            .replace("{Time_2}", date_sample2) \
            .replace("{Period_1}", time_period_past_value) \
            .replace("{Period_2}", time_period_value) \
            .replace("{Fuzzy_time}", fuzzy_time_value) \
            .replace("{Holiday_time}", festival_date_value)

        question = template["Opening Price Inquiry"] \
            .replace("{Stockname}", stock_name) \
            .replace("{Stockname1}", stock_name1) \
            .replace("{Stockname2}", stock_name2) \
            .replace("{Time}", date_sample) \
            .replace("{Time_1}", date_sample1) \
            .replace("{Time_2}", date_sample2) \
            .replace("{Period_1}", time_period_past_key) \
            .replace("{Period_2}", time_period_key) \
            .replace("{Fuzzy_time}", fuzzy_time_key) \
            .replace("{Holiday_time}", festival_date_key)

        answer = []
        result = sql_verify.find_answer(sql_statement)  
        answer = result if result else "Trading Halt"  

        if answer == "Trading Halt":  
            return None  
        
 
        result_history = sql_verify.find_answer(history_sql)  
        if result_history:  
            history_answer_str = result_history
        else:  
            history_answer_str = "Trading Halt"  

        bio_annotation = generate_bio_slots_from_question(question)
        stock_name_str = extract_stock_names_from_question(question, stock_name, stock_name1, stock_name2)

        return {  
            "Sample_ID": f"{i+1:05d}",  
            "stock_name": stock_name_str,
            "sql_statement": sql_statement,  
            "question": question,  
            "answer": answer,  
            "bio_annotation": " ".join(bio_annotation),  
            "Intent": "Opening Price Inquiry",
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
    for i in range(15,16):
        try:
            template = template_data[i]  

            qa_data = generate_qa_data(stock_data, template, num_samples=800)  

            save_to_json(qa_data, file_name=f"/home/***/dataset/output_train_dataset/qa_data{i+1}.json")  
            print("QA data has been saved to qa_data.json file!")    
        except:
            continue 

if __name__ == "__main__":  
    main()     