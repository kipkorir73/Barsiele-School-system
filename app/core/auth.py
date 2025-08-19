from passlib.hash import bcrypt
from app.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, dbm=None):
        self.dbm = dbm or DatabaseManager()

    def create_user(self, username, password, role='admin'):
        conn = self.dbm.connect()
        cur = conn.cursor()
        password_hash = bcrypt.hash(password)
        # users table is optional; create if not exists
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );''')
        cur.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?);',
                    (username, password_hash, role))
        conn.commit()
        logger.info('User created: %s', username)
        self.dbm.close()

    def verify_user(self, username, password):
        conn = self.dbm.connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?;', (username,))
        user = cur.fetchone()
        self.dbm.close()
        if not user:
            return False, 'User not found'
        valid = bcrypt.verify(password, user['password_hash'])
        return valid, user if valid else (False, 'Invalid credentials')
