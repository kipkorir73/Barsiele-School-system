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
    def create_user(username, email, password, role):
        hashed_password = Auth.hash_password(password)
        with DBManager() as db:
            try:
                db.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                          (username, email, hashed_password, role))
                logging.info(f"User created: {username} ({email}) - {role}")
            except Exception as e:
                logging.error(f"User creation failed: {e}")
                raise

    @staticmethod
    def authenticate(email_or_username, password):
        with DBManager() as db:
            # Try to authenticate with email first, then username for backward compatibility
            user = db.fetch_one("SELECT * FROM users WHERE email = ? OR username = ?", (email_or_username, email_or_username))
            if user and Auth.verify_password(password, user['password']):
                user_dict = dict(user)
                logging.info(f"User logged in: {user_dict['username']} ({user_dict['email']})")
                return user_dict
            return None

# Convenience functions for backward compatibility
def create_user(username, email, password, role):
    return Auth.create_user(username, email, password, role)

def validate_login(identifier, password):
    return Auth.authenticate(identifier, password)