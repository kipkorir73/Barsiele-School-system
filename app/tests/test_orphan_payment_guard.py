"""Regression tests: payments must not attach to deleted/missing students."""

import os
import tempfile
import unittest
from unittest import mock


SCHEMA = """
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
    bus_fee REAL NOT NULL DEFAULT 0.0
);
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
);
CREATE TABLE contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    item TEXT NOT NULL,
    quantity REAL NOT NULL,
    cash_equivalent REAL NOT NULL
);
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class OrphanPaymentGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        self.env = mock.patch.dict(os.environ, {"SQLITE_PATH": self.db_path, "DB_TYPE": "sqlite"})
        self.env.start()

        from app.core.db_manager import DBManager

        with DBManager() as db:
            for stmt in SCHEMA.strip().split(";"):
                if stmt.strip():
                    db.execute(stmt)
            db.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                ("clerk", "clerk@test.local", "x", "clerk"),
            )
            db.execute("INSERT INTO classes (name) VALUES (?)", ("Grade 1",))
            db.execute(
                "INSERT INTO students (admission_number, name, class_id) VALUES (?, ?, ?)",
                ("ADM001", "Temp Student", 1),
            )
            db.execute(
                "INSERT INTO fees (student_id, total_fees, bus_fee) VALUES (?, ?, ?)",
                (1, 10000.0, 0.0),
            )

    def tearDown(self):
        self.env.stop()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_record_payment_rejects_deleted_student(self):
        from app.core.db_manager import DBManager
        from app.core.payment_manager import record_payment

        with DBManager() as db:
            db.execute("DELETE FROM students WHERE id = ?", (1,))

        with self.assertRaises(ValueError) as ctx:
            record_payment(1, 5000.0, "Cash", "2026-08-05", 1)

        self.assertIn("does not exist", str(ctx.exception))

        with DBManager() as db:
            count = db.fetch_one("SELECT COUNT(*) FROM payments")[0]
            joined = db.fetch_one(
                "SELECT COUNT(*) FROM payments p JOIN students s ON s.id = p.student_id"
            )[0]
        self.assertEqual(count, 0)
        self.assertEqual(joined, 0)

    def test_record_payment_allows_existing_student(self):
        from app.core.db_manager import DBManager
        from app.core.payment_manager import record_payment

        payment_id, receipt_no = record_payment(1, 1500.0, "Cash", "2026-08-05", 1)
        self.assertIsNotNone(payment_id)
        self.assertTrue(receipt_no)

        with DBManager() as db:
            row = db.fetch_one("SELECT student_id, amount FROM payments WHERE id = ?", (payment_id,))
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], 1500.0)

    def test_stale_combo_scenario_leaves_no_orphan_ledger(self):
        """Payments tab may still hold a deleted student id; insert must fail closed."""
        from app.core.db_manager import DBManager
        from app.core.payment_manager import record_payment

        stale_student_id = 1
        with DBManager() as db:
            db.execute("DELETE FROM students WHERE id = ?", (stale_student_id,))

        with self.assertRaises(ValueError):
            record_payment(stale_student_id, 5000.0, "M-Pesa", "2026-08-05", 1, mpesa_code="ABC123")

        with DBManager() as db:
            orphan_total = db.fetch_one(
                """
                SELECT COALESCE(SUM(amount), 0) FROM payments p
                WHERE NOT EXISTS (SELECT 1 FROM students s WHERE s.id = p.student_id)
                """
            )[0]
        self.assertEqual(orphan_total, 0.0)


if __name__ == "__main__":
    unittest.main()
