from datetime import datetime
import uuid
from .db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def record_payment(student_id, amount, method, date, clerk_id, transaction_code=None, bank_reference=None, mpesa_code=None):
    with DBManager() as db:
        try:
            receipt_no = str(uuid.uuid4())[:8]  # Unique receipt number
            
            # Check for duplicate transaction codes to prevent duplicate payments
            if transaction_code:
                existing = db.fetch_one("SELECT id FROM payments WHERE transaction_code = ?", (transaction_code,))
                if existing:
                    raise ValueError(f"Transaction code {transaction_code} already exists. Duplicate payment prevented.")
            
            if mpesa_code:
                existing = db.fetch_one("SELECT id FROM payments WHERE mpesa_code = ?", (mpesa_code,))
                if existing:
                    raise ValueError(f"M-Pesa code {mpesa_code} already exists. Duplicate payment prevented.")
            
            if bank_reference:
                existing = db.fetch_one("SELECT id FROM payments WHERE bank_reference = ?", (bank_reference,))
                if existing:
                    raise ValueError(f"Bank reference {bank_reference} already exists. Duplicate payment prevented.")
            
            db.execute(
                "INSERT INTO payments (student_id, amount, method, date, clerk_id, receipt_no, transaction_code, bank_reference, mpesa_code, verified) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (student_id, amount, method, date, clerk_id, receipt_no, transaction_code, bank_reference, mpesa_code, 1)
            )
            payment_id = db.cursor.lastrowid  # SQLite way to get last inserted ID
            
            # Enhanced logging with verification details
            verification_info = []
            if transaction_code:
                verification_info.append(f"Transaction: {transaction_code}")
            if mpesa_code:
                verification_info.append(f"M-Pesa: {mpesa_code}")
            if bank_reference:
                verification_info.append(f"Bank: {bank_reference}")
            
            verification_text = " | " + " | ".join(verification_info) if verification_info else ""
            log_action(clerk_id, f"Recorded payment {receipt_no} for student {student_id} via {method}{verification_text}")
            
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
            # Detect if boarding_fee column exists (pre-migration DBs won't have it)
            cols = db.fetch_all("PRAGMA table_info(fees)")
            has_boarding = any(col[1] == 'boarding_fee' for col in cols)
            if has_boarding:
                fee = db.fetch_one("SELECT total_fees, bus_fee, COALESCE(boarding_fee, 0) FROM fees WHERE student_id = ?", (student_id,))
                total_fees = fee[0] if fee else 0
                bus_fee = fee[1] if fee else 0
                boarding_fee = fee[2] if fee and len(fee) > 2 else 0
            else:
                fee = db.fetch_one("SELECT total_fees, bus_fee FROM fees WHERE student_id = ?", (student_id,))
                total_fees = fee[0] if fee else 0
                bus_fee = fee[1] if fee else 0
                boarding_fee = 0
            paid_result = db.fetch_one("SELECT SUM(amount) FROM payments WHERE student_id = ?", (student_id,))
            paid = paid_result[0] if paid_result and paid_result[0] else 0
            return total_fees + bus_fee + boarding_fee - paid
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