# app/db.py
import os
import logging
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import Error

try:
    pool = MySQLConnectionPool(
        pool_name=os.getenv('DB_POOL_NAME', 'mypool'),
        pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
except Error as e:
    logging.error(f"❗ Fehler beim Initialisieren des Connection Pools: {e}")
    raise

def get_db_connection():
    try:
        return pool.get_connection()
    except Error as err:
        logging.error(f"❗ Fehler beim Holen der DB-Verbindung: {err}")
        raise
