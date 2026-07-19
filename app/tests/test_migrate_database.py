import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from migrate_database import migrate_database


LEGACY_SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'clerk'))
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
    receipt_no TEXT UNIQUE NOT NULL
);
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class MigrateDatabaseTests(unittest.TestCase):
    def test_migrates_previous_schema_without_losing_financial_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_cwd = os.getcwd()
            os.chdir(temp_dir)
            try:
                db_path = Path(temp_dir) / "school_fees.db"
                with sqlite3.connect(db_path) as conn:
                    conn.executescript(LEGACY_SCHEMA)
                    conn.execute(
                        "INSERT INTO users (id, username, password, role) "
                        "VALUES (1, 'admin', 'hashed-password', 'admin')"
                    )
                    conn.execute(
                        "INSERT INTO students (id, admission_number, name) "
                        "VALUES (1, 'ADM001', 'Test Student')"
                    )
                    conn.execute(
                        "INSERT INTO fees (student_id, total_fees, bus_fee) "
                        "VALUES (1, 30000, 6000)"
                    )
                    conn.execute(
                        "INSERT INTO payments "
                        "(id, student_id, amount, method, date, clerk_id, receipt_no) "
                        "VALUES (1, 1, 5000, 'Cash', '2025-08-20', 1, 'receipt1')"
                    )

                self.assertTrue(migrate_database(str(db_path)))

                with sqlite3.connect(db_path) as conn:
                    user_columns = {
                        row[1] for row in conn.execute("PRAGMA table_info(users)")
                    }
                    payment_columns = {
                        row[1] for row in conn.execute("PRAGMA table_info(payments)")
                    }
                    fee_columns = {
                        row[1] for row in conn.execute("PRAGMA table_info(fees)")
                    }

                    self.assertTrue({"email", "created_at"} <= user_columns)
                    self.assertTrue(
                        {
                            "transaction_code",
                            "mpesa_code",
                            "bank_reference",
                            "verified",
                        }
                        <= payment_columns
                    )
                    self.assertIn("boarding_fee", fee_columns)
                    self.assertEqual(
                        conn.execute(
                            "SELECT amount, receipt_no FROM payments WHERE id = 1"
                        ).fetchone(),
                        (5000.0, "receipt1"),
                    )
                    self.assertEqual(
                        conn.execute(
                            "SELECT total_fees, bus_fee, boarding_fee "
                            "FROM fees WHERE student_id = 1"
                        ).fetchone(),
                        (30000.0, 6000.0, 0.0),
                    )
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
