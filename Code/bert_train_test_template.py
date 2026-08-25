import torch
import numpy as np
from transformers import BertTokenizer
import json
import pandas as pd
from torch import nn
from transformers import BertModel
from torch.optim import Adam
from tqdm import tqdm
from ipywidgets import FloatProgress
from torch.utils.tensorboard import SummaryWriter
import re
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from tqdm import tqdm
from sklearn import metrics
import json
import pandas as pd
from test_split import bert_split
import os  
os.environ["TOKENIZERS_PARALLELISM"] = "false"  
BERT_PATH = '/home/***/code/stock_generate/bert-base-cased'
tokenizer = BertTokenizer.from_pretrained(BERT_PATH)

def pad_to_512(input_string, max_pad_lenth=512):
    while len(input_string) < max_pad_lenth:
        input_string.append(int(-100))
    return input_string

intents_num = {  
    'Opening Price Inquiry': 0,   
    'Closing Price Inquiry': 1,    
    'Stock Trading Volume Inquiry': 2,
    'Stock Price Prediction': 3,
    'Stock Trend Prediction': 4,
    'Stock Extremum Prediction': 5,
    'Stock Return Rate Prediction': 6, 
} 

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

def json2dataframe(all_datas):  
    df = pd.DataFrame(columns=['intent_vector', 'question', 'intent_flag', 'slots'])
    for data in all_datas:  
        question = data['question']    
        intent_str = data['Intent']
        intents = []
        bio_str_list = data['bio_annotation'].split(' ')    
        bio_str_list.insert(0, 'O')  
        bio_str_list.append('O')
        numbered_slots = [slots_num[item] for item in bio_str_list]  

        intent_vector = [0.0] * len(intents_num)
        intent_flag = 0
        if data['Intent'] not in intents and '+' not in data['Intent']:
            intents.append(data['Intent'])
        if '+' in intent_str:  
            sub_intents = intent_str.split('+')  
            intent_flag = 1  
            for sub_intent in sub_intents:  
                intent_vector[intents_num[sub_intent]] = 1.0
            df = pd.concat([df, pd.DataFrame([{'intent_vector': intent_vector, 'question': question, 'intent_flag': intent_flag, 'slots': numbered_slots}])], ignore_index=True)  
        elif '+' not in data['Intent']:  
            intent_str = data['Intent']
            intent_vector[intents_num[intent_str]] = 1.0  
            df = pd.concat([df, pd.DataFrame([{'intent_vector': intent_vector, 'question': question, 'intent_flag': intent_flag, 'slots': numbered_slots}])], ignore_index=True)

    df['slots'] = df['slots'].apply(pad_to_512)  
    return df

train_path = '/home/***/dataset/train_merged.json'
with open(train_path, 'r', encoding='utf-8') as f:
    all_datas = json.load(f)
df_train = json2dataframe(all_datas)

validation_path = '/home/***/dataset/val_merged.json'
with open(validation_path, 'r', encoding='utf-8') as f:
    all_datas = json.load(f)
df_val = json2dataframe(all_datas)

test_path = '/home/***/dataset/test_merged.json'
with open(test_path, 'r', encoding='utf-8') as f:
    all_datas = json.load(f)
df_test = json2dataframe(all_datas)

print(len(df_train), len(df_val), len(df_test))

class Dataset(torch.utils.data.Dataset):
    def __init__(self, df):
        self.labels = df['intent_vector']
        self.texts = df['question']
        self.num_intents = df['intent_flag']
        self.slots = df['slots']

    def classes(self):
        return self.labels

    def __len__(self):
        return len(self.labels)

    def get_batch_labels(self, idx):
        return np.array(self.labels[idx])

    def get_batch_texts(self, idx):
        return self.texts[idx]

    def get_batch_num_intents(self, idx):
        return np.array(self.num_intents[idx])

    def get_batch_slots(self, idx):
        return np.array(self.slots[idx])

    def __getitem__(self, idx):
        batch_texts = self.get_batch_texts(idx)
        batch_y = self.get_batch_labels(idx)
        batch_num = self.get_batch_num_intents(idx)
        batch_slots = self.get_batch_slots(idx)
        return batch_texts, batch_y, batch_num, batch_slots

