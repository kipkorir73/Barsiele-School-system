import sqlite3
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

load_dotenv()

class DBManager:
    def __init__(self):
        """Initialize a new database connection for each instance"""
        db_type = os.getenv('DB_TYPE', 'sqlite')
        if db_type == 'sqlite':
            db_path = os.getenv('SQLITE_PATH', 'app/data/school_fees.db')
            # Ensure the directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
        else:
            raise ValueError("Only SQLite is supported with current configuration")
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logging.error(f"Database error: {exc_val}")
            self.conn.rollback()
        else:
            self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def execute(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self.conn.commit()
        except Exception as e:
            logging.error(f"Query execution failed: \n    {query}\n     - {str(e)}")
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