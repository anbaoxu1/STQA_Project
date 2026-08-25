
template_data = [
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0001",
        "Opening Price Inquiry": "What was the opening price of {stock_name} on {time}?",
        "SQL": """SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{time}';""",
        "ANSWER": "The opening price is {opening_price}",
        "HISTORY_SQL": "SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{time}';",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0002",
        "Opening Price Inquiry": "What was the opening price of {stock_name} {vague_time}?",
        "SQL": """SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{vague_time}';""",
        "ANSWER": "The opening price of last week is {opening_price}.",
        "HISTORY_SQL": """SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{vague_time}';""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0003",
        "Opening Price Inquiry": "What has been the highest opening price of {stock_name} {time_period1}?",
        "SQL": """SELECT MAX(open) AS maximum_opening_price FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "ANSWER": "The highest stock price is {opening_price}.",
        "HISTORY_SQL": """SELECT date,open FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The maximum opening price is {maximum_opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0004",
        "Opening Price Inquiry": "How many days have the opening prices of {stock_name} exceeded the average value {time_period1}?",
        "SQL": """SELECT COUNT(*) FROM "{stock_name}" WHERE open > (SELECT AVG(open) FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} DAYS') AND CAST('2023-11-24' AS DATE)) AND CAST(date AS DATE) > (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} DAYS') AND CAST(date AS DATE) < CAST('2023-11-24' AS DATE);""",
        "ANSWER": "The opening prices are {opening_price1} and {opening_price2} respectively",
        "HISTORY_SQL": """SELECT date,open FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The average price is {average_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0005",
        "Opening Price Inquiry": "On which day did the opening price of {stock_name} exceed the average value {time_period1} ?",
        "SQL": """SELECT date FROM "{stock_name}" WHERE open > (SELECT AVG(open) FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} DAYS') AND CAST('2023-11-24' AS DATE)) AND CAST(date AS DATE) > (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} DAYS') AND CAST(date AS DATE) < CAST('2023-11-24' AS DATE);""",
        "ANSWER": "The lowest opening price last week was on {date}.",
        "HISTORY_SQL": """SELECT date,open FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The average price is {average_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0006",
        "Opening Price Inquiry": "What was the opening price of {stock_name} {time_period2} before {holiday_time}?",
        "SQL": """SELECT date,open FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE -  INTERVAL '{time_period2} DAYS') AND '{holiday_time}'::DATE;""",
        "ANSWER": "The opening prices are {opening_price} respectively.",
        "HISTORY_SQL": """SELECT date,open FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE -  INTERVAL '{time_period2} DAYS') AND '{holiday_time}'::DATE;""",
        "HISTORY_ANSWER": "The opening prices are {opening_price} respectively"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0007",
        "Opening Price Inquiry": "What has been the lowest opening price of {stock_name} {time_period1}?",
        "SQL": """SELECT MIN(open) AS minimum_opening_price FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "ANSWER": "The highest stock price is {opening_price}.",
        "HISTORY_SQL": """SELECT date,open FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The minimum opening price is {minimum_opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0008",
        "Opening Price Inquiry": "Did the opening price of {stock_name} rise or fall from {time2} to {time1}?",
        "SQL": """SELECT CASE WHEN t2.open < t1.open THEN 'Rise' WHEN t2.open > t1.open THEN 'Fall' ELSE 'Unchanged' END AS trend FROM (SELECT open FROM "{stock_name}" WHERE CAST(date AS DATE) = '{time1}') t1, (SELECT open FROM "{stock_name}" WHERE CAST(date AS DATE) = '{time2}') t2 WHERE t1.open IS NOT NULL AND t2.open IS NOT NULL;""",
        "ANSWER": "The opening price difference is {opening_price}",
        "HISTORY_SQL": """SELECT date, open FROM "{stock_name}" WHERE CAST(date AS DATE) IN ('{time1}', '{time2}');""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0009",
        "Opening Price Inquiry": "Which is higher, the opening price of {stock_name} {vague_time} or its opening price today?",
        "SQL": """SELECT CASE WHEN (SELECT open FROM "{stock_name}" WHERE CAST(date AS DATE) = '{vague_time}'::DATE LIMIT 1) > (SELECT open FROM "{stock_name}" WHERE CAST(date AS DATE) = '2023-11-24'::DATE LIMIT 1) THEN '{vague_time}' WHEN (SELECT open FROM "{stock_name}" WHERE CAST(date AS DATE) = '{vague_time}'::DATE LIMIT 1) < (SELECT open FROM "{stock_name}" WHERE CAST(date AS DATE) = '2023-11-24'::DATE LIMIT 1) THEN '2023-11-24' ELSE 'equal' END AS higher_price_date;""",
        "ANSWER": "The opening price difference is {opening_price}",
        "HISTORY_SQL": """SELECT past.date, past.open, today.date, today.open FROM LATERAL (SELECT date, open FROM "{stock_name}" WHERE CAST(date AS DATE) = '{vague_time}'::DATE LIMIT 1) past, LATERAL (SELECT date, open FROM "{stock_name}" WHERE CAST(date AS DATE) = '2023-11-24'::DATE LIMIT 1) today;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0010",
        "Opening Price Inquiry": "Which day had the highest opening prices for {stock_name} {time_period1}?",
        "SQL": """SELECT date FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE) ORDER BY open DESC LIMIT 1;""",
        "ANSWER": "The highest opening price within {time_period1} was on {date}.",
        "HISTORY_SQL": """SELECT date,open FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0011",
        "Opening Price Inquiry": "Which stock, {stock_name1} or {stock_name2}, had the fastest growth in opening price {time_period2} before {holiday_time}?",
        "SQL": """SELECT CASE WHEN cur1 IS NULL OR past1 IS NULL OR cur2 IS NULL OR past2 IS NULL OR past1 = 0 OR past2 = 0 THEN 'Trading Halt' WHEN ((cur1 - past1) / past1) > ((cur2 - past2) / past2) THEN '{stock_name1}' ELSE '{stock_name2}' END AS result FROM (SELECT (SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE) AS cur1, (SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS past1, (SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE) AS cur2, (SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS past2) t1;""",
        "ANSWER": "{stock_name} had the fastest opening price growth",
        "HISTORY_SQL": """SELECT '{stock_name1}' AS stock_name1, date, open FROM "{stock_name1}" WHERE CAST(date AS DATE) IN (('{holiday_time}'::DATE - INTERVAL '{time_period2} days'), '{holiday_time}'::DATE) UNION ALL SELECT '{stock_name2}' AS stock_name2,date, open FROM "{stock_name2}" WHERE CAST(date AS DATE) IN (('{holiday_time}'::DATE - INTERVAL '{time_period2} days'), '{holiday_time}'::DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0012",
        "Opening Price Inquiry": "What was the opening price return of {stock_name} {time_period2} before {holiday_time}",
        "SQL": """SELECT ((SELECT open FROM "{stock_name}" WHERE date::DATE = '{holiday_time}'::DATE)-(SELECT open FROM "{stock_name}" WHERE date::DATE = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')))/(SELECT open FROM "{stock_name}" WHERE date::DATE = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS Opening_Price_Return;""",
        "ANSWER": "The opening price the day before yesterday is {opening_price}.",
        "HISTORY_SQL": """SELECT date, open FROM "{stock_name}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') UNION ALL SELECT date, open FROM "{stock_name}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0013",
        "Opening Price Inquiry": "What were the opening price return rates of {stock_name1} and {stock_name2} {time_period2} before {holiday_time}?",
        "SQL": """SELECT '{stock_name1}' AS stock_name, ((SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE) - (SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days'))) / (SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS opening_price_return_rate UNION ALL SELECT '{stock_name2}' AS stock_name, ((SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE) - (SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days'))) / (SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS opening_price_return_rate;""",
        "ANSWER": "The minimum opening price of last week is {opening_price}.",
        "HISTORY_SQL": """SELECT '{stock_name1}' AS stock_name, date, open FROM "{stock_name1}" WHERE CAST(date AS DATE) IN (('{holiday_time}'::DATE - INTERVAL '{time_period2} days'), '{holiday_time}'::DATE) UNION ALL SELECT '{stock_name2}' AS stock_name, date, open FROM "{stock_name2}" WHERE CAST(date AS DATE) IN (('{holiday_time}'::DATE - INTERVAL '{time_period2} days'), '{holiday_time}'::DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0014",
        "Opening Price Inquiry": "What was the opening return rate of {stock_name} from {time1} to {time2}?",
        "SQL": """SELECT ((open2 - open1) / open1) * 100 AS return_rate_percent FROM (SELECT MAX(CASE WHEN CAST(date AS DATE) = '{time1}' THEN open END) AS open1, MAX(CASE WHEN CAST(date AS DATE) = '{time2}' THEN open END) AS open2 FROM "{stock_name}" WHERE CAST(date AS DATE) IN ('{time1}', '{time2}')) AS t WHERE open1 IS NOT NULL AND open2 IS NOT NULL;""",
        "ANSWER": "The opening price difference is {opening_price}",
        "HISTORY_SQL": """SELECT t1.date AS date1, t1.open AS open1, t2.date AS date2, t2.open AS open2 FROM (SELECT date, open FROM "{stock_name}" WHERE CAST(date AS DATE) = '{time1}' LIMIT 1) t1, (SELECT date, open FROM "{stock_name}" WHERE CAST(date AS DATE) = '{time2}' LIMIT 1) t2;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0015",
        "Opening Price Inquiry": "What were the opening prices of {stock_name1} and {stock_name2} {time_period2} before {holiday_time}?",
        "SQL": """SELECT date, open, '{stock_name1}' AS stock_name FROM "{stock_name1}" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') AND '{holiday_time}'::DATE UNION ALL SELECT date, open, '{stock_name2}' AS stock_name FROM "{stock_name2}" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') AND '{holiday_time}'::DATE;""",
        "ANSWER": "The maximum opening price of last week is {opening_price}.",
        "HISTORY_SQL": """SELECT date, open, '{stock_name1}' AS stock_name FROM "{stock_name1}" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') AND '{holiday_time}'::DATE UNION ALL SELECT date, open, '{stock_name2}' AS stock_name FROM "{stock_name2}" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') AND '{holiday_time}'::DATE;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0016",
        "Opening Price Inquiry": "What were the opening prices of {stock_name1} and {stock_name2} {vague_time}?",
        "SQL": """SELECT '{stock_name1}' AS StockName1, (SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{vague_time}' LIMIT 1) AS OpenPrice1, '{stock_name2}' AS StockName2, (SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{vague_time}' LIMIT 1) AS OpenPrice2;""",
        "ANSWER": "The opening prices of {stock_name1} and {stock_name2} are {opening_price1} and {opening_price2} respectively.",
        "HISTORY_SQL": """SELECT '{stock_name1}' AS StockName1, (SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{vague_time}' LIMIT 1) AS OpenPrice1, '{stock_name2}' AS StockName2, (SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{vague_time}' LIMIT 1) AS OpenPrice2;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0017",
        "Opening Price Inquiry": "What were the opening prices of {stock_name1} and {stock_name2} on {time}?",
        "SQL": """SELECT '{stock_name1}' AS StockName1, (SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{time}' LIMIT 1) AS OpenPrice1, '{stock_name2}' AS StockName2, (SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{time}' LIMIT 1) AS OpenPrice2;""",
        "ANSWER": "The values of {stock_name1} and {stock_name2} at {time} are {opening_price1} and {opening_price2} respectively.",
        "HISTORY_SQL": """SELECT '{stock_name1}' AS StockName1, (SELECT open FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{time}' LIMIT 1) AS OpenPrice1, '{stock_name2}' AS StockName2, (SELECT open FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{time}' LIMIT 1) AS OpenPrice2;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Opening Price Inquiry",
        "Template_ID": "0018",
        "Opening Price Inquiry": "What were the opening prices of {stock_name} on {time1} and {time2}?",
        "SQL": """SELECT date,open FROM \"{stock_name}\" WHERE date IN ('{time1}', '{time2}');""",
        "ANSWER": "The prices are {opening_price1} and {opening_price2} respectively.",
        "HISTORY_SQL": """SELECT date,open FROM \"{stock_name}\" WHERE date IN ('{time1}', '{time2}');""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    # Closing price direct query
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0019",
        "Stock Trading Volume Inquiry": "What was the closing price of {stock_name} on {time}?",
        "SQL": """SELECT close FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{time}';""",
        "ANSWER": "The opening price gain rate of last month is {opening_price}.",
        "HISTORY_SQL": """SELECT close FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{time}';""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0020",
        "Stock Trading Volume Inquiry": "What was the closing price of {stock_name} {vague_time}?",
        "SQL": """SELECT close FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{vague_time}';""",
        "ANSWER": "The date with higher price than today is {date}.",
        "HISTORY_SQL": """SELECT close FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{vague_time}';""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0021",
        "Stock Trading Volume Inquiry": "What has been the highest closing price of {stock_name} {time_period1} ?",
        "SQL": """SELECT MAX(close) AS maximum_closing_price FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "ANSWER": "The maximum closing price is {closing_price}",
        "HISTORY_SQL": """SELECT date,close FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0022",
        "Stock Trading Volume Inquiry": "How many days have the closing price of {stock_name} exceeded the average value {time_period1}?",
        "SQL": """SELECT COUNT(*) FROM "{stock_name}" WHERE close > (SELECT AVG(close) FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} DAYS') AND CAST('2023-11-24' AS DATE)) AND CAST(date AS DATE) > (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} DAYS') AND CAST(date AS DATE) < CAST('2023-11-24' AS DATE);""",
        "ANSWER": "The closing price is {closing_price}.",
        "HISTORY_SQL": """SELECT date,close FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0023",
        "Stock Trading Volume Inquiry": "On which day did the closing price of {stock_name} exceed the average value {time_period1} ?",
        "SQL": """SELECT date FROM "{stock_name}" WHERE close > (SELECT AVG(close) FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} DAYS') AND CAST('2023-11-24' AS DATE)) AND CAST(date AS DATE) > (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} DAYS') AND CAST(date AS DATE) < CAST('2023-11-24' AS DATE);""",
        "ANSWER": "Today's closing price is {closing_price}",
        "HISTORY_SQL": """SELECT date,close FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0024",
        "Stock Trading Volume Inquiry": "What was the closing price of {stock_name} {time_period2} before {holiday_time}?",
        "SQL": """SELECT date,close FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE -  INTERVAL '{time_period2} DAYS') AND '{holiday_time}'::DATE;""",
        "ANSWER": "The highest stock price is {closing_price}.",
        "HISTORY_SQL": """SELECT date,close FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE -  INTERVAL '{time_period2} DAYS') AND '{holiday_time}'::DATE;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0025",
        "Stock Trading Volume Inquiry": "What has been the lowest closing price of {stock_name} {time_period1}?",
        "SQL": """SELECT MIN(close) AS minimum_closing_price FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "ANSWER": "The highest stock price is {opening_price}.",
        "HISTORY_SQL": """SELECT date,close FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The minimum opening price is {minimum_opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0026",
        "Stock Trading Volume Inquiry": "Did the closing price of {stock_name} rise or fall from {time1} to {time2}?",
        "SQL": """SELECT CASE WHEN t2.close < t1.close THEN 'Rise' WHEN t2.close > t1.close THEN 'Fall' ELSE 'Unchanged' END AS trend FROM (SELECT close FROM "{stock_name}" WHERE CAST(date AS DATE) = '{time1}') t1, (SELECT close FROM "{stock_name}" WHERE CAST(date AS DATE) = '{time2}') t2 WHERE t1.close IS NOT NULL AND t2.close IS NOT NULL;""",
        "ANSWER": "The closing price difference is {opening_price}",
        "HISTORY_SQL": """SELECT date, close FROM "{stock_name}" WHERE CAST(date AS DATE) IN ('{time1}', '{time2}');""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0027",
        "Stock Trading Volume Inquiry": "Which is higher, the closing price of {stock_name} {vague_time} or its closing price today?",
        "SQL": """SELECT CASE WHEN (SELECT close FROM "{stock_name}" WHERE CAST(date AS DATE) = '{vague_time}'::DATE LIMIT 1) > (SELECT close FROM "{stock_name}" WHERE CAST(date AS DATE) = '2023-11-24'::DATE LIMIT 1) THEN '{vague_time}' WHEN (SELECT close FROM "{stock_name}" WHERE CAST(date AS DATE) = '{vague_time}'::DATE LIMIT 1) < (SELECT close FROM "{stock_name}" WHERE CAST(date AS DATE) = '2023-11-24'::DATE LIMIT 1) THEN '2023-11-24' ELSE 'equal' END AS higher_price_date;""",
        "ANSWER": "The closing price difference is {opening_price}",
        "HISTORY_SQL": """SELECT past.date, past.close, today.date, today.close FROM LATERAL (SELECT date, close FROM "{stock_name}" WHERE CAST(date AS DATE) = '{vague_time}'::DATE LIMIT 1) past, LATERAL (SELECT date, close FROM "{stock_name}" WHERE CAST(date AS DATE) = '2023-11-24'::DATE LIMIT 1) today;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0028",
        "Stock Trading Volume Inquiry": "Which day had the highest closing price of {stock_name} {time_period1}?",
        "SQL": """SELECT date FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE) ORDER BY close DESC LIMIT 1;""",
        "ANSWER": "Yesterday's closing price is {closing_price}.",
        "HISTORY_SQL": """SELECT date,close FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN ('2023-11-24'::DATE -  INTERVAL '{time_period1} DAYS') AND '2023-11-24'::DATE ORDER BY close DESC LIMIT 1;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0029",
        "Stock Trading Volume Inquiry": "Which stock, {stock_name1} or {stock_name2}, had the fastest growth in closing price {time_period2} before {holiday_time}?",
        "SQL": """SELECT CASE WHEN cur1 IS NULL OR past1 IS NULL OR cur2 IS NULL OR past2 IS NULL OR past1 = 0 OR past2 = 0 THEN 'Trading Halt' WHEN ((cur1 - past1) / past1) > ((cur2 - past2) / past2) THEN '{stock_name1}' ELSE '{stock_name2}' END AS result FROM (SELECT (SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE) AS cur1, (SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS past1, (SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE) AS cur2, (SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS past2) t1;""",
        "ANSWER": "The closing price of last week is {closing_price}.",
        "HISTORY_SQL": """SELECT '{stock_name1}' AS stock_name, date, close FROM "{stock_name1}" WHERE CAST(date AS DATE) IN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days', '{holiday_time}'::DATE) UNION ALL SELECT '{stock_name2}' AS stock_name, date, close FROM "{stock_name2}" WHERE CAST(date AS DATE) IN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days', '{holiday_time}'::DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0030",
        "Stock Trading Volume Inquiry": "What was the closing price return of {stock_name} {time_period2} before {holiday_time}?",
        "SQL": """SELECT ((SELECT close FROM "{stock_name}" WHERE date::DATE = '{holiday_time}'::DATE)-(SELECT close FROM "{stock_name}" WHERE date::DATE = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')))/(SELECT close FROM "{stock_name}" WHERE date::DATE = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS Closing_Price_Return;""",
        "ANSWER": "The lowest stock price is {closing_price}.",
        "HISTORY_SQL": """SELECT date, close FROM "{stock_name}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') UNION ALL SELECT date, close FROM "{stock_name}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0031",
        "Stock Trading Volume Inquiry": "What were the closing price return rates of {stock_name1} and {stock_name2} {time_period2} before {holiday_time}?",
        "SQL": """SELECT '{stock_name1}' AS stock_name, ((SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE) - (SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days'))) / (SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS closing_price_return_rate UNION ALL SELECT '{stock_name2}' AS stock_name, ((SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{holiday_time}'::DATE) - (SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days'))) / (SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = ('{holiday_time}'::DATE - INTERVAL '{time_period2} days')) AS closing_price_return_rate;""",
        "ANSWER": "The highest closing price last week was on {date}.",
        "HISTORY_SQL": """SELECT '{stock_name1}' AS stock_name, date, close FROM "{stock_name1}" WHERE CAST(date AS DATE) IN (('{holiday_time}'::DATE - INTERVAL '{time_period2} days'), '{holiday_time}'::DATE) UNION ALL SELECT '{stock_name2}' AS stock_name, date, close FROM "{stock_name2}" WHERE CAST(date AS DATE) IN (('{holiday_time}'::DATE - INTERVAL '{time_period2} days'), '{holiday_time}'::DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0032",
        "Stock Trading Volume Inquiry": "What was the closing return rate of {stock_name} from {time1} to {time2}?",
        "SQL": """SELECT ((close2 - close1) / close1) * 100 AS return_rate_percent FROM (SELECT MAX(CASE WHEN CAST(date AS DATE) = '{time1}' THEN close END) AS close1, MAX(CASE WHEN CAST(date AS DATE) = '{time2}' THEN close END) AS close2 FROM "{stock_name}" WHERE CAST(date AS DATE) IN ('{time1}', '{time2}')) AS t WHERE close1 IS NOT NULL AND close2 IS NOT NULL;""",
        "ANSWER": "The prices are {closing_price1} and {closing_price2} respectively.",
        "HISTORY_SQL": """SELECT t1.date AS date1, t1.close AS close1, t2.date AS date2, t2.close AS close2 FROM (SELECT date, close FROM "{stock_name}" WHERE CAST(date AS DATE) = '{time1}' LIMIT 1) t1, (SELECT date, close FROM "{stock_name}" WHERE CAST(date AS DATE) = '{time2}' LIMIT 1) t2;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0033",
        "Stock Trading Volume Inquiry": "What were the closing prices of {stock_name1} and {stock_name2} {time_period2} before {holiday_time}?",
        "SQL": """SELECT date, close, '{stock_name1}' AS stock_name FROM "{stock_name1}" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') AND '{holiday_time}'::DATE UNION ALL SELECT date, close, '{stock_name2}' AS stock_name FROM "{stock_name2}" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') AND '{holiday_time}'::DATE;""",
        "ANSWER": "The maximum closing price of last month is {closing_price}.",
        "HISTORY_SQL": """SELECT date, close, '{stock_name1}' AS stock_name FROM "{stock_name1}" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') AND '{holiday_time}'::DATE UNION ALL SELECT date, close, '{stock_name2}' AS stock_name FROM "{stock_name2}" WHERE CAST(date AS DATE) BETWEEN ('{holiday_time}'::DATE - INTERVAL '{time_period2} days') AND '{holiday_time}'::DATE;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0034",
        "Stock Trading Volume Inquiry": "What were the closing prices of {stock_name1} and {stock_name2} {vague_time}?",
        "SQL": """SELECT '{stock_name1}' AS StockName1, (SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{vague_time}' LIMIT 1) AS ClosePrice1, '{stock_name2}' AS StockName2, (SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{vague_time}' LIMIT 1) AS ClosePrice2;""",
        "ANSWER": "The closing price is {closing_price}",
        "HISTORY_SQL": """SELECT '{stock_name1}' AS StockName1, (SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{vague_time}' LIMIT 1) AS ClosePrice1, '{stock_name2}' AS StockName2, (SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{vague_time}' LIMIT 1) AS ClosePrice2;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0035",
        "Stock Trading Volume Inquiry": "What were the closing prices of {stock_name1} and {stock_name2} on {time}?",
        "SQL": """SELECT '{stock_name1}' AS StockName1, (SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{time}' LIMIT 1) AS ClosePrice1, '{stock_name2}' AS StockName2, (SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{time}' LIMIT 1) AS ClosePrice2;""",
        "ANSWER": "The closing prices are {closing_price1} and {closing_price2} respectively",
        "HISTORY_SQL": """SELECT '{stock_name1}' AS StockName1, (SELECT close FROM "{stock_name1}" WHERE CAST(date AS DATE) = '{time}' LIMIT 1) AS ClosePrice1, '{stock_name2}' AS StockName2, (SELECT close FROM "{stock_name2}" WHERE CAST(date AS DATE) = '{time}' LIMIT 1) AS ClosePrice2;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Closing Price Inquiry",
        "Template_ID": "0036",
        "Stock Trading Volume Inquiry": "What were the closing prices for {stock_name} on {time1} and {time2}?",
        "SQL": """SELECT date,close FROM \"{stock_name}\" WHERE date IN ('{time1}', '{time2}');""",
        "ANSWER": "The lowest closing price last week was on {date}.",
        "HISTORY_SQL": """SELECT date,close FROM \"{stock_name}\" WHERE date IN ('{time1}', '{time2}');""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    # Stock trading volume query
    {
        "Intent": "Stock Trading Volume Inquiry",
        "Template_ID": "0037",
        "Stock Trading Volume Inquiry": "What was the trading volume of {stock_name} on {time}?",
        "SQL": """SELECT volume FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{time}';""",
        "ANSWER": "The trading volume is {volume}",
        "HISTORY_SQL": """SELECT date,volume FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{time}';""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Stock Trading Volume Inquiry",
        "Template_ID": "0038",
        "Stock Trading Volume Inquiry": "What was the trading volume of {stock_name} {vague_time}?",
        "SQL": """SELECT volume FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{vague_time}';""",
        "ANSWER": "Today's trading volume is {volume}.",
        "HISTORY_SQL": """SELECT date,volume FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{vague_time}';""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Stock Trading Volume Inquiry",
        "Template_ID": "0039",
        "Stock Trading Volume Inquiry": "What was the maximum trading volume of {stock_name} {time_period2} before {holiday_time}?",
        "SQL": """SELECT MAX(volume) AS maximum_trading_volume FROM \"{stock_name}\" WHERE CAST(date AS DATE) < '{holiday_time}' AND CAST(date AS DATE) >= (DATE '{holiday_time}' - INTERVAL '{time_period2} DAYS');""",
        "ANSWER": "The stock trading volume is {volume}.",
        "HISTORY_SQL": """SELECT date,volume FROM "{stock_name}" WHERE CAST(date AS DATE) < '{holiday_time}' AND CAST(date AS DATE) >= (DATE '{holiday_time}' - INTERVAL '{time_period2} DAYS');""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Stock Trading Volume Inquiry",
        "Template_ID": "0040",
        "Stock Trading Volume Inquiry": "What was the trading volume of {stock_name} {time_period1}",
        "SQL": """SELECT date,volume FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "ANSWER": "The stock trading volume is {volume}.",
        "HISTORY_SQL": """SELECT date,volume FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period1} days') AND CAST('2023-11-24' AS DATE);""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Stock Trading Volume Inquiry",
        "Template_ID": "0041",
        "Stock Trading Volume Inquiry": "Which day had a trading volume for {stock_name} that exceeded the average for {time_period2} before {time}?",
        "SQL": """SELECT date FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN ('{time}'::DATE  - INTERVAL '{time_period2} DAYS') AND '{time}'::DATE AND volume > (SELECT AVG(volume) FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN ('{time}'::DATE  - INTERVAL '{time_period2} DAYS') AND '{time}'::DATE);""",
        "ANSWER": "The stock trading volume is {volume}.",
        "HISTORY_SQL": """SELECT date,volume FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN ('{time}'::DATE - INTERVAL '{time_period2} DAYS') AND '{time}'::DATE;""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    },
    {
        "Intent": "Stock Trading Volume Inquiry",
        "Template_ID": "0042",
        "Stock Trading Volume Inquiry": "What were the trading volumes of {stock_name} on {time1} and {time2}?",
        "SQL": """SELECT date,volume FROM \"{stock_name}\" WHERE date IN ('{time1}', '{time2}');""",
        "ANSWER": "The stock trading volume is {volume}.",
        "HISTORY_SQL": """SELECT date,volume FROM \"{stock_name}\" WHERE date IN ('{time1}', '{time2}');""",
        "HISTORY_ANSWER": "The opening price is {opening_price}"
    }
]