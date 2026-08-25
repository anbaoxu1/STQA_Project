# STQA Dataset

## Overview

STQA is a stock question answering dataset containing **31,400 QA instances**. Following the dataset setting described in the paper, the full dataset is divided into training, validation, and test sets using a **7:2:1** ratio:

| Split | Number of Instances | Ratio |
|---|---:|---:|
| Training (`train_merged.json`) | 21,980 | 70% |
| Validation | 6,280 | 20% |
| Test | 3,140 | 10% |
| **Total** | **31,400** | **100%** |

The dataset contains three task categories:

| Task Type | Number of QA Pairs | Description |
|---|---:|---|
| Query Reasoning | 10,500 | Answers questions by retrieving and reasoning over historical stock data. |
| Numerical Forecasting | 10,400 | Predicts future numerical stock values such as opening or closing prices. |
| Forecast-based Reasoning | 10,500 | Performs reasoning over predicted future stock values, such as trend comparison, extrema identification, or threshold-based reasoning. |
| **Total** | **31,400** | |

As stated in the paper:

> The 31,400 instances are split into training, validation, and test sets at a 7:2:1 ratio, yielding 21,980, 6,280, and 3,140 instances, respectively. By task type, STQA includes 10,500 query reasoning QA pairs, 10,400 numerical forecasting QA pairs, and 10,500 forecast-based reasoning QA pairs.

---

## Dataset Files

The training set is stored in:

```text
train_merged.json
```

It contains **21,980 instances** and follows the same JSON schema and annotation format as the validation and test sets.

Each dataset file is a JSON array, where every element corresponds to one QA instance.

---

## Data Format

A typical instance has the following structure:

```json
{
  "Sample_ID": "00001",
  "stock_name": "OLLI",
  "sql_statement": "SELECT open FROM \"OLLI\" WHERE CAST(date AS DATE) = '2020-01-06';",
  "question": "What was the opening price of OLLI on 2020-01-06?",
  "answer": [[60.61]],
  "bio_annotation": "O O O O O O B-stock_name I-stock_name I-stock_name O B-year O B-month O B-day O",
  "slots": [
    "stock_name: OLLI",
    "year: 2020",
    "month: 01",
    "day: 06"
  ],
  "Intent": "Opening Price Inquiry",
  "bert_split": "What was the opening price of O ##LL ##I on 2020 - 01 - 06 ?"
}
```

Forecast-related instances may additionally contain historical stock sequences:

```json
{
  "history_sql": "SELECT date, close FROM ...",
  "history_answer": [
    ["2023-09-15", 20.98],
    ["2023-09-18", 21.09],
    ["2023-09-19", 21.01]
  ]
}
```

---

## Field Description

| Field | Type | Description |
|---|---|---|
| `Sample_ID` | String | Unique identifier of the QA instance. |
| `stock_name` | String | Stock ticker involved in the question. |
| `sql_statement` | String | SQL statement associated with the target answer. |
| `question` | String | Natural-language stock question. |
| `answer` | List / String | Ground-truth answer. It may be a nested list containing numerical values, dates, or categorical results, or a special string such as `Trading Halt`. |
| `bio_annotation` | String | Token-level BIO sequence-label annotation for semantic slot extraction. |
| `slots` | List[String] | Structured slot-value annotations extracted from the question. |
| `Intent` | String | Intent label describing the semantic objective of the question. |
| `bert_split` | String | BERT WordPiece tokenization of the question used for sequence labeling. |
| `history_sql` | String, optional | SQL query used to retrieve the historical time-series context required by forecasting-related questions. |
| `history_answer` | List, optional | Historical stock time series returned by `history_sql`, typically represented as `[date, value]` pairs. |

`history_sql` and `history_answer` are primarily used by **Numerical Forecasting** and **Forecast-based Reasoning** instances and may be absent from pure historical query-reasoning samples.

---

## Task Categories

### 1. Query Reasoning

Query Reasoning questions are answered using historical stock information and do not require future stock-price prediction.

Example:

```text
Question:
What was the opening price of OLLI on 2020-01-06?

Intent:
Opening Price Inquiry

Answer:
60.61
```

Typical operations include historical value lookup, date-conditioned retrieval, and reasoning over retrieved stock records.

### 2. Numerical Forecasting

Numerical Forecasting questions require prediction of future numerical stock values.

Typical targets include future:

- opening prices;
- closing prices;
- other numerical stock indicators defined by the dataset.

Historical time-series observations are provided through `history_sql` and `history_answer` when required.

### 3. Forecast-based Reasoning

