from passlib.hash import bcrypt
from ..core.db_manager import DBManager

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
            db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, hashed_password, role))

    @staticmethod
    def authenticate(username, password):
        with DBManager() as db:
            user = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
            if user and Auth.verify_password(password, user['password']):
                return dict(user)
            return None