from datetime import datetime
from db_manager import DBManager

def record_payment(student_id, amount, method, date, clerk_id):
    db = DBManager()
    db.execute(
        "INSERT INTO payments (student_id, amount, method, date, clerk_id) VALUES (?, ?, ?, ?, ?)",
        (student_id, amount, method, date, clerk_id)
    )
    return db.last_id()

def get_payments_for_student(student_id):
    db = DBManager()
    return db.fetch_all("SELECT * FROM payments WHERE student_id = ?", (student_id,))

def get_balance(student_id):
    db = DBManager()
    fee = db.fetch_one("SELECT total_fees FROM fees WHERE student_id = ?", (student_id,))
    total_fees = fee[0] if fee else 0
    paid = db.fetch_one("SELECT SUM(amount) FROM payments WHERE student_id = ?", (student_id,))[0] or 0
    return total_fees - paid