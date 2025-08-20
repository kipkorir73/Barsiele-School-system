from datetime import datetime
import uuid
from .db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def record_payment(student_id, amount, method, date, clerk_id):
    with DBManager() as db:
        try:
            receipt_no = str(uuid.uuid4())[:8]  # Unique receipt number
            db.execute(
                "INSERT INTO payments (student_id, amount, method, date, clerk_id, receipt_no) VALUES (?, ?, ?, ?, ?, ?)",
                (student_id, amount, method, date, clerk_id, receipt_no)
            )
            payment_id = db.cursor.lastrowid  # SQLite way to get last inserted ID
            log_action(clerk_id, f"Recorded payment {receipt_no} for student {student_id}")
            return payment_id, receipt_no
        except Exception as e:
            logging.error(f"Error recording payment for student {student_id}: {e}")
            raise

def get_payments_for_student(student_id):
    with DBManager() as db:
        try:
            return db.fetch_all("SELECT * FROM payments WHERE student_id = ? ORDER BY date DESC", (student_id,))
        except Exception as e:
            logging.error(f"Error fetching payments for student {student_id}: {e}")
            raise

def get_balance(student_id):
    with DBManager() as db:
        try:
            fee = db.fetch_one("SELECT total_fees, bus_fee FROM fees WHERE student_id = ?", (student_id,))
            total_fees = fee[0] if fee else 0
            bus_fee = fee[1] if fee else 0
            paid_result = db.fetch_one("SELECT SUM(amount) FROM payments WHERE student_id = ?", (student_id,))
            paid = paid_result[0] if paid_result and paid_result[0] else 0
            return total_fees + bus_fee - paid
        except Exception as e:
            logging.error(f"Error getting balance for student {student_id}: {e}")
            raise

def log_action(user_id, action):
    """Helper function to log actions"""
    with DBManager() as db:
        try:
            db.execute("INSERT INTO audit_logs (user_id, action) VALUES (?, ?)", (user_id, action))
        except Exception as e:
            logging.error(f"Error logging action: {e}")
            # Don't raise here as it's not critical