Forecast-based Reasoning questions require one or more future stock values to be predicted first and then used for downstream reasoning.

Examples include:

- determining whether a future price will **rise**, **fall**, or **remain unchanged**;
- finding the date with the **highest** or **lowest** predicted price;
- identifying dates on which a predicted value is above or below a threshold;
- comparing future prices with the current or historical price.

Example:

```text
Question:
Compared with today’s closing price, will EMIF’s closing price on
2023-11-27 rise, fall, or remain unchanged?

Intent:
Closing Price Trend Prediction

Answer:
fall
```

---

## Semantic Annotations

Each QA instance contains three complementary forms of semantic annotation:

1. **Intent annotation**
2. **Slot-value annotation**
3. **BIO sequence annotation**

These annotations can be used for spoken/natural-language understanding, intent classification, slot filling, and downstream workflow routing.

### Intent Labels

The `Intent` field specifies the semantic objective of each question.

Intent labels observed in the provided dataset examples include:

```text
Opening Price Inquiry
Closing Price Trend Prediction
Closing Price Extremum Prediction
Opening Price Trend Prediction
```

The complete set of intent labels should be obtained directly from all instances in the dataset rather than inferred from this README excerpt.

### Slot Labels

The `slots` field stores semantic slot-value pairs.

Slot types observed in the provided examples include:

```text
stock_name
year
month
day
time
point
```

Examples:

```json
[
  "stock_name: PWFL",
  "time: half a month ago"
]
```

and

```json
[
  "stock_name: ESTA",
  "time: in the next three days"
]
```

### BIO Labels

The `bio_annotation` field provides token-level BIO annotations aligned with the tokenized question representation.

BIO labels observed in the provided examples include:

```text
O
B-stock_name
I-stock_name
B-time
I-time
B-year
I-year
B-month
B-day
```

where:

- `B-*` denotes the beginning of a semantic slot;
- `I-*` denotes a continuation token belonging to the same slot;
- `O` denotes a token outside any annotated slot.

Because `bert_split` uses WordPiece tokenization, a stock ticker may be divided into several subword tokens. For example:

```text
OLLI -> O ##LL ##I
```

Corresponding BIO labels can therefore span multiple WordPiece tokens:

```text
B-stock_name I-stock_name I-stock_name
```

For experiments requiring the **complete label vocabulary**, labels should be extracted programmatically from the full training, validation, and test files rather than treating the labels shown above as exhaustive.

---

## Answer Formats

Different task types can produce different answer formats.

### Numerical answer

```json
[
  [60.61]
]
```

### Categorical answer

```json
[
  ["rise"]
]
```

### Date answer

```json
[
  ["2023-11-24"]
]
```

### Special state

```json
"Trading Halt"
```

Evaluation code should therefore handle both nested-list answers and special string-valued answers.

---

## Historical Time-Series Context

Forecasting-related instances may include a historical context window in `history_answer`.

Example:

```json
"history_answer": [
  ["2023-11-20", 21.14],
  ["2023-11-21", 20.83],
  ["2023-11-22", 20.78]
]
```

The corresponding `history_sql` records how this historical sequence was retrieved.

This design separates:

```text
Natural-language question
        ↓
Semantic annotations
        ↓
Historical data retrieval
        ↓
Forecasting / reasoning
        ↓
Final answer
```

and supports both direct historical queries and forecast-dependent reasoning within a unified dataset format.

---

## Dataset Statistics

```text
Total instances:                 31,400

Training set:                    21,980
Validation set:                   6,280
Test set:                         3,140

Query Reasoning:                 10,500
Numerical Forecasting:           10,400
Forecast-based Reasoning:        10,500
```

The split statistics and task statistics describe two different dimensions of STQA:

- **Dataset split** specifies whether an instance belongs to training, validation, or testing.
- **Task type** specifies the reasoning capability required by the instance.

---

## Notes

- `train_merged.json` contains **21,980** training instances.
- Training, validation, and test data use the same basic annotation schema.
- `history_sql` and `history_answer` are optional because historical-query instances do not necessarily require a forecasting history window.
- Relative temporal expressions such as `half a month ago`, `15 days from now`, `one week`, and `in the next three days` are represented using the `time` slot.
- Absolute dates can be represented using `year`, `month`, and `day` slots.
- Stock tickers are represented using the `stock_name` slot.
- Numerical thresholds can be represented using the `point` slot.
- The complete intent and BIO label sets should be extracted from the released dataset files to avoid assuming that labels visible in a small example are exhaustive.

