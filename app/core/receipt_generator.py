from fpdf import FPDF
from .db_manager import DBManager
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReceiptGenerator:
    @staticmethod
    def generate_receipt(payment_id, receipt_no):
        try:
            with DBManager() as db:
                payment = db.fetch_one("SELECT * FROM payments WHERE id = ?", (payment_id,))
                if not payment:
                    logging.error(f"Payment {payment_id} not found")
                    return None
                
                student_id = payment[1]  # student_id is at index 1
                student = db.fetch_one("SELECT name, admission_number FROM students WHERE id = ?", (student_id,))
                clerk = db.fetch_one("SELECT username FROM users WHERE id = ?", (payment[5],))  # clerk_id is at index 5
                
                if not student:
                    logging.error(f"Student {student_id} not found")
                    return None
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=16)
                
                # Header
                pdf.cell(200, 10, txt="SCHOOL MANAGEMENT SYSTEM", ln=1, align="C")
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 5, txt="PAYMENT RECEIPT", ln=1, align="C")
                pdf.ln(5)
                
                # Receipt details
                pdf.cell(200, 8, txt=f"Receipt No: {receipt_no}", ln=1)
                pdf.cell(200, 8, txt=f"Date: {payment[4]}", ln=1)  # date is at index 4
                pdf.ln(3)
                
                # Student details
                pdf.cell(200, 8, txt=f"Student: {student[0]}", ln=1)  # name
                pdf.cell(200, 8, txt=f"Admission No: {student[1]}", ln=1)  # admission_number
                pdf.ln(3)
                
                # Payment details
                pdf.cell(200, 8, txt=f"Amount Paid: KSh {payment[2]:,.2f}", ln=1)  # amount is at index 2
                pdf.cell(200, 8, txt=f"Payment Method: {payment[3]}", ln=1)  # method is at index 3
                pdf.cell(200, 8, txt=f"Processed by: {clerk[0] if clerk else 'Unknown'}", ln=1)
                pdf.ln(5)
                
                # Footer
                pdf.set_font("Arial", size=10)
                pdf.cell(200, 8, txt="Thank you for your payment!", ln=1, align="C")
                pdf.cell(200, 8, txt="Keep this receipt for your records.", ln=1, align="C")
                
                # Ensure receipts directory exists
                receipts_dir = os.path.join(os.path.dirname(__file__), '..', 'receipts')
                os.makedirs(receipts_dir, exist_ok=True)
                
                filename = os.path.join(receipts_dir, f"receipt_{receipt_no}.pdf")
                pdf.output(filename)
                
                # Save receipt record to database
                db.execute("INSERT OR REPLACE INTO receipts (payment_id, receipt_no, filename) VALUES (?, ?, ?)",
                          (payment_id, receipt_no, filename))
                
                logging.info(f"Receipt generated: {filename}")
                return filename
                
        except Exception as e:
            logging.error(f"Receipt generation failed: {str(e)}")
            return None

# Standalone function for easier importing
def generate_receipt(payment_id, receipt_no):
    """Generate a PDF receipt for a payment"""
    return ReceiptGenerator.generate_receipt(payment_id, receipt_no)