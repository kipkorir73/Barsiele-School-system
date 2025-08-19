import sqlite3
from dotenv import load_dotenv
import os
import logging

load_dotenv()

class DBManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            db_type = os.getenv('DB_TYPE', 'mysql')
            if db_type == 'sqlite':
                db_path = os.getenv('SQLITE_PATH', 'data/school_fees.db')
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                cls._instance.conn = sqlite3.connect(db_path)
                cls._instance.conn.row_factory = sqlite3.Row
            else:
                raise ValueError("Only SQLite is supported with current configuration")
            cls._instance.cursor = cls._instance.conn.cursor()
        return cls._instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logging.error(f"Database error: {exc_val}")
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
        self._instance = None

    def execute(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
        except Exception as e:
            logging.error(f"Query execution failed: {query} - {str(e)}")
            raise

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Exception as e:
            logging.error(f"Fetch one failed: {query} - {str(e)}")
            raise

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Exception as e:
            logging.error(f"Fetch all failed: {query} - {str(e)}")
            raise

# Ensure log directory exists
log_path = os.getenv('LOG_PATH', 'logs/school_fees.log')
log_dir = os.path.dirname(log_path)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')