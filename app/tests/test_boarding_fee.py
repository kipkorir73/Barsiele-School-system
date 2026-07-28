"""Regression tests for boarding fee apply + balance inclusion."""

import os
import tempfile
import unittest
from unittest import mock


LEGACY_SCHEMA = """
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    class_id INTEGER,
    guardian_contact TEXT,
    profile_picture TEXT,
    bus_location TEXT
);
CREATE TABLE fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER UNIQUE NOT NULL,
    total_fees REAL NOT NULL DEFAULT 0.0,
    bus_fee REAL NOT NULL DEFAULT 0.0
);
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    method TEXT NOT NULL,
    date TEXT NOT NULL,
    clerk_id INTEGER NOT NULL,
    receipt_no TEXT UNIQUE NOT NULL
);
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class BoardingFeeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        self.env = mock.patch.dict(os.environ, {"SQLITE_PATH": self.db_path, "DB_TYPE": "sqlite"})
        self.env.start()

        from app.core.db_manager import DBManager
        with DBManager() as db:
            for stmt in LEGACY_SCHEMA.strip().split(";"):
                if stmt.strip():
                    db.execute(stmt)
            db.execute("INSERT INTO classes (name) VALUES (?)", ("Grade 7",))
            db.execute(
                "INSERT INTO students (admission_number, name, class_id) VALUES (?, ?, ?)",
                ("ADM001", "Boarding Student", 1),
            )
            db.execute(
                "INSERT INTO fees (student_id, total_fees, bus_fee) VALUES (?, ?, ?)",
                (1, 30000.0, 0.0),
            )
            db.execute(
                "INSERT INTO payments (student_id, amount, method, date, clerk_id, receipt_no) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (1, 35000.0, "Cash", "2025-08-01", 1, "rcpt001"),
            )

    def tearDown(self):
        self.env.stop()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_apply_boarding_fee_migrates_legacy_schema_instead_of_noop(self):
        from app.core.db_manager import DBManager
        from app.core.fee_manager import set_boarding_fee_for_class, get_fee
        from app.core.payment_manager import get_balance

        with DBManager() as db:
            cols = [c[1] for c in db.fetch_all("PRAGMA table_info(fees)")]
            self.assertNotIn("boarding_fee", cols)

        updated = set_boarding_fee_for_class(1, 15000.0)
        self.assertEqual(updated, 1)

        with DBManager() as db:
            cols = [c[1] for c in db.fetch_all("PRAGMA table_info(fees)")]
            self.assertIn("boarding_fee", cols)
            row = db.fetch_one("SELECT boarding_fee FROM fees WHERE student_id = 1")
            self.assertEqual(row[0], 15000.0)

        fee = get_fee(1)
        self.assertEqual(fee["boarding_fee"], 15000.0)
        # tuition 30000 + boarding 15000 - paid 35000 = 10000 still owed
        self.assertEqual(get_balance(1), 10000.0)

    def test_arrears_and_reports_include_boarding_fee(self):
        from app.core.fee_manager import set_boarding_fee_for_class
        from app.core.report_manager import generate_student_balance_report, generate_class_report
        from app.core.db_manager import DBManager

        set_boarding_fee_for_class(1, 15000.0)

        # Mirror arrears_detail expected-fee math
        with DBManager() as db:
            student = db.fetch_one(
                """
                SELECT COALESCE(f.total_fees, 0), COALESCE(f.bus_fee, 0), COALESCE(f.boarding_fee, 0)
                FROM fees f WHERE f.student_id = 1
                """
            )
            paid = db.fetch_one("SELECT SUM(amount) FROM payments WHERE student_id = 1")[0]
            total_expected = student[0] + student[1] + student[2]
            arrears = total_expected - paid
            self.assertEqual(total_expected, 45000.0)
            self.assertEqual(arrears, 10000.0)

        balance_report = generate_student_balance_report()
        with open(balance_report, encoding="utf-8") as f:
            contents = f.read()
        self.assertIn("Boarding Fee", contents)
        self.assertIn("15000", contents)
        self.assertIn("10000", contents)

        class_report = generate_class_report(1)
        with open(class_report, encoding="utf-8") as f:
            class_contents = f.read()
        self.assertIn("Boarding Fee", class_contents)
        self.assertIn("15000", class_contents)


if __name__ == "__main__":
    unittest.main()
