from passlib.hash import bcrypt
from ..core.db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Auth:
    @staticmethod
    def hash_password(password):
        return bcrypt.hash(password)

    @staticmethod
    def verify_password(password, hashed):
        return bcrypt.verify(password, hashed)

    @staticmethod
    def create_user(username, password, role):
        hashed_password = Auth.hash_password(password)
        with DBManager() as db:
            try:
                db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                          (username, hashed_password, role))
                logging.info(f"User created: {username} ({role})")
            except Exception as e:
                logging.error(f"User creation failed: {e}")
                raise

    @staticmethod
    def authenticate(username, password):
        with DBManager() as db:
            user = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
            if user and Auth.verify_password(password, user['password']):
                logging.info(f"User logged in: {username}")
                return dict(user)
            return None

# Convenience functions for backward compatibility
def create_user(username, password, role):
    return Auth.create_user(username, password, role)

def validate_login(username, password):
    return Auth.authenticate(username, password)