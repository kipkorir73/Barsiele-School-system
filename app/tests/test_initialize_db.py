import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.core import initialize_db


class TestInitializeDb(unittest.TestCase):
    def setUp(self):
        self.original_sqlite_path = os.environ.get("SQLITE_PATH")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "school_fees.db")
        os.environ["SQLITE_PATH"] = self.db_path

    def tearDown(self):
        if self.original_sqlite_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self.original_sqlite_path
        self.temp_dir.cleanup()

    def test_locked_database_is_not_deleted(self):
        Path(self.db_path).write_bytes(b"existing database contents")

        with mock.patch("app.core.initialize_db.DBManager", side_effect=Exception("database is locked")), \
             mock.patch("app.core.initialize_db.time.sleep"), \
             mock.patch("app.core.initialize_db.os.remove") as remove:
            with self.assertRaises(Exception):
                initialize_db.init_db()

        remove.assert_not_called()
        self.assertEqual(Path(self.db_path).read_bytes(), b"existing database contents")

    def test_legacy_schema_gets_additive_migrations(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            );
            INSERT INTO users (username, password, role) VALUES ('admin', 'hash', 'admin');

            CREATE TABLE classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            INSERT INTO classes (name) VALUES ('Grade 1');

            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admission_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                class_id INTEGER,
                guardian_contact TEXT,
                profile_picture TEXT,
                bus_location TEXT
            );
            INSERT INTO students (admission_number, name, class_id) VALUES ('ADM001', 'Test Student', 1);

            CREATE TABLE fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL,
                total_fees REAL NOT NULL DEFAULT 0.0,
                bus_fee REAL NOT NULL DEFAULT 0.0
            );
            INSERT INTO fees (student_id, total_fees, bus_fee) VALUES (1, 1000, 100);

            CREATE TABLE payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                date TEXT NOT NULL,
                clerk_id INTEGER NOT NULL,
                receipt_no TEXT UNIQUE NOT NULL
            );
            INSERT INTO payments (student_id, amount, method, date, clerk_id, receipt_no)
            VALUES (1, 250, 'Cash', '2025-08-20', 1, 'R001');

            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
        conn.close()

        initialize_db.init_db()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        user_columns = {column[1] for column in cursor.fetchall()}
        cursor.execute("PRAGMA table_info(fees)")
        fee_columns = {column[1] for column in cursor.fetchall()}
        cursor.execute("PRAGMA table_info(payments)")
        payment_columns = {column[1] for column in cursor.fetchall()}
        cursor.execute("PRAGMA table_info(audit_logs)")
        audit_columns = {column[1] for column in cursor.fetchall()}

        self.assertIn("email", user_columns)
        self.assertIn("created_at", user_columns)
        self.assertIn("boarding_fee", fee_columns)
        self.assertTrue({"transaction_code", "bank_reference", "mpesa_code", "verified"}.issubset(payment_columns))
        self.assertTrue({"ip_address", "user_agent"}.issubset(audit_columns))

        cursor.execute("SELECT username, email FROM users WHERE id = 1")
        self.assertEqual(cursor.fetchone(), ("admin", "admin@barsiele.ac.ke"))
        cursor.execute("SELECT total_fees, bus_fee, boarding_fee FROM fees WHERE student_id = 1")
        self.assertEqual(cursor.fetchone(), (1000.0, 100.0, 0.0))
        cursor.execute("SELECT COUNT(*) FROM payments WHERE receipt_no = 'R001'")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()


if __name__ == "__main__":
    unittest.main()
