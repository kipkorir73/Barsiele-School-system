import os, logging
from fpdf import FPDF
from app.db_manager import DatabaseManager
from app.config import RECEIPTS_DIR
from datetime import datetime

logger = logging.getLogger(__name__)

class ReceiptGenerator:
    RECEIPTS_DIR = RECEIPTS_DIR

    def __init__(self):
        self.dbm = DatabaseManager()

    def generate_receipt(self, payment_id):
        conn = self.dbm.connect()
        cur = conn.cursor()
        cur.execute('''SELECT p.*, s.full_name, s.admission_number, s.class_name
                       FROM payments p JOIN students s ON p.student_id = s.student_id
                       WHERE p.payment_id = ?;''', (payment_id,))
        row = cur.fetchone()
        if not row:
            self.dbm.close()
            raise RuntimeError('Payment not found for receipt.')
        # create simple PDF receipt
        os.makedirs(self.RECEIPTS_DIR, exist_ok=True)
        filename = f"receipt_{payment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = os.path.join(self.RECEIPTS_DIR, filename)
        pdf = FPDF(format='A6', unit='mm')
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 6, 'SUNRISE ACADEMY', ln=True, align='C')
        pdf.set_font('Arial', size=10)
        pdf.cell(0, 6, 'School Fees Receipt', ln=True, align='C')
        pdf.ln(4)
        pdf.set_font('Arial', size=9)
        pdf.cell(0, 5, f"Receipt No: {row.get('receipt_no') or ''}", ln=True)
        pdf.cell(0, 5, f"Date: {row.get('payment_date')}", ln=True)
        pdf.cell(0, 5, f"Student: {row.get('full_name')} ({row.get('admission_number')})", ln=True)
        pdf.cell(0, 5, f"Class: {row.get('class_name')}", ln=True)
        pdf.ln(3)
        pdf.cell(0, 5, f"Cash: KES {row.get('cash_amount')}", ln=True)
        pdf.cell(0, 5, f"Maize (kg): {row.get('maize_kg')}", ln=True)
        pdf.cell(0, 5, f"Millet (kg): {row.get('millet_kg')}", ln=True)
        pdf.cell(0, 5, f"Total (KES): {row.get('total_amount')}", ln=True)
        pdf.ln(6)
        pdf.cell(0, 5, 'Thank you for your payment.', ln=True, align='C')
        pdf.output(path)
        self.dbm.close()
        logger.info('Receipt generated: %s', path)
        return path
