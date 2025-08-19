from db_manager import DBManager

def set_fee(student_id, total_fees):
    db = DBManager()
    db.execute(
        "INSERT OR REPLACE INTO fees (student_id, total_fees) VALUES (?, ?)",
        (student_id, total_fees)
    )