class BertClassifier(nn.Module):
    def __init__(self, dropout=0.5):
        super(BertClassifier, self).__init__()
        self.bert = BertModel.from_pretrained(BERT_PATH)
        self.dropout = nn.Dropout(dropout)
        self.linear1 = nn.Linear(768, 7)
        self.linear2 = nn.Linear(768, 2)
        self.linear3 = nn.Linear(768, 12)
        self.sigmoid = nn.Sigmoid()
        self.softmax = nn.Softmax()

    def forward(self, input_id, mask):
        last_hidden_state, pooled_output = self.bert(input_ids=input_id, attention_mask=mask, return_dict=False)
        dropout_output = self.dropout(pooled_output)
        linear1_output = self.linear1(dropout_output)
        intent_probability = self.sigmoid(linear1_output)
        num_intents = self.linear2(dropout_output)
        last_hidden_state_output = self.dropout(last_hidden_state)
        slot_probability = self.linear3(last_hidden_state_output)
        return intent_probability, num_intents, slot_probability

def tensors_equal_ignore_order(tensor1, tensor2):
    sorted_tensor1, _ = torch.sort(tensor1)
    sorted_tensor2, _ = torch.sort(tensor2)
    results = []
    for row1, row2 in zip(sorted_tensor1, sorted_tensor2):
        results.append(torch.equal(row1, row2))
    results_tensor = torch.tensor(results, dtype=torch.bool)
    return results_tensor

def compute_multi_label_acc(probility, label):
    probility, idx1 = torch.sort(probility, descending=True)
    label, idx2 = torch.sort(label, descending=True)
    idx1 = idx1[:,0:2]
    idx2 = idx2[:,0:2]
    for i, labl in enumerate(label):
        if labl.sum() < 2:
            idx1[i,1] = 0
            idx2[i,1] = 0
    acc = tensors_equal_ignore_order(idx1, idx2).sum().item()
    return acc

def train(model, train_data, val_data, learning_rate, epochs):
    train, val = Dataset(train_data), Dataset(val_data)
    train_dataloader = torch.utils.data.DataLoader(train, batch_size=5, shuffle=True)
    val_dataloader = torch.utils.data.DataLoader(val, batch_size=5)
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    criterion = nn.CrossEntropyLoss()
    binary_criterion = nn.BCELoss()
    optimizer = Adam(model.parameters(), lr=learning_rate)
    if use_cuda:
        model = model.cuda()
        criterion = criterion.cuda()
    for epoch_num in range(epochs):
        total_intent_acc_train = 0
        total_num_acc_train = 0
        total_loss_train = 0
        total_slot_acc_train = 0
        total_tokens_train = 0
        for train_input, train_intent_label, train_num_label, train_slot_label in tqdm(train_dataloader):
            train_intent_label = train_intent_label.to(device)
            train_num_label = train_num_label.to(device)
            train_slot_label = train_slot_label.to(device)
            encoding = tokenizer(train_input, padding='max_length', max_length=512, truncation=True, return_tensors="pt")  
            input_id = encoding['input_ids'].squeeze(1).to(device)  
            mask = encoding['attention_mask'].squeeze(1).to(device)

            intent_probability, num_intents, slot_probability = model(input_id, mask)
            
            intent_loss = binary_criterion(intent_probability, train_intent_label.float())
            active_loss = mask.view(-1) == 1
            active_logits = slot_probability.view(-1, 12)[active_loss]
            active_labels = train_slot_label.view(-1)[active_loss]
            slot_loss = criterion(active_logits, active_labels)
            num_loss = criterion(num_intents, train_num_label)
            loss = intent_loss + num_loss + slot_loss
            total_loss_train += loss.item()
            
            intent_acc = compute_multi_label_acc(intent_probability, train_intent_label)
            total_intent_acc_train += intent_acc
            num_intent_acc = (num_intents.argmax(dim=1) == train_num_label).sum().item()
            total_num_acc_train += num_intent_acc
            word_leval_slots_acc = (slot_probability.argmax(dim=2).view(-1) == train_slot_label.view(-1)).sum().item()
            batch_token_nums = active_loss.sum().item()
            total_slot_acc_train += word_leval_slots_acc
            total_tokens_train += batch_token_nums
            
            model.zero_grad()
            loss.backward()
            optimizer.step()
        
        total_intent_acc_val = 0
        total_num_acc_val = 0
        total_loss_val = 0
        total_slot_acc_val = 0
        total_tokens_val = 0
        with torch.no_grad():
            for val_input, val_intent_label, val_num_label, val_slot_label in val_dataloader:
                val_intent_label = val_intent_label.to(device)
                val_num_label = val_num_label.to(device)
                val_slot_label = val_slot_label.to(device)
                encoding = tokenizer(val_input, padding='max_length', max_length=512, truncation=True, return_tensors="pt")  
                input_id = encoding['input_ids'].squeeze(1).to(device)  
                mask = encoding['attention_mask'].squeeze(1).to(device)
                intent_probability, num_intents, slot_probability = model(input_id, mask)
                intent_loss = binary_criterion(intent_probability, val_intent_label.float())

                active_loss = mask.view(-1) == 1
                active_logits = slot_probability.view(-1, 12)[active_loss]
                active_labels = val_slot_label.view(-1)[active_loss]
                slot_loss = criterion(active_logits, active_labels)

                num_loss = criterion(num_intents, val_num_label)
                loss = intent_loss + num_loss + slot_loss
                total_loss_val += loss.item()
                
                intent_acc = compute_multi_label_acc(intent_probability, val_intent_label)
                total_intent_acc_val += intent_acc
                num_intent_acc = (num_intents.argmax(dim=1) == val_num_label).sum().item()
                total_num_acc_val += num_intent_acc
                word_leval_slots_acc = (slot_probability.argmax(dim=2).view(-1)[active_loss] == val_slot_label.view(-1)[active_loss]).sum().item()
                batch_token_nums = active_loss.sum().item()
                total_slot_acc_val += word_leval_slots_acc
                total_tokens_val += batch_token_nums
        
        writer.add_scalar('Loss/train', total_loss_train / len(train_data), epoch_num)
        writer.add_scalar('Accuracy/train_intent', total_intent_acc_train / len(train_data), epoch_num)
        writer.add_scalar('Accuracy/train_num_intents', total_num_acc_train / len(train_data), epoch_num)
        writer.add_scalar('Accuracy/train_token_level_slot_acc', total_slot_acc_train / total_tokens_train, epoch_num)
        writer.add_scalar('Loss/val', total_loss_val / len(val_data), epoch_num)
        writer.add_scalar('Accuracy/val_intent', total_intent_acc_val / len(val_data), epoch_num)
        writer.add_scalar('Accuracy/val_num_intents', total_num_acc_val / len(val_data), epoch_num)
        writer.add_scalar('Accuracy/val_token_level_slot_acc', total_slot_acc_val / total_tokens_val, epoch_num)

        print(
            f'''Epochs: {epoch_num + 1} 
            | Train Loss: {total_loss_train / len(train_data): .3f} 
            | Train Intent Accuracy: {total_intent_acc_train / len(train_data): .3f}
            | Train Num of intents Accuracy: {total_num_acc_train / len(train_data): .3f} 
            | Train Token-level Slots Accuracy: {total_slot_acc_train / total_tokens_train: .3f} 
            | Val Loss: {total_loss_val / len(val_data): .3f} 
            | Val Intent Accuracy: {total_intent_acc_val / len(val_data): .3f}
            | Val Num of intents Accuracy: {total_num_acc_val / len(val_data): .3f}
            | Val Token-level Slots Accuracy: {total_slot_acc_val / total_tokens_val: .3f} ''')
        writer.close()

