import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

class DBManager:
    def __init__(self):
        self.db_type = os.getenv('DB_TYPE', 'sqlite')
        if self.db_type == 'sqlite':
            if not os.path.exists('data'):
                os.makedirs('data')
            self.conn = sqlite3.connect('data/school.db')
        elif self.db_type == 'mysql':
            import mysql.connector
            self.conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASS'),
                database=os.getenv('DB_NAME')
            )
        self.cursor = self.conn.cursor()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def last_id(self):
        if self.db_type == 'sqlite':
            return self.cursor.lastrowid
        else:
            return self.cursor.lastrowid