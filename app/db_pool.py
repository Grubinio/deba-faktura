# app/db.py
import os
import logging
import threading
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import Error, connect

_pool = None
_pool_lock = threading.Lock()


def _create_pool():
    # Pool-Name muss pro Prozess eindeutig sein, sonst kann mysql-connector
    # unter mod_wsgi bei Reloads mit "Pool name ... already exists" abbrechen.
    pool_name = f"{os.getenv('DB_POOL_NAME', 'mypool')}_{os.getpid()}"
    return MySQLConnectionPool(
        pool_name=pool_name,
        pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'faktura_user'),
        password=os.getenv('DB_PASSWORD', 'meinpasswort'),
        database=os.getenv('DB_NAME', 'faktura_app')
    )


def get_db_connection():
    global _pool

    if _pool is None:
        with _pool_lock:
            if _pool is None:
                try:
                    _pool = _create_pool()
                except Error as err:
                    logging.error(f"❗ Fehler beim Initialisieren des Connection Pools: {err}")
                    raise

    try:
        return _pool.get_connection()
    except Error as err:
        logging.warning(f"⚠️ Pool-Verbindung fehlgeschlagen, versuche Direktverbindung: {err}")
        try:
            return connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'faktura_user'),
                password=os.getenv('DB_PASSWORD', 'meinpasswort'),
                database=os.getenv('DB_NAME', 'faktura_app')
            )
        except Error as direct_err:
            logging.error(f"❗ Fehler bei Direktverbindung zur DB: {direct_err}")
            raise
