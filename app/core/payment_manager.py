from app.db_manager import DatabaseManager
from decimal import Decimal
from app.fee_manager import FeeManager
import logging, os
from app.receipt_generator import ReceiptGenerator

logger = logging.getLogger(__name__)

class PaymentManager:
    def __init__(self, dbm=None):
        self.dbm = dbm or DatabaseManager()
        self.fee_manager = FeeManager()

    def calculate_total(self, cash_amount, maize_kg, millet_kg):
        maize_rate = self.fee_manager.get_conversion_rate('maize') or Decimal('0')
        millet_rate = self.fee_manager.get_conversion_rate('millet') or Decimal('0')
        total = Decimal(cash_amount or 0) + Decimal(maize_kg or 0) * maize_rate + Decimal(millet_kg or 0) * millet_rate
        return total, maize_rate, millet_rate

    def record_payment(self, admission_number, term_id, cash_amount=0, maize_kg=0, millet_kg=0, receipt_no=None):
        db = self.dbm
        conn = db.connect()
        cur = conn.cursor()
        # find student id
        cur.execute('SELECT student_id, class_name FROM students WHERE admission_number = ?;', (admission_number,))
        student = cur.fetchone()
        if not student:
            db.close()
            return {'success': False, 'error': 'Student not found'}
        student_id = student['student_id']
        total, maize_rate, millet_rate = self.calculate_total(cash_amount, maize_kg, millet_kg)
        try:
            cur.execute('''
                INSERT INTO payments (student_id, term_id, payment_type, cash_amount, maize_kg, millet_kg, converted_amount, total_amount, receipt_no)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            ''', (
                student_id, term_id,
                'mixed' if (maize_kg or millet_kg) and cash_amount else ('maize' if maize_kg and not cash_amount else ('millet' if millet_kg and not cash_amount else 'cash')),
                float(cash_amount), float(maize_kg), float(millet_kg),
                float((maize_kg or 0) * maize_rate + (millet_kg or 0) * millet_rate),
                float(total),
                receipt_no
            ))
            conn.commit()
            payment_id = cur.lastrowid
            # generate receipt
            os.makedirs(ReceiptGenerator.RECEIPTS_DIR, exist_ok=True)
            rg = ReceiptGenerator()
            receipt_path = rg.generate_receipt(payment_id)
            db.close()
            return {'success': True, 'payment_id': payment_id, 'receipt_path': receipt_path, 'total': float(total)}
        except Exception as e:
            conn.rollback()
            db.close()
            logger.exception('Error recording payment: %s', e)
            return {'success': False, 'error': str(e)}

    def get_student_payments(self, admission_number):
        db = self.dbm
        conn = db.connect()
        cur = conn.cursor()
        cur.execute('SELECT student_id FROM students WHERE admission_number = ?;', (admission_number,))
        s = cur.fetchone()
        if not s:
            db.close()
            return []
        student_id = s['student_id']
        cur.execute('SELECT * FROM payments WHERE student_id = ? ORDER BY payment_date DESC;', (student_id,))
        rows = cur.fetchall()
        db.close()
        return rows
