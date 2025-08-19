from .db_manager import DBManager

def set_fee(student_id, total_fees):
    db = DBManager()
    try:
        db.execute(
            "INSERT OR REPLACE INTO fees (student_id, total_fees) VALUES (?, ?)",
            (student_id, total_fees)
        )
    finally:
        db.close()

def get_fee(student_id):
    """Get total fee for a student"""
    db = DBManager()
    try:
        result = db.fetch_one("SELECT total_fees FROM fees WHERE student_id = ?", (student_id,))
        return result[0] if result else 0.0
    finally:
        db.close()