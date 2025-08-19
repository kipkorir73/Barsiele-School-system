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
                "INSERT INTO payments (student_id, amount, method, date, clerk_id, receipt_no) VALUES (%s, %s, %s, %s, %s, %s)",
                (student_id, amount, method, date, clerk_id, receipt_no)
            )
            log_action(clerk_id, f"Recorded payment {receipt_no} for student {student_id}")
            return db.last_id(), receipt_no
        except Exception as e:
            logging.error(f"Error recording payment for student {student_id}: {e}")
            raise

def get_payments_for_student(student_id):
    with DBManager() as db:
        try:
            return db.fetch_all("SELECT * FROM payments WHERE student_id = %s ORDER BY date DESC", (student_id,))
        except Exception as e:
            logging.error(f"Error fetching payments for student {student_id}: {e}")
            raise

def get_balance(student_id):
    with DBManager() as db:
        try:
            fee = db.fetch_one("SELECT total_fees, bus_fee FROM fees WHERE student_id = %s", (student_id,))
            total_fees = fee[0] if fee else 0
            bus_fee = fee[1] if fee else 0
            paid = db.fetch_one("SELECT SUM(amount) FROM payments WHERE student_id = %s", (student_id,))[0] or 0
            return total_fees + bus_fee - paid
        except Exception as e:
            logging.error(f"Error getting balance for student {student_id}: {e}")
            raise