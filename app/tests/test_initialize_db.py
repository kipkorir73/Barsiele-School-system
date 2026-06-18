import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


class TestInitializeDb(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "school_fees.db"
        self._old_env = {
            key: os.environ.get(key)
            for key in (
                "SQLITE_PATH",
                "SQLITE_TIMEOUT",
                "DB_INIT_MAX_RETRIES",
                "DB_INIT_RETRY_DELAY",
            )
        }
        os.environ["SQLITE_PATH"] = str(self.db_path)
        os.environ["SQLITE_TIMEOUT"] = "0.05"
        os.environ["DB_INIT_MAX_RETRIES"] = "1"
        os.environ["DB_INIT_RETRY_DELAY"] = "0"

    def tearDown(self):
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp_dir.cleanup()

    def test_locked_database_is_not_deleted(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE keep_me (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO keep_me (id) VALUES (1)")
        conn.commit()

        lock_conn = sqlite3.connect(self.db_path)
        lock_conn.execute("BEGIN EXCLUSIVE")
        try:
            from app.core.initialize_db import init_db

            with self.assertRaises(sqlite3.OperationalError):
                init_db()
        finally:
            lock_conn.rollback()
            lock_conn.close()

        self.assertTrue(self.db_path.exists())
        saved = sqlite3.connect(self.db_path)
        try:
            count = saved.execute("SELECT COUNT(*) FROM keep_me").fetchone()[0]
        finally:
            saved.close()
        self.assertEqual(count, 1)

    def test_legacy_database_is_migrated_during_startup(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
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
            CREATE TABLE receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER UNIQUE NOT NULL,
                receipt_no TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL
            );
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users (id, username, password, role)
            VALUES (1, 'admin', 'not-used-by-this-test', 'admin');
            INSERT INTO classes (id, name) VALUES (1, 'Grade 1');
            INSERT INTO students (id, admission_number, name, class_id, guardian_contact)
            VALUES (1, 'ADM001', 'Test Student', 1, 'guardian@example.com');
            INSERT INTO fees (student_id, total_fees, bus_fee)
            VALUES (1, 1000.0, 0.0);
            """
        )
        conn.commit()
        conn.close()

        from app.core.initialize_db import init_db
        from app.core.payment_manager import record_payment

        init_db()

        migrated = sqlite3.connect(self.db_path)
        try:
            user_columns = {
                row[1] for row in migrated.execute("PRAGMA table_info(users)").fetchall()
            }
            payment_columns = {
                row[1] for row in migrated.execute("PRAGMA table_info(payments)").fetchall()
            }
            fee_columns = {
                row[1] for row in migrated.execute("PRAGMA table_info(fees)").fetchall()
            }
            self.assertIn("email", user_columns)
            self.assertIn("created_at", user_columns)
            self.assertIn("transaction_code", payment_columns)
            self.assertIn("mpesa_code", payment_columns)
            self.assertIn("bank_reference", payment_columns)
            self.assertIn("verified", payment_columns)
            self.assertIn("boarding_fee", fee_columns)

            row = migrated.execute(
                "SELECT email FROM users WHERE email = ? OR username = ?",
                ("admin", "admin"),
            ).fetchone()
            self.assertEqual(row[0], "admin@barsiele.ac.ke")
        finally:
            migrated.close()

        payment_id, receipt_no = record_payment(
            1,
            250.0,
            "cash",
            "2026-06-18",
            1,
            transaction_code="TXN-001",
        )
        self.assertIsInstance(payment_id, int)
        self.assertTrue(receipt_no)

        paid = sqlite3.connect(self.db_path)
        try:
            payment = paid.execute(
                "SELECT transaction_code, verified FROM payments WHERE id = ?",
                (payment_id,),
            ).fetchone()
        finally:
            paid.close()
        self.assertEqual(payment, ("TXN-001", 1))

    def test_fresh_database_creates_loginable_admin(self):
        from app.core.auth import Auth
        from app.core.initialize_db import init_db

        init_db()

        admin = Auth.authenticate("admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["username"], "admin")
        self.assertEqual(admin["email"], "admin@barsiele.ac.ke")
        self.assertFalse(Auth.authenticate("admin", "wrong-password"))


if __name__ == "__main__":
    unittest.main()
