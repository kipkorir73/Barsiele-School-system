import os
from datetime import datetime
from fpdf import FPDF
from db_manager import DBManager
from student_manager import get_student

def generate_receipt(payment_id):
    if not os.path.exists('receipts'):
        os.makedirs('receipts')
    db = DBManager()
    payment = db.fetch_one("SELECT * FROM payments WHERE id = ?", (payment_id,))
    if not payment:
        return None
    student = get_student(payment[1])
    pdf = FPDF(format='A6')
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "School Payment Receipt", ln=1, align='C')
    pdf.cell(0, 10, f"Student: {student[2]} (Adm: {student[1]})", ln=1)
    pdf.cell(0, 10, f"Amount: {payment[2]}", ln=1)
    pdf.cell(0, 10, f"Method: {payment[3]}", ln=1)
    pdf.cell(0, 10, f"Date: {payment[4]}", ln=1)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"receipts/receipt_{payment_id}_{timestamp}.pdf"
    pdf.output(filename)
    db.execute("INSERT INTO receipts (payment_id, filename) VALUES (?, ?)", (payment_id, filename))
    return filename