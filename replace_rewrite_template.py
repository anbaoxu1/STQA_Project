import json
import re
from tqdm import tqdm
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI 

polish_prompt_file = '/home/***/code/stock_generate/polish_question_predict.json'
with open(polish_prompt_file, 'r', encoding='utf-8') as f:
    polish_prompt_str = json.load(f)["template"]

llm = ChatOpenAI(
    base_url="http://*******.*****.***:8080/v1",
    api_key="**************************************",
    model="gpt-oss-120b"
)
polish_prompt = ChatPromptTemplate.from_template(polish_prompt_str)
polish_chain = polish_prompt | llm

def extract_question_from_json(output):
    output = output.strip()
    if output.startswith("```"):
        lines = output.splitlines()
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        output = "\n".join(lines).strip()
    try:
        js = json.loads(output)
        if isinstance(js, dict):
            if "question" in js:
                return js["question"]
            if len(js) == 1 and list(js.values())[0] is None:
                return list(js.keys())[0]
        elif isinstance(js, list) and len(js):
            return js[0]
    except Exception:
        pass
    m = re.match(r'^\{\s*[\'"]?(.+?)[\'"]?\s*\}$', output)
    if m:
        return m.group(1).strip()
    m2 = re.match(r'^\{\s*[\'"]?(.+)', output)
    if m2:
        return m2.group(1).strip(' "\'\n')
    if output.startswith("{"):
        output = output[1:].strip(' "\'\n')
    if output.endswith("}"):
        output = output[:-1].strip(' "\'\n')
    if (output.startswith('"') and output.endswith('"')) or (output.startswith("'") and output.endswith("'")):
        output = output[1:-1].strip()
    output = output.strip(' "\'\n\\')
    return output

def extract_questions(input_file_path):
    with open(input_file_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f) 
    original_questions = []
    for item in dataset:
        if "question" in item:
            original_questions.append(item["question"])
        else:
            original_questions.append("")
            print(f"Warning: Found data missing 'question' field, Sample_ID: {item.get('Sample_ID', 'Unknown')}")
    return original_questions

def polish_questions(question_list):
    polished_list = []
    for question in tqdm(question_list, desc="Rewriting questions"):
        try:
            polish_resp = polish_chain.invoke({"question": question}).content
            new_question = extract_question_from_json(polish_resp)
            polished_list.append(new_question)
        except Exception as e:
            print(f"Rewriting failed, original question: '{question[:30]}...', error: {e}")
            polished_list.append(question)  
    return polished_list

def save_to_json(data_list, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    print(f"Saved: {output_file_path} (Total {len(data_list)} items)")

def main():
    input_file = '/home/***/dataset/extract_dataset_people_score/first_two_entries_simple.json'
    original_output_file = '/home/***/dataset/extract_dataset_people_score/original_questions_diff_only.json'
    polished_output_file = '/home/***/dataset/extract_dataset_people_score/polished_questions_diff_only.json'

    print("Step 1/3: Extracting original questions from dataset...")
    original_questions = extract_questions(input_file)
    print(f"Successfully extracted {len(original_questions)} original questions.")

    print("\nStep 2/3: Batch rewriting questions using LLM...")
    polished_questions = polish_questions(original_questions)

    print("\nStep 3/3: Filtering and saving results with differences...")
    
    filtered_original = []
    filtered_polished = []
    
    for orig, pol in zip(original_questions, polished_questions):
        if orig.strip() != pol.strip():
            filtered_original.append(orig)
            filtered_polished.append(pol)
            
    print(f"Filtering completed: {len(original_questions)} total items, {len(filtered_original)} items changed.")

    if len(filtered_original) > 0:
        save_to_json(filtered_original, original_output_file)
        save_to_json(filtered_polished, polished_output_file)
        
        print("\n--- Difference examples (first 3) ---")
        for i in range(min(3, len(filtered_original))):
            print(f"{i+1}. Original: {filtered_original[i]}")
            print(f"   Rewritten: {filtered_polished[i]}\n")
    else:
        print("No changes found, no files saved.")

    print("\n✅ All tasks completed!")

if __name__ == "__main__":
    main()