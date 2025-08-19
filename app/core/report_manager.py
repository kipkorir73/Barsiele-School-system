import csv
import os
from .db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_payment_summary(start_date, end_date):
    os.makedirs('reports', exist_ok=True)
    with DBManager() as db:
        try:
            payments = db.fetch_all(
                "SELECT * FROM payments WHERE date BETWEEN %s AND %s ORDER BY date DESC",
                (start_date, end_date)
            )
            filename = f"reports/payment_summary_{start_date}_{end_date}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Payment ID', 'Student ID', 'Amount', 'Method', 'Date', 'Clerk ID', 'Receipt No'])
                for payment in payments:
                    writer.writerow(payment)
            logging.info(f"Generated payment summary: {filename}")
            return filename
        except Exception as e:
            logging.error(f"Error generating payment summary: {e}")
            raise

def generate_student_balance_report():
    os.makedirs('reports', exist_ok=True)
    with DBManager() as db:
        try:
            query = """
            SELECT s.id, s.admission_number, s.name, c.name as class_name,
                   COALESCE(f.total_fees, 0) as total_fees,
                   COALESCE(f.bus_fee, 0) as bus_fee,
                   COALESCE(SUM(p.amount), 0) as total_paid,
                   (COALESCE(f.total_fees, 0) + COALESCE(f.bus_fee, 0) - COALESCE(SUM(p.amount), 0)) as balance
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN fees f ON s.id = f.student_id
            LEFT JOIN payments p ON s.id = p.student_id
            GROUP BY s.id, s.admission_number, s.name, c.name, f.total_fees, f.bus_fee
            ORDER BY c.name, s.name
            """
            results = db.fetch_all(query)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reports/student_balances_{timestamp}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Student ID', 'Adm No', 'Name', 'Class', 'Total Fees', 'Bus Fee', 'Total Paid', 'Balance'])
                for result in results:
                    writer.writerow(result)
            logging.info(f"Generated student balance report: {filename}")
            return filename
        except Exception as e:
            logging.error(f"Error generating student balance report: {e}")
            raise