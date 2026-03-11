# app/db.py
import os
import logging
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import Error

_pool = None


def _create_pool():
    return MySQLConnectionPool(
        pool_name=os.getenv('DB_POOL_NAME', 'mypool'),
        pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'faktura_user'),
        password=os.getenv('DB_PASSWORD', 'meinpasswort'),
        database=os.getenv('DB_NAME', 'faktura_app')
    )


def get_db_connection():
        global _pool

    if _pool is None:
        try:
            _pool = _create_pool()
        except Error as err:
            logging.error(f"❗ Fehler beim Initialisieren des Connection Pools: {err}")
            raise

    try:
        return _pool.get_connection()
    except Error as err:
        logging.error(f"❗ Fehler beim Holen der DB-Verbindung: {err}")
        raise