EPOCHS = 10
writer = SummaryWriter('./runs')
model = BertClassifier()
LR = 1e-6
train(model, df_train, df_val, LR, EPOCHS)

def evaluate(model, test_data):
    test = Dataset(test_data)
    test_dataloader = torch.utils.data.DataLoader(test, batch_size=4)
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    if use_cuda:
        model = model.cuda()
    total_intent_acc_test = 0
    total_num_acc_test = 0
    total_tokens_test = 0
    total_slot_acc_test = 0
    all_pred_intents = []
    all_true_intents = []

    with torch.no_grad():
        for test_input, test_intent_label, test_num_label, test_slot_label in test_dataloader:
            test_intent_label = test_intent_label.to(device)
            test_num_label = test_num_label.to(device)
            test_slot_label = test_slot_label.to(device)
            encoding = tokenizer(test_input, padding='max_length', max_length=512, truncation=True, return_tensors="pt")  
            input_id = encoding['input_ids'].squeeze(1).to(device)  
            mask = encoding['attention_mask'].squeeze(1).to(device)
            intent_probability, num_intents, slot_probability = model(input_id, mask)

            pred_intents = intent_probability.argmax(dim=1).cpu().tolist()
            true_intents = test_intent_label.argmax(dim=1).cpu().tolist()
            all_pred_intents.extend(pred_intents)
            all_true_intents.extend(true_intents)

            active_loss = mask.view(-1) == 1
            intent_acc = compute_multi_label_acc(intent_probability, test_intent_label)
            total_intent_acc_test += intent_acc
            num_intent_acc = (num_intents.argmax(dim=1) == test_num_label).sum().item()
            total_num_acc_test += num_intent_acc
            word_leval_slots_acc = (slot_probability.argmax(dim=2).view(-1)[active_loss] == test_slot_label.view(-1)[active_loss]).sum().item()
            batch_token_nums = active_loss.sum().item()
            total_slot_acc_test += word_leval_slots_acc
            total_tokens_test += batch_token_nums

    print(f'Test Intent Accuracy: {total_intent_acc_test*100 / len(test_data): .2f}%')
    print(f'Test Num of Intent Accuracy: {total_num_acc_test*100 / len(test_data): .2f}%')
    print(f'Test Token-level Slots Accuracy: {total_slot_acc_test*100 / total_tokens_test: .2f}%')

