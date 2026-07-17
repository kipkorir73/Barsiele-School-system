import csv
import os
import tempfile
import unittest
from pathlib import Path

from app.core.db_manager import DBManager
from app.core.models import tables
from app.core.payment_manager import get_balance, get_total_credits
from app.core.report_manager import generate_class_report, generate_student_balance_report


class TestContributionBalances(unittest.TestCase):
    def setUp(self):
        self.original_sqlite_path = os.environ.get("SQLITE_PATH")
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["SQLITE_PATH"] = str(Path(self.temp_dir.name) / "school_fees.db")
        os.chdir(self.temp_dir.name)

        with DBManager() as db:
            for table_sql in tables:
                db.execute(table_sql)
            db.execute("INSERT INTO classes (id, name) VALUES (1, 'Grade 7')")
            db.execute(
                """
                INSERT INTO students (id, admission_number, name, class_id)
                VALUES (1, 'ADM001', 'Test Student', 1)
                """
            )
            db.execute(
                """
                INSERT INTO fees (student_id, total_fees, bus_fee, boarding_fee)
                VALUES (1, 1000, 100, 200)
                """
            )
            db.execute(
                """
                INSERT INTO payments
                    (student_id, amount, method, date, clerk_id, receipt_no)
                VALUES (1, 100, 'Cash', '2026-07-17', 1, 'cash-1')
                """
            )
            # Old versions also wrote an in-kind contribution to payments.
            # It must not be counted in addition to the contribution row.
            db.execute(
                """
                INSERT INTO payments
                    (student_id, amount, method, date, clerk_id, receipt_no)
                VALUES (1, 300, 'Maize', '2026-07-17', 1, 'legacy-kind-1')
                """
            )
            db.execute(
                """
                INSERT INTO contributions (student_id, item, quantity, cash_equivalent)
                VALUES (1, 'Maize', 10, 300)
                """
            )
            db.execute(
                """
                INSERT INTO contributions (student_id, item, quantity, cash_equivalent)
                VALUES (1, 'Beans', 8, 200)
                """
            )

    def tearDown(self):
        os.chdir(self.original_cwd)
        if self.original_sqlite_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self.original_sqlite_path
        self.temp_dir.cleanup()

    def test_balance_credits_contributions_without_double_counting_legacy_payment(self):
        self.assertEqual(get_total_credits(1), 600)
        self.assertEqual(get_balance(1), 700)

    def test_balance_reports_include_contribution_credits(self):
        class_report = generate_class_report(1)
        with open(class_report, newline="", encoding="utf-8") as report:
            class_row = list(csv.reader(report))[1]

        self.assertEqual(float(class_row[5]), 600)
        self.assertEqual(float(class_row[6]), 700)

        student_report = generate_student_balance_report()
        with open(student_report, newline="", encoding="utf-8") as report:
            student_row = list(csv.reader(report))[1]

        self.assertEqual(float(student_row[6]), 600)
        self.assertEqual(float(student_row[7]), 700)


if __name__ == "__main__":
    unittest.main()
