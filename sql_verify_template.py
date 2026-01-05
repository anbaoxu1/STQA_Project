import psycopg2

class PostgresQueryExecutor:
    def __init__(self, host='localhost', database='*******', user='***', password='******', port="****"):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.conn = None
        self.cur = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            self.cur = self.conn.cursor()
        except psycopg2.DatabaseError as e:
            print(f"Database connection error: {e}")
            raise

    def execute_sql(self, sql_statement):
        if not self.conn or not self.cur:
            self.connect()
        try:
            self.cur.execute(sql_statement)
            result = self.cur.fetchall()
            self.conn.commit()
            return result
        except Exception as e:
            print(f"Error executing SQL statement: {e}")
            return None

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
def find_answer(sql_statement):
    
    target_executor = PostgresQueryExecutor()
    answer = target_executor.execute_sql(sql_statement)
    return answer
