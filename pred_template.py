
template_data = [
    {
        "Intent": "Stock Price Prediction",  
        "Template_ID": "0001",  
        "question": "What will be the opening price of {stock_name} on {time}?",    
        "SQL_target": """SELECT open FROM \"{stock_name}\" WHERE date = '{time}';""",  
        "ANSWER": "The opening price three days later is {opening_price}",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },  
    {  
        "Intent": "Stock Price Prediction", 
        "Template_ID": "0002",  
        "question": "What will be the opening price of {stock_name} {vague_time}?", 
        "SQL_target": """SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) = '{vague_time}';""",  
        "ANSWER": "The opening price one week later is {opening_price}.",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },  
    {
        "Intent": "Stock Price Prediction",  
        "Template_ID": "0003",  
        "question": "What will be the respective opening prices of {stock_name} {time_period2}?",  
        "SQL_target": """SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{time_period2} days');""",  
        "ANSWER": "The opening price three days after {time} is {opening_price}.",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Price Prediction",  
        "Template_ID": "0004",  
        "question": "What will be the opening price of {stock_name} {time_period1} after {holiday_time}?", 
        "SQL_target": """SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('{holiday_time}' AS DATE) + INTERVAL '1 day') AND (CAST('{holiday_time}' AS DATE) + INTERVAL '{time_period1} days') AND open IS NOT NULL;""",  
        "ANSWER": "The opening prices before and after {time} are {opening_price1} and {opening_price2} respectively.",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },   
    {  
        "Intent": "Stock Price Prediction", 
        "Template_ID": "0005",  
        "question": "What will be the highest opening price of {stock_name} {time_period1} after {holiday_time}?", 
        "SQL_target": """SELECT MAX(open) FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('{holiday_time}' AS DATE) + INTERVAL '1 day') AND (CAST('{holiday_time}' AS DATE) + INTERVAL '{time_period1} days') AND open IS NOT NULL;""",  
        "ANSWER": "The stock price three days later is {opening_price}.",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    }, 
    {
        "Intent": "Stock Trend Prediction", 
        "Template_ID": "0006",  
        "question": "Will the opening price of {stock_name} rise or fall in {time_period1}?",
        "SQL_target": """SELECT CASE WHEN (SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) = CAST('2023-11-24' AS DATE) + INTERVAL '{time_period1} days') > (SELECT open FROM \"{stock_name}\" WHERE CAST(date AS DATE) = CAST('2023-11-24' AS DATE)) THEN 'rise' ELSE 'fall' END AS trend;""",  
        "ANSWER": "The opening price from future [day1] to [day2] is {opening_price}.",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction", 
        "Template_ID": "0007",   
        "question": "Will the opening price of {stock_name} set a new record {time_period2} relative to last month?",  
        "SQL_target": """SELECT CASE WHEN (SELECT MAX(open) FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{time_period2} days')) > (SELECT MAX(open) FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '30 days') AND CAST('2023-11-24' AS DATE)) THEN 'Yes' ELSE 'No' END AS will_reach_new_high;""",  
        "ANSWER": "The opening price of {stock_name} three days later is {opening_price}.",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",   
        "Template_ID": "0008",   
        "question": "Will the opening price of {stock_name} fall below its lowest value {time_period2} relative to last month?",  
        "SQL_target": """SELECT CASE WHEN (SELECT MIN(open) FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{time_period2} days')) > (SELECT MIN(open) FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '30 days') AND CAST('2023-11-24' AS DATE)) THEN 'Yes' ELSE 'No' END AS will_fall_below_lowest;""",  
        "ANSWER": "The opening price of {stock_name} one week later is {opening_price}.",  
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    }, 
    {
        "Intent": "Stock Trend Prediction",  
        "Template_ID": "0009",  
        "question": "Did the opening price of {stock_name} on {time} rise or fall relative to today?",  
        "SQL_target": """SELECT CASE WHEN t1.open > t2.open THEN 'rise' WHEN t1.open < t2.open THEN 'fall' ELSE 'unchange' END AS result FROM "{stock_name}" t1, "{stock_name}" t2 WHERE t1.date='{time}' AND t2.date='2023-11-24';""",  
        "ANSWER": "{stock_name} {rise or fall}",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {  
        "Intent": "Stock Trend Prediction", 
        "Template_ID": "0010",  
        "question": "Did the opening price of {stock_name} {vague_time} rise or fall relative to today?", 
        "SQL_target": """SELECT CASE WHEN t1.open > t2.open THEN 'rise' WHEN t1.open < t2.open THEN 'fall' ELSE 'unchange' END AS result FROM "{stock_name}" t1, "{stock_name}" t2 WHERE t1.date='{vague_time}' AND t2.date='2023-11-24';""",  
        "ANSWER": "{stock_name} {rise or fall}",  
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Trend Prediction",   
        "Template_ID": "0011",   
        "question": "Will the average opening price of {stock_name} {time_period2} go up or down relative to {time_period3}?",  
        "SQL_target": """SELECT CASE WHEN (SELECT AVG(open) FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{time_period2} days')) > (SELECT AVG(open) FROM "{stock_name}" WHERE CAST(date AS DATE) BETWEEN (CAST('2023-11-24' AS DATE) - INTERVAL '{time_period3} days') AND CAST('2023-11-24' AS DATE)) THEN 'rise' ELSE 'fall' END AS price_trend;""",  
        "ANSWER": "The opening prices before and after {time} are {opening_price1} and {opening_price2} respectively.", 
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Extremum Prediction", 
        "Template_ID": "0012",   
        "question": "On which day will the opening price of {stock_name} be the highest {time_period2}?",  
        "SQL_target": """SELECT date FROM \"{stock_name}\" WHERE CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{time_period2} days') ORDER BY open DESC LIMIT 1;""",  
        "ANSWER": "The minimum opening price of last week is {opening_price}.",
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    },
    {
        "Intent": "Stock Extremum Prediction",   
        "Template_ID": "0013",   
        "question": "{time_period4}, on which days did {stock_name} have an opening price exceeding {points} points?",  
        "SQL_target": """SELECT date FROM \"{stock_name}\" WHERE open > {points} AND CAST(date AS DATE) BETWEEN CAST('2023-11-25' AS DATE) AND (CAST('2023-11-24' AS DATE) + INTERVAL '{time_period4} days');""",  
        "ANSWER": "The opening prices before and after {time} are {opening_price1} and {opening_price2} respectively.",  
        "HISTORY_SQL": "SELECT date, open FROM (SELECT date, open FROM \"{stock_name}\" WHERE date::DATE <= (DATE '2023-11-25' - INTERVAL '1 DAY') ORDER BY date::DATE DESC LIMIT 49) AS subquery ORDER BY date::DATE ASC;"
    }
]