import pandas as pd  
import psycopg2  
import os  
from sqlalchemy import create_engine

# 定义 CSV 文件所在目录  
csv_directory = '/home/bbx/dataset/full_history/full_history'  # 替换为你的 CSV 文件所在目录  
# 创建 SQLAlchemy 数据库引擎  
engine = create_engine('postgresql+psycopg2://bbx:123456@localhost:1213/postgres')  

# 遍历 CSV 文件目录  
for filename in os.listdir(csv_directory):  
    if filename.endswith('.csv'):  
        csv_file_path = os.path.join(csv_directory, filename)  
        print(f"处理文件: {csv_file_path}")  
        
        # 读取 CSV 文件  
        df = pd.read_csv(csv_file_path)  

        # 将 DataFrame 中的数据写入 PostgreSQL 表  
        table_name = filename[:-4]  # 将文件名作为表名，去掉 .csv 后缀  
        df.to_sql(table_name, engine, if_exists='replace', index=False)  

        print(f"数据已成功写入表 {table_name}") 
