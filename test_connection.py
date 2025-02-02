import mysql.connector
import pyodbc

# Uji koneksi ke MySQL
mysql_conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='sqms_django',
)

print("MySQL connection successful!")

# Uji koneksi ke SQL Server
sql_server_conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=10.50.2.20;'
    'PORT=1433;'
    'DATABASE=sqms_django;'
    'UID=sa;'
    'PWD=konawe@2023;'
)

print("SQL Server connection successful!")
