import os
import sqlite3
from pathlib import Path
from .config import DB_TYPE, SQLITE_PATH, MYSQL_HOST, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD

class DBManager:
    def __init__(self):
        self.db_type = DB_TYPE
        self.conn = None
        self.cursor = None
        
        try:
            if self.db_type == 'sqlite':
                # Ensure data directory exists
                Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
                self.conn = sqlite3.connect(SQLITE_PATH)
            elif self.db_type == 'mysql':
                import mysql.connector
                self.conn = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    database=MYSQL_DB
                )
            
            if self.conn:
                self.cursor = self.conn.cursor()
                
        except Exception as e:
            print(f"Database connection error: {e}")
            raise

    def execute(self, query, params=()):
        if not self.cursor:
            raise Exception("Database connection not established")
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_one(self, query, params=()):
        if not self.cursor:
            raise Exception("Database connection not established")
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all(self, query, params=()):
        if not self.cursor:
            raise Exception("Database connection not established")
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def last_id(self):
        if not self.cursor:
            raise Exception("Database connection not established")
        return self.cursor.lastrowid
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()