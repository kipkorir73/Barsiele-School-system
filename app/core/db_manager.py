import sqlite3
import os
from app.config import DB_TYPE, SQLITE_PATH, MYSQL_HOST, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, use_mysql=False):
        self.use_mysql = use_mysql or (DB_TYPE == 'mysql')
        self.conn = None

    def connect(self):
        if self.use_mysql:
            import mysql.connector
            self.conn = mysql.connector.connect(
                host=MYSQL_HOST, database=MYSQL_DB, user=MYSQL_USER, password=MYSQL_PASSWORD
            )
        else:
            os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
            self.conn = sqlite3.connect(SQLITE_PATH, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
            # Enable foreign keys
            self.conn.execute('PRAGMA foreign_keys = ON;')
        self.conn.row_factory = self._dict_factory
        logger.info('Database connected: %s', 'MySQL' if self.use_mysql else 'SQLite')
        return self.conn

    def _dict_factory(self, cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info('Database connection closed.')
