"""Cheque numbers must not be globally unique across students."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock


LEGACY_PAYMENTS_SQL = """
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    method TEXT NOT NULL,
    date TEXT NOT NULL,
    clerk_id INTEGER NOT NULL,
    receipt_no TEXT UNIQUE NOT NULL,
    transaction_code TEXT UNIQUE,
    bank_reference TEXT,
    mpesa_code TEXT,
    verified BOOLEAN DEFAULT 0
)
"""


class TestChequeUniqueness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "cheque_test.db")
        self.env_patch = mock.patch.dict(os.environ, {
            "SQLITE_PATH": self.db_path,
            "DB_TYPE": "sqlite",
            "LOG_PATH": str(Path(self.tmp.name) / "test.log"),
        })
        self.env_patch.start()

        # Force DBManager to use the temp DB even if dotenv already loaded.
        from app.core import db_manager
        self._orig_init = db_manager.DBManager.__init__

        def _init(instance):
            instance.conn = sqlite3.connect(self.db_path)
            instance.conn.row_factory = sqlite3.Row
            instance.cursor = instance.conn.cursor()

        db_manager.DBManager.__init__ = _init

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            );
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
                bus_fee REAL NOT NULL DEFAULT 0.0,
                boarding_fee REAL NOT NULL DEFAULT 0.0
            );
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(LEGACY_PAYMENTS_SQL)
        cur.execute(
            "INSERT INTO users (username, email, password, role) VALUES ('clerk','c@t.com','x','clerk')"
        )
        cur.execute("INSERT INTO classes (name) VALUES ('Grade 1')")
        cur.execute(
            "INSERT INTO students (admission_number, name, class_id, guardian_contact) "
            "VALUES ('ADM1','Alice',1,'g'), ('ADM2','Bob',1,'g')"
        )
        cur.execute(
            "INSERT INTO fees (student_id, total_fees, bus_fee, boarding_fee) VALUES (1,1000,0,0), (2,1000,0,0)"
        )
        conn.commit()
        conn.close()

        # Confirm the buggy legacy UNIQUE index exists before the fix runs.
        conn = sqlite3.connect(self.db_path)
        unique_tx = False
        for idx in conn.execute("PRAGMA index_list('payments')"):
            if idx[2]:
                cols = [c[2] for c in conn.execute(f"PRAGMA index_info('{idx[1]}')")]
                if cols == ["transaction_code"]:
                    unique_tx = True
        conn.close()
        self.assertTrue(unique_tx, "test setup must start with UNIQUE(transaction_code)")

    def tearDown(self):
        from app.core import db_manager
        db_manager.DBManager.__init__ = self._orig_init
        self.env_patch.stop()
        self.tmp.cleanup()

    def test_same_cheque_number_allowed_for_different_students(self):
        from app.core.payment_manager import record_payment, get_balance

        record_payment(1, 100, "Cheque", "2026-08-09", 1, transaction_code="000123")
        # Different student, same printed cheque number — must succeed.
        record_payment(2, 200, "Cheque", "2026-08-09", 1, transaction_code="000123")

        self.assertEqual(get_balance(1), 900.0)
        self.assertEqual(get_balance(2), 800.0)

        conn = sqlite3.connect(self.db_path)
        for idx in conn.execute("PRAGMA index_list('payments')"):
            if idx[2]:
                cols = [c[2] for c in conn.execute(f"PRAGMA index_info('{idx[1]}')")]
                self.assertNotEqual(cols, ["transaction_code"])
        rows = conn.execute(
            "SELECT student_id, amount, transaction_code FROM payments ORDER BY student_id"
        ).fetchall()
        conn.close()
        self.assertEqual(rows, [(1, 100.0, "000123"), (2, 200.0, "000123")])

    def test_same_student_duplicate_cheque_still_rejected(self):
        from app.core.payment_manager import record_payment

        record_payment(1, 100, "Cheque", "2026-08-09", 1, transaction_code="000123")
        with self.assertRaises(ValueError):
            record_payment(1, 50, "Cheque", "2026-08-09", 1, transaction_code="000123")


if __name__ == "__main__":
    unittest.main()
