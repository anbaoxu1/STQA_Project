template_data = [
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0001",
        "question": "What will be the opening price of {股票名称} on {时间}?",
        "SQL_target": """SELECT open FROM \"{股票名称}\" WHERE date = '{时间}';""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '{时间}' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0002",
        "question": "What will be the opening price of {股票名称} {模糊时间}?",
        "SQL_target": """SELECT open FROM \"{股票名称}\" WHERE CAST(date AS DATE) = '{模糊时间}';""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '{模糊时间}' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0003",
        "question": "What will be the respective opening prices of {股票名称} {时间段2}?",
        "SQL_target": """SELECT open FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days');""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0004",
        "question": "What will be the opening price of {股票名称} {时间段1} after {节日时间}?",
        "SQL_target": """SELECT open FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN (CAST('{节日时间}' AS DATE) + INTERVAL '1 day') AND (CAST('{节日时间}' AS DATE) + INTERVAL '{时间段1} days') AND open IS NOT NULL;""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '{节日时间}' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0005",
        "question": "What will be the highest opening price of {股票名称} {时间段1} after {节日时间}?",
        "SQL_target": """SELECT MAX(open) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN (CAST('{节日时间}' AS DATE) + INTERVAL '1 day') AND (CAST('{节日时间}' AS DATE) + INTERVAL '{时间段1} days') AND open IS NOT NULL;""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '{节日时间}' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0006",
        "question": "What will be the closing price of {股票名称} on {时间}?",
        "SQL_target": """SELECT close FROM \"{股票名称}\" WHERE date = '{时间}';""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '{时间}' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0007",
        "question": "What will be the closing price of {股票名称} {模糊时间}?",
        "SQL_target": """SELECT close FROM \"{股票名称}\" WHERE CAST(date AS DATE) = '{模糊时间}';""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '{模糊时间}' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0008",
        "question": "What will be the respective closing prices of {股票名称} {时间段2}?",
        "SQL_target": """SELECT close FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days');""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0009",
        "question": "What will be the closing price of {股票名称} {时间段1} after {节日时间}?",
        "SQL_target": """SELECT close FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN (CAST('{节日时间}' AS DATE) + INTERVAL '1 day') AND (CAST('{节日时间}' AS DATE) + INTERVAL '{时间段1} days') AND close IS NOT NULL;""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '{节日时间}' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",
        "Template_ID": "0010",
        "question": "What will be the highest closing price of {股票名称} {时间段1} after {节日时间}?",
        "SQL_target": """SELECT MAX(close) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN (CAST('{节日时间}' AS DATE) + INTERVAL '1 day') AND (CAST('{节日时间}' AS DATE) + INTERVAL '{时间段1} days') AND close IS NOT NULL;""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '{节日时间}' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0011",
        "question": "Will the opening price of {股票名称} rise or fall in {时间段1}?",
        "SQL_target": """SELECT CASE WHEN (SELECT open FROM \"{股票名称}\" WHERE CAST(date AS DATE) = CAST('2023-11-24' AS DATE) + INTERVAL '{时间段1} days') > (SELECT open FROM \"{股票名称}\" WHERE CAST(date AS DATE) = CAST('2023-11-24' AS DATE)) THEN 'rise' ELSE 'fall' END AS trend;""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0012",
        "question": "Will the opening price of {股票名称} set a new record {时间段2} relative to last month?",
        "SQL_target": """SELECT CASE WHEN (SELECT MAX(open) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days')) > (SELECT MAX(open) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '30 days') AND CAST('2023-11-24' AS DATE)) THEN 'Yes' ELSE 'No' END AS will_reach_new_high;""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0013",
        "question": "Will the opening price of {股票名称} fall below its lowest value {时间段2} relative to last month?",
        "SQL_target": """SELECT CASE WHEN (SELECT MIN(open) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days')) > (SELECT MIN(open) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '30 days') AND CAST('2023-11-24' AS DATE)) THEN 'Yes' ELSE 'No' END AS will_fall_below_lowest;""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0014",
        "question": "Will the opening price of {股票名称} on {时间} rise or fall relative to today?",
        "SQL_target": """SELECT CASE WHEN t1.open > t2.open THEN 'rise' WHEN t1.open < t2.open THEN 'fall' ELSE 'unchange' END AS result FROM "{股票名称}" t1, "{股票名称}" t2 WHERE t1.date='{时间}' AND t2.date='2023-11-24';""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0015",
        "question": "Will the opening price of {股票名称} {模糊时间} rise or fall relative to today?",
        "SQL_target": """SELECT CASE WHEN t1.open > t2.open THEN 'rise' WHEN t1.open < t2.open THEN 'fall' ELSE 'unchange' END AS result FROM "{股票名称}" t1, "{股票名称}" t2 WHERE t1.date='{模糊时间}' AND t2.date='2023-11-24';""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0016",
        "question": "Will the average opening price of {股票名称} {时间段2} go up or down relative to {时间段3}?",
        "SQL_target": """SELECT CASE WHEN (SELECT AVG(open) FROM "{股票名称}" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days')) > (SELECT AVG(open) FROM "{股票名称}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{时间段3} days') AND CAST('2023-11-24' AS DATE)) THEN 'rise' ELSE 'fall' END AS price_trend;""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Extremum Prediction",
        "Template_ID": "00017",
        "question": "On which day will the opening price of {股票名称} be the highest {时间段2}?",
        "SQL_target": """SELECT date FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days') ORDER BY open DESC LIMIT 1;""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Extremum Prediction",
        "Template_ID": "0018",
        "question": "{时间段4}, on which days will {股票名称} have an opening price exceeding {点数} points?",
        "SQL_target": """SELECT date FROM \"{股票名称}\" WHERE open > {点数} AND CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段4} days');""",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0019",
        "question": "Will the closing price of {股票名称} rise or fall in {时间段1}?",
        "SQL_target": """SELECT CASE WHEN (SELECT close FROM \"{股票名称}\" WHERE CAST(date AS DATE) = CAST('2023-11-24' AS DATE) + INTERVAL '{时间段1} days') > (SELECT close FROM \"{股票名称}\" WHERE CAST(date AS DATE) = CAST('2023-11-24' AS DATE)) THEN 'rise' ELSE 'fall' END AS trend;""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0020",
        "question": "Will the closing price of {股票名称} set a new record {时间段2} relative to last month?",
        "SQL_target": """SELECT CASE WHEN (SELECT MAX(close) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days')) > (SELECT MAX(close) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '30 days') AND CAST('2023-11-24' AS DATE)) THEN 'Yes' ELSE 'No' END AS will_reach_new_high;""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0021",
        "question": "Will the closing price of {股票名称} fall below its lowest value {时间段2} relative to last month?",
        "SQL_target": """SELECT CASE WHEN (SELECT MIN(close) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days')) > (SELECT MIN(close) FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '30 days') AND CAST('2023-11-24' AS DATE)) THEN 'Yes' ELSE 'No' END AS will_fall_below_lowest;""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0022",
        "question": "Will the closing price of {股票名称} on {时间} rise or fall relative to today?",
        "SQL_target": """SELECT CASE WHEN t1.close > t2.close THEN 'rise' WHEN t1.close < t2.close THEN 'fall' ELSE 'unchange' END AS result FROM "{股票名称}" t1, "{股票名称}" t2 WHERE t1.date='{时间}' AND t2.date='2023-11-24';""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0023",
        "question": "Will the closing price of {股票名称} {模糊时间} rise or fall relative to today?",
        "SQL_target": """SELECT CASE WHEN t1.close > t2.close THEN 'rise' WHEN t1.close < t2.close THEN 'fall' ELSE 'unchange' END AS result FROM "{股票名称}" t1, "{股票名称}" t2 WHERE t1.date='{模糊时间}' AND t2.date='2023-11-24';""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",
        "Template_ID": "0024",
        "question": "Will the average closing price of {股票名称} {时间段2} go up or down relative to {时间段3}?",
        "SQL_target": """SELECT CASE WHEN (SELECT AVG(close) FROM "{股票名称}" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days')) > (SELECT AVG(close) FROM "{股票名称}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{时间段3} days') AND CAST('2023-11-24' AS DATE)) THEN 'rise' ELSE 'fall' END AS price_trend;""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Extremum Prediction",
        "Template_ID": "00025",
        "question": "On which day will the closing price of {股票名称} be the highest {时间段2}?",
        "SQL_target": """SELECT date FROM \"{股票名称}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段2} days') ORDER BY close DESC LIMIT 1;""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Extremum Prediction",
        "Template_ID": "0026",
        "question": "{时间段4}, on which days will {股票名称} have an closing price exceeding {点数} points?",
        "SQL_target": """SELECT date FROM \"{股票名称}\" WHERE close > {点数} AND CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{时间段4} days');""",
        "HISTORY_SQL": "SELECT date, close FROM (SELECT date, close FROM \"{股票名称}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    }
]