# Multi-Agent and Multi-Task Experimental Framework

## Overview

This repository contains the experimental code and datasets for multi-agent and multi-task scenarios. It supports the following experiments and modules:

- Main multi-agent routing and workflow experiments
- Ground Truth ablation experiments
- QA dataset construction, rewriting, training, and evaluation
- SQL generation and execution verification
- Time-series forecasting based on Time-MoE
- Stock trend prediction and dataset construction

The project provides an end-to-end experimental pipeline covering data preparation, prompt construction, model inference, SQL verification, time-series forecasting, and evaluation.

---

## Environment Setup

The project dependencies are listed in `requirements.txt`.

Install them using:

```bash
pip install -r requirements.txt
```

It is recommended to create an isolated Python environment before installing the dependencies.

For example:

```bash
conda create -n multi_agent_exp python=3.11
conda activate multi_agent_exp
pip install -r requirements.txt
```

---

## Project Structure

```text
.
├── main_test_agent_all_template.py
├── llm_tranformer_stock_qwen_ground_truth_wf_template.py
├── bert_train_test_template.py
├── query_template.py
├── mian_test_agent_spoken_100_qwen_multi.py
├── template_predict_QA.py
├── replace_rewrite_template.py
├── template_generate_template.py
├── sql_verify_template.py
├── Train-Timemoe_template.ipynb
├── Stock Trend Prediction_template.py
├── train_merged.json
├── val_merged.json
├── test_merged.json
├── requirements.txt
└── Prompt/
    ├── README.md
    ├── direct_pred_prompt_baseline_english.json
    ├── history_sql_prompt_english.json
    └── sql_prompt_english.json
```

> The actual paths of the scripts and datasets should be adjusted according to the repository layout and the path configurations used in the code.

---

## Main Experiment

### Script

```text
main_test_agent_all_template.py
```

### Description

This script serves as the main entry point for the overall multi-agent routing and workflow experiments.

It is responsible for:

- Orchestrating different agents and subtasks
- Loading task-specific prompts and data templates
- Routing samples to the corresponding processing modules
- Calling model inference code
- Integrating the outputs of different modules
- Constructing an end-to-end experimental pipeline

The script can be used to evaluate the overall performance of the multi-agent and multi-task framework.

### Running the Main Experiment

```bash
python main_test_agent_all_template.py
```

Before running the script, ensure that:

1. All required dependencies have been installed.
2. Dataset paths are correctly configured.
3. Prompt files are available in the `Prompt/` directory.
4. Model paths or API configurations are correctly specified.
5. Database configurations are available if SQL-related tasks are enabled.

---

## Ground Truth Ablation Experiment

### Script

```text
llm_tranformer_stock_qwen_ground_truth_wf_template.py
```

### Description

This script implements the Ground Truth-related workflow used in the ablation experiments.

The module is designed to compare:

- Direct LLM prediction
- Ground Truth or structured process-based prediction

It provides a reference structured workflow for stock-related tasks, including:

- Stock quote analysis
- Trend prediction
- Question answering
- Structured intermediate processing
- Ground Truth-based evaluation

The results can be compared with the direct-prediction baseline that uses:

```text
Prompt/direct_pred_prompt_baseline_english.json
```

### Running the Ground Truth Experiment

```bash
python llm_tranformer_stock_qwen_ground_truth_wf_template.py
```

---

## QA-Related Modules

### 1. BERT Fine-Tuning and Evaluation

#### File

```text
bert_train_test_template.py
```

#### Description

This script fine-tunes and evaluates a BERT-based model using the QA datasets.

It supports:

- Loading training, validation, and test datasets
- Tokenizing QA samples
- Fine-tuning a BERT model
- Evaluating the trained model
- Reporting performance on different dataset splits

The following datasets are used:

```text
train_merged.json
val_merged.json
test_merged.json
```

#### Running the Script

```bash
python bert_train_test_template.py
```

---

### 2. QA Query-Type Template

#### File

```text
query_template.py
```

#### Description

This file defines templates for query-type QA datasets.

Its main functions include:

- Constructing question–answer samples for query tasks
- Standardizing query-type inputs and outputs
- Converting raw task data into a model-consumable format
- Supporting downstream training and evaluation

---

### 3. Evaluation on 100 Real Spoken Samples

#### File

```text
mian_test_agent_spoken_100_qwen_multi.py
```

#### Description

This script is used to evaluate the system on 100 real spoken-language samples.

It is responsible for:

- Loading the 100 real spoken samples
- Running the multi-agent or Qwen-based inference workflow
- Collecting the prediction results
- Producing experimental results for spoken-language evaluation

#### Running the Script

```bash
python mian_test_agent_spoken_100_qwen_multi.py
```

> Note: The filename uses `mian` rather than `main`. Use the actual filename when running the script.

---

### 4. QA Prediction-Type Template

#### File

```text
template_predict_QA.py
```

#### Description

This file defines templates for prediction-type QA datasets.

Its main functions include:

- Converting original queries or questions into model-consumable inputs
- Constructing prediction-oriented QA samples
- Generating labels or target fields
- Standardizing the data format for prediction tasks

Typical prediction tasks include:

- Stock trend prediction
- Indicator movement prediction
- Future-value comparison
- Upward or downward trend classification

---

### 5. QA Rewriting Template

#### File

```text
replace_rewrite_template.py
```

#### Description

This script performs question rewriting and paraphrasing for QA data.

It can be used to:

- Generate diverse question formulations
- Replace expressions while preserving the original intent
- Construct paraphrased QA samples
- Improve model robustness to linguistic variation
- Expand the original QA dataset

---

### 6. Unified QA Dataset Generation

#### File

```text
template_generate_template.py
```

#### Description

This script generates unified-format QA datasets for all intents and task types.

Supported task types may include:

- Prediction-type tasks
- Query-type tasks
- SQL-type tasks
- Multi-task QA
- Other intent-based tasks

The script converts heterogeneous task samples into a unified QA or instruction-style schema, facilitating:

- Unified model training
- Multi-task learning
- Consistent evaluation
- Cross-task data management

---

## SQL Query and Verification Module

### File

```text
sql_verify_template.py
```

### Description

This module implements SQL query generation and execution verification.

Its main functions include:

- Receiving natural-language questions
- Generating SQL statements
- Executing generated SQL queries
- Verifying whether the SQL statements are executable
- Checking whether the execution results are correct or usable
- Recording SQL generation and verification results

The module can be used together with the following prompt files:

```text
Prompt/sql_prompt_english.json
Prompt/history_sql_prompt_english.json
```

### Running the SQL Verification Module

```bash
python sql_verify_template.py
```

Before running the script, ensure that the database connection information and required tables are correctly configured.

---

## Time-Series Forecasting and Stock Trend Modules

### 1. Time-MoE Time-Series Forecasting

#### File

```text
Train-Timemoe_template.ipynb
```

#### Description

This notebook implements time-series forecasting experiments based on the Time-MoE model.

It is suitable for modeling and forecasting sequential data such as:

- Market quotations
- Stock prices
- Trading indicators
- Financial time series
- Other temporal indicator sequences

The notebook may cover:

- Data loading and preprocessing
- Time-series sample construction
- Model training or inference
- Future-value forecasting
- Forecast result evaluation

### Running the Notebook

Start Jupyter Notebook or JupyterLab:

```bash
jupyter notebook
```

or:

```bash
jupyter lab
```

Then open:

```text
Train-Timemoe_template.ipynb
```

---

### 2. Stock Trend Prediction Data Construction

#### File

```text
Stock Trend Prediction_template.py
```

#### Description

This script fills and constructs datasets for stock prediction-related intents.

Supported scenarios include:

- Stock trend prediction
- Upward or downward movement classification
- Indicator movement prediction
- Prediction-label construction
- Quote and trend data organization

The script organizes raw quotation data, indicator information, and labels into samples that can be used to train or evaluate prediction models.

### Running the Script

Because the filename contains spaces, use:

```bash
python "Stock Trend Prediction_template.py"
```

---

## QA Dataset Description

The QA datasets consist of three subsets:

| Dataset | File | Description |
|---|---|---|
| Training set | `train_merged.json` | Used for model training or fine-tuning |
| Validation set | `val_merged.json` | Used for validation and model selection |
| Test set | `test_merged.json` | Used for final evaluation |

Together, these files form the complete QA dataset for:

- BERT fine-tuning
- LLM-based task training
- Multi-task learning
- Model evaluation
- Ablation experiments

Before running an experiment, place these files in the data directory expected by the corresponding script or update the dataset paths in the code.

---

## Typical Experimental Workflow

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Prepare the QA Datasets

Prepare the following files:

```text
train_merged.json
val_merged.json
test_merged.json
```

Place them in the paths expected by the corresponding scripts.

### Step 3: Construct or Rewrite QA Data

Use the following scripts according to the target task:

```text
query_template.py
template_predict_QA.py
replace_rewrite_template.py
template_generate_template.py
```

These scripts support query-type QA construction, prediction-type QA construction, question rewriting, and unified dataset generation.

### Step 4: Run BERT Fine-Tuning

```bash
python bert_train_test_template.py
```

### Step 5: Run SQL Generation and Verification

Use:

```text
sql_verify_template.py
```

together with:

```text
Prompt/sql_prompt_english.json
Prompt/history_sql_prompt_english.json
```

Run:

```bash
python sql_verify_template.py
```

### Step 6: Run Time-Series Forecasting

Open and execute:

```text
Train-Timemoe_template.ipynb
```

### Step 7: Construct Stock Trend Prediction Data

```bash
python "Stock Trend Prediction_template.py"
```

### Step 8: Run the Main Multi-Agent Experiment

```bash
python main_test_agent_all_template.py
```

### Step 9: Run the Ground Truth Ablation Experiment

```bash
python llm_tranformer_stock_qwen_ground_truth_wf_template.py
```

Compare the Ground Truth workflow results with the direct LLM prediction baseline based on:

```text
Prompt/direct_pred_prompt_baseline_english.json
```

### Step 10: Evaluate Real Spoken-Language Samples

```bash
python mian_test_agent_spoken_100_qwen_multi.py
```

---

## Prompt Configuration

All prompt configuration files are located in:

```text
Prompt/
```

For detailed descriptions of the prompt files and their intended use, see:

```text
Prompt/README.md
```

---

## Notes

- Check and update all dataset, model, output, and database paths before running the scripts.
- Configure API keys or local model paths when LLM inference is required.
- Configure the database connection before running SQL generation and verification experiments.
- GPU-enabled environments are recommended for BERT fine-tuning, LLM inference, and Time-MoE forecasting.
- Make sure that the CUDA version is compatible with the installed PyTorch version.
- Some filenames preserve their original spelling, such as `mian_test_agent_spoken_100_qwen_multi.py`. Use the actual repository filenames when executing commands.