evaluate(model, df_test)
model_path = '/home/***/code/stock_generate/model/bert.pt'
torch.save(model, model_path)

def top2_indices(tensor):
    if len(tensor) < 2:
        raise ValueError("Input tensor must have at least 2 elements")
    _, indices = torch.topk(tensor, k=2, dim=0)
    return indices

def find_key(dictionary, value):
    return [key for key, val in dictionary.items() if val == value]

model_path = '/home/***/code/stock_generate/model/bert.pt'
model = torch.load(model_path)
use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")
if use_cuda:
    model = model.cuda()
BERT_PATH = '/home/***/code/stock_generate/bert-base-cased'
tokenizer = BertTokenizer.from_pretrained(BERT_PATH)

def align_tokens_with_query(tokens, query, query_slot):
    query = list(query)
    new_tokens = []
    origin_slot = query_slot
    if isinstance(origin_slot, type('str')):
        origin_slot = origin_slot.split(' ')
    new_slot = []
    for i, token in enumerate(tokens):
        if token == '[CLS]' or token == '[SEP]':
            continue
        elif token == query[0]:
            new_tokens.append(token)
            new_slot.append(origin_slot[0])
            query = query[1:]
            origin_slot = origin_slot[1:]
        elif '##' in token:
            token = token[2:]
            new_tokens.append(token)
            new_slot.append(origin_slot[0])
            for t in list(token):
                if t == query[0]:
                    query = query[1:]
                    origin_slot = origin_slot[1:]
        elif '[UNK]' == token:
            end_index = query.index(tokens[i+1])
            unk = ''.join(query[0:end_index])
            new_tokens.append(unk)
            new_slot.append(origin_slot[0])
            query = query[end_index:]
            origin_slot = origin_slot[1:]
        elif len(token) > 1:
            new_tokens.append(token)
            new_slot.append(origin_slot[0])
            for t in list(token):
                if t == query[0]:
                    query = query[1:]
                    origin_slot = origin_slot[1:]
    return new_tokens, new_slot

def restore_keywords_from_tokens(tokens, token_slot):
    keywords = []
    current_tokens = []
    current_label = None
    token_slot = token_slot[1:-1]

    for token, slot in zip(tokens, token_slot):
        if slot.startswith('B-'):
            if current_tokens:
                keywords.append((''.join(current_tokens), current_label))
                current_tokens = []
            current_label = slot[2:]
            current_tokens.append(token)
        elif slot.startswith('I-') and current_label == slot[2:]:
            current_tokens.append(token)
        else:
            if current_tokens:
                keywords.append((''.join(current_tokens), current_label))
                current_tokens = []
                current_label = None

    if current_tokens:
        keywords.append((''.join(current_tokens), current_label))

    return keywords

def restore_keywords_from_query(query, slots):
    keywords = []
    current_tokens = []
    current_label = None
    query = list(query)
    if slots[0] == '[CLS]':
        slots = slots[1:-1]

    for token, slot in zip(query, slots):
        if slot.startswith('B-'):
            if current_tokens:
                keywords.append((''.join(current_tokens), current_label))
                current_tokens = []
            current_label = slot[2:]
            current_tokens.append(token)
        elif slot.startswith('I-') and current_label == slot[2:]:
            current_tokens.append(token)
        else:
            if current_tokens:
                keywords.append((''.join(current_tokens), current_label))
                current_tokens = []
                current_label = None

    if current_tokens:
        keywords.append((''.join(current_tokens), current_label))

    return keywords

model_path = '/home/***/code/stock_generate/model/bert.pt'
model = torch.load(model_path)
use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")
if use_cuda:
    model = model.cuda()
BERT_PATH = '/home/***/code/stock_generate/bert-base-cased'
tokenizer = BertTokenizer.from_pretrained(BERT_PATH)