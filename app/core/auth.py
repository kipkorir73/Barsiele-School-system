import bcrypt
from db_manager import DBManager

def hash_password(pw):
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed, pw):
    return bcrypt.checkpw(pw.encode('utf-8'), hashed)

def create_user(username, pw, role):
    db = DBManager()
    hashed = hash_password(pw)
    db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))
    return db.last_id()

def validate_login(username, pw):
    db = DBManager()
    user = db.fetch_one("SELECT id, password, role FROM users WHERE username = ?", (username,))
    if user and check_password(user[1], pw):
        return {'id': user[0], 'role': user[2]}
    return None