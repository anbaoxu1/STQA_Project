Project README
This project contains experimental code and data for multi-agent and multi-task scenarios, including main experiments, ablation experiments (Ground Truth), QA data generation and prediction, SQL query verification, as well as time series forecasting and stock trend prediction modules.

Environment setup
The dependency environment is managed via requirements.txt, please use the following command to install:

bash
pip install -r requirements.txt

Main experiment entry
Main experiment script: main_test_agent_all_template.py

Function: Serves as the main entry point for the overall multi-agent routing / workflow experiments, used to orchestrate various subtasks and template code, and to realize an end-to-end experimental pipeline (such as calling different prompts, data templates, and model inference code).

Ablation experiment: Ground Truth module
Ground Truth script: llm_tranformer_stock_qwen_ground_truth_wf_template.py

Functions:

Implements the Ground Truth-related workflow used in ablation experiments to compare the performance difference between “direct LLM prediction” and “Ground Truth / structured process-based” approaches.

Provides a reference workflow design for stock-related tasks (such as quotes, trends, QA, etc.).

QA-related modules

BERT fine-tuning
File: bert_train_test_template.py

Functions:

Fine-tunes and evaluates a BERT model based on QA datasets.

Supports training and testing on split datasets such as train / validation / test.

QA query-type template
File: query_template.py

Functions:

Defines templates for QA query-type datasets, mainly used for “question–answer” style task modeling.

QA prediction-type template
File: template_predict_QA.py

Functions:

Defines templates for QA prediction-type datasets, mainly used for “question–answer” style prediction tasks.

Converts the original query / question into model-consumable input format and generates corresponding labels or target fields.

QA rewriting template
File: replace_rewrite_template.py

Functions:

Performs question rewriting and paraphrasing for QA data.

Can be used to construct datasets with diverse question formulations to improve model robustness to different expressions.

Code for generating QA dataset templates (all intents)
File: template_generate_template.py

Functions:

Generates unified-format datasets for all intents (multi-task, multi-type QA).

Supports converting different task types (such as prediction-type, query-type, SQL-type, etc.) into a unified QA/instruction-style schema, facilitating unified training or evaluation.

SQL query and verification module
File: sql_verify_template.py

Functions:

Implements the logic for SQL query generation and execution verification.

Used to generate SQL from natural language questions and verify whether the execution results are correct or usable.

Time series forecasting and stock trend modules

Time-MoE time series forecasting
File: Train-Timemoe_template.ipynb

Functions:

Implements time series forecasting experiments based on the Time-MoE model.

Suitable for modeling and forecasting time series data such as market quotes and indicator sequences.

Stock trend prediction data filling
File: Stock Trend Prediction_template.py

Functions:

Fills and constructs datasets for prediction-type intents, for example:

Stock trend prediction

Upward/downward movement judgment for indicators

Organizes raw quotes/label information into samples that can be used to train prediction models.

QA dataset description
The QA datasets in this project mainly consist of three parts:

Training set: train_merged.json

Validation set: val_merged.json

Test set: test_merged.json

These three files together form the complete QA task data, used for BERT fine-tuning, LLM task training, or evaluation scenarios.

Prompt configuration description
Prompt files are located in the Prompt/ directory, with different files corresponding to different experiments and intents:

direct_pred_prompt_baseline_english.json

Usage:

Baseline prompt for direct LLM prediction in ablation experiments.

Does not rely on intermediate structured workflows or auxiliary modules, directly uses the LLM to perform task answering or prediction.

history_sql_prompt_english.json

Usage:

Prompt templates corresponding to “history_sql”-related tasks.

Targeted at SQL generation/query scenarios with historical information (such as constructing SQL based on historical QA or context).

sql_prompt_english.json

Usage:

Prompt templates used for SQL query generation.

Input is a natural language question; output is the corresponding SQL statement, guiding the LLM to generate executable SQL in the required format.

Typical usage workflow (example)

Install dependencies

bash
pip install -r requirements.txt

Prepare data

Place train_merged.json, val_merged.json, and test_merged.json in the specified data directory (corresponding to the code).

QA-related experiments

Use bert_train_test_template.py to fine-tune and evaluate BERT for QA.

Use query_template.py / replace_rewrite_template.py / template_generate_template.py to complete QA data construction and rewriting for different intents.

SQL-related experiments

Use sql_verify_template.py together with sql_prompt_english.json / history_sql_prompt_english.json to conduct SQL generation and verification experiments.

Time series and stock-related experiments

Use Train-Timemoe_template.ipynb for Time-MoE time series forecasting experiments.

Use Stock Trend Prediction_template.py to build stock trend prediction-related datasets and tasks.

Main experiments and ablation experiments

Run the overall multi-agent workflow experiments through main_test_agent_all_template.py.

Use llm_tranformer_stock_qwen_ground_truth_wf_template.py to run Ground Truth ablation experiments and compare with the direct prediction results based on direct_pred_prompt_baseline_english.json.
