import os
from datetime import datetime
from fpdf import FPDF
from .db_manager import DBManager
from .student_manager import get_student

def generate_receipt(payment_id):
    if not os.path.exists('receipts'):
        os.makedirs('receipts')
    
    db = DBManager()
    try:
        payment = db.fetch_one("SELECT * FROM payments WHERE id = ?", (payment_id,))
        if not payment:
            return None
        
        student = get_student(payment[1])
        if not student:
            return None
            
        pdf = FPDF(format='A6')
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "School Payment Receipt", ln=1, align='C')
        pdf.ln(5)
        pdf.cell(0, 8, f"Student: {student[2]} (Adm: {student[1]})", ln=1)
        pdf.cell(0, 8, f"Amount: KSh {payment[2]:,.2f}", ln=1)
        pdf.cell(0, 8, f"Method: {payment[3]}", ln=1)
        pdf.cell(0, 8, f"Date: {payment[4]}", ln=1)
        pdf.cell(0, 8, f"Receipt ID: {payment_id}", ln=1)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"receipts/receipt_{payment_id}_{timestamp}.pdf"
        pdf.output(filename)
        
        # Record receipt in database
        db.execute("INSERT INTO receipts (payment_id, filename) VALUES (?, ?)", (payment_id, filename))
        
        return filename
        
    except Exception as e:
        print(f"Error generating receipt: {e}")
        return None
    finally:
        db.close()