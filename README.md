# STQA: A Benchmark for Stock-Focused Tabular Question Answering over Historical and Forecasted Data

This work has been accepted for publication in **Findings of EMNLP 2026**.

<img width="2839" height="1013" alt="picture2" src="https://github.com/user-attachments/assets/83130334-3194-483f-847b-d7dd407d1de1" />

This repository contains the dataset and code released for the paper:

**"STQA: A Benchmark for Stock-Focused Tabular Question Answering over Historical and Forecasted Data"**

Stock market analysis inherently requires composite reasoning over historical records and future projections, yet existing benchmarks remain fragmented across isolated tasks. We introduce **STQA (Stock-focused Tabular Question Answering)**, an end-to-end benchmark designed to systematically evaluate natural-language question answering over historical data, numerical forecasts, and forecast-based reasoning.

Built on a large-scale financial dataset, STQA covers **4,417 stocks** and contains **31,400 question–answer pairs** derived from expert-crafted templates, accompanied by fine-grained intent and slot annotations. To operationalize this benchmark, we present **SQFRS (Stock Query–Forecast–Reasoning System)**, an agent-based unified framework that orchestrates SQL retrieval and time-series forecasting tools.

Experiments demonstrate that while current large language models perform well on historical queries, forecast-based reasoning poses a substantial challenge, revealing critical bottlenecks in tool coordination and reasoning under uncertainty.

---

## Requirements and Installation

To reproduce the experimental environment used in the paper, please install the following dependencies:

```text
torch==2.5.1+cu124
numpy==1.26.4
transformers==4.48.2
pandas==2.2.3
ipywidgets==8.1.5
scikit-learn==1.5.2
langchain==0.3.17
langchain-openai==0.2.12
langchain-community==0.3.16
langchain-core==0.3.33
rank-bm25==0.2.2
jieba==0.42.1
psycopg2-binary==2.9.10


## Importing Data

### Create a New Database

First, create a new database. Here, we use a PostgreSQL database deployed in a Docker container. Please ensure that Docker is installed on your system before proceeding.

Run the following command to create the PostgreSQL container:

```bash
docker run -id \
  --name=my-postgresql \
  -v ./data:/var/lib/postgresql/data \
  -p 1213:5432 \
  -e POSTGRES_PASSWORD='123456' \
  -e POSTGRES_USER='***' \
  -e LANG=C.UTF-8 \
  --restart=always \
  postgres:alpine

After the command is executed successfully, the PostgreSQL database will be accessible through port 1213.
Read and Import Tables

## Read and Import Tables

Read all tables located in the `tables` directory and import them into the newly created PostgreSQL database.

You can run the following script to complete the database setup:

```bash
python Code/Input_to_POSTGRE.py
```

Before running the script, make sure to update the PostgreSQL username and password in the script so that they match the credentials configured when creating the Docker container.

---

## Repository Contents

The repository includes:

- The **STQA dataset** in JSON format
- The **source code for the SQFRS framework**
- **Pre-trained STQA model checkpoints**
- Detailed instructions for **dataset usage, model training, and evaluation**

This resource is designed to advance research on question answering in the stock domain by systematically evaluating natural-language question answering capabilities across three major task categories:

- **Historical data query reasoning**
- **Numerical forecasting**
- **Forecast-based reasoning**

We hope that STQA will serve as a valuable benchmark and resource for the research community.

---

## Contact Us

If you have any questions regarding the project code or dataset, please feel free to contact us at:

**Email:** `anbaoxu@mail.bnu.edu.cn`

You are also welcome to open an issue in this repository.


