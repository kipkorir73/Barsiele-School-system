import csv
from db_manager import DBManager

def generate_payment_summary(start_date, end_date):
    db = DBManager()
    payments = db.fetch_all("SELECT * FROM payments WHERE date BETWEEN ? AND ?", (start_date, end_date))
    filename = f"reports/summary_{start_date}_{end_date}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Student ID', 'Amount', 'Method', 'Date', 'Clerk ID'])
        for p in payments:
            writer.writerow(p)
    return filename