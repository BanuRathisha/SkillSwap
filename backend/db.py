import os
import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "skillswap"),
        port=int(os.environ.get("DB_PORT", "3306"))
    )
    return connection