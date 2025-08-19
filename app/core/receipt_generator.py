from fpdf import FPDF  # Changed to fpdf2 import style, but fpdf2 is a drop-in replacement for basic use
from ..core.db_manager import DBManager
import os
from datetime import datetime

class ReceiptGenerator:
    @staticmethod
    def generate_receipt(payment_id, receipt_no):
        try:
            with DBManager() as db:
                payment = db.fetch_one("SELECT * FROM payments WHERE id = ?", (payment_id,))
                if not payment:
                    return None
                
                student_id = payment['student_id']
                student = db.fetch_one("SELECT name, admission_number FROM students WHERE id = ?", (student_id,))
                clerk = db.fetch_one("SELECT username FROM users WHERE id = ?", (payment['clerk_id'],))
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="School Management System Receipt", ln=1, align="C")
                pdf.cell(200, 10, txt=f"Receipt No: {receipt_no}", ln=1, align="C")
                pdf.cell(200, 10, txt=f"Date: {payment['date']}", ln=1, align="C")
                pdf.cell(200, 10, txt=f"Student: {student['name']} (Adm No: {student['admission_number']})", ln=1)
                pdf.cell(200, 10, txt=f"Amount: KSh {payment['amount']:.2f}", ln=1)
                pdf.cell(200, 10, txt=f"Method: {payment['method']}", ln=1)
                pdf.cell(200, 10, txt=f"Clerk: {clerk['username']}", ln=1)
                pdf.cell(200, 10, txt="Thank you for your payment!", ln=1)
                
                receipts_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'receipts')
                os.makedirs(receipts_dir, exist_ok=True)
                filename = os.path.join(receipts_dir, f"receipt_{receipt_no}.pdf")
                pdf.output(filename)
                
                db.execute("INSERT OR REPLACE INTO receipts (payment_id, receipt_no, filename) VALUES (?, ?, ?)",
                          (payment_id, receipt_no, filename))
                return filename
        except Exception as e:
            print(f"Receipt generation failed: {str(e)}")
            return None