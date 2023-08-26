import sqlite3
from sqlite3 import Error
import pandas as pd 

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
        
def pd_to_sql(conn, df, table_name, if_exists="replace", index=False):
    """ Uploads a pandas dataframe to SQLite database """
    df.to_sql(table_name,
              conn, 
              if_exists=if_exists,
              index=index)
    
def get_tablenames_fromsql(conn):
    """ SEE all tables in database """
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [val for item in cursor.fetchall() for val in item]

def delete_table(conn, table_name):
    """ drop table """
    try:
        conn.execute(f"DROP TABLE {table_name}")
    except Error as e:
        print(e)
        
def sql_to_pd(conn, table_name, columns = None):
    """ Load data from SQLite database """
    if columns:
        columns = ", ".join(columns)
    else:
        columns = '*'
    query_ = f"""select {columns} from {table_name}"""
    df = pd.read_sql(query_ , conn)
    return df