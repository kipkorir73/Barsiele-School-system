import csv
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.core.initialize_db import init_db
from app.core.report_manager import generate_class_report, generate_student_balance_report


class TestReportManager(unittest.TestCase):
    def setUp(self):
        self.original_sqlite_path = os.environ.get("SQLITE_PATH")
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.db_path = str(self.workspace / "school_fees.db")
        os.environ["SQLITE_PATH"] = self.db_path
        os.chdir(self.workspace)
        init_db()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO classes (name) VALUES ('Boarding Class')")
        self.class_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO students (admission_number, name, class_id) VALUES ('ADM001', 'Boarding Student', ?)",
            (self.class_id,)
        )
        self.student_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO fees (student_id, total_fees, bus_fee, boarding_fee) VALUES (?, 1000, 100, 500)",
            (self.student_id,)
        )
        cursor.execute(
            """
            INSERT INTO payments (student_id, amount, method, date, clerk_id, receipt_no, verified)
            VALUES (?, 300, 'Cash', '2025-08-20', 1, 'R001', 1)
            """,
            (self.student_id,)
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        os.chdir(self.original_cwd)
        if self.original_sqlite_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self.original_sqlite_path
        self.temp_dir.cleanup()

    def test_balance_reports_include_boarding_fee(self):
        class_report = generate_class_report(self.class_id)
        balance_report = generate_student_balance_report()

        with open(class_report, newline="", encoding="utf-8") as file:
            class_rows = list(csv.reader(file))
        with open(balance_report, newline="", encoding="utf-8") as file:
            balance_rows = list(csv.reader(file))

        self.assertEqual(class_rows[1][-1], "1300.0")
        self.assertEqual(balance_rows[1][-1], "1300.0")


if __name__ == "__main__":
    unittest.main()
