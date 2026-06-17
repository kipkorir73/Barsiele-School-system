import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.core.auth import Auth
from app.core.initialize_db import init_db


class TestInitializeDb(unittest.TestCase):
    def setUp(self):
        self._old_sqlite_path = os.environ.get("SQLITE_PATH")

    def tearDown(self):
        if self._old_sqlite_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self._old_sqlite_path

    def test_init_db_does_not_remove_locked_database(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "school_fees.db")
            with open(db_path, "wb") as db_file:
                db_file.write(b"existing data")
            os.environ["SQLITE_PATH"] = db_path

            class LockedDB:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return False

                def execute(self, query, params=None):
                    raise sqlite3.OperationalError("database is locked")

            with patch("app.core.initialize_db.DBManager", return_value=LockedDB()), \
                 patch("app.core.initialize_db.time.sleep", return_value=None), \
                 patch("app.core.initialize_db.os.remove") as remove:
                with self.assertRaises(sqlite3.OperationalError):
                    init_db()

            remove.assert_not_called()
            self.assertTrue(os.path.exists(db_path))

    def test_init_db_migrates_legacy_schema_required_by_login_and_payments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "school_fees.db")
            os.environ["SQLITE_PATH"] = db_path

            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", Auth.hash_password("secret"), "admin")
            )
            conn.execute(
                """
                CREATE TABLE payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    method TEXT NOT NULL,
                    date TEXT NOT NULL,
                    clerk_id INTEGER NOT NULL,
                    receipt_no TEXT UNIQUE NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER UNIQUE NOT NULL,
                    total_fees REAL NOT NULL DEFAULT 0.0,
                    bus_fee REAL NOT NULL DEFAULT 0.0
                )
                """
            )
            conn.commit()
            conn.close()

            init_db()

            conn = sqlite3.connect(db_path)
            try:
                users_columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
                payments_columns = {row[1] for row in conn.execute("PRAGMA table_info(payments)")}
                fees_columns = {row[1] for row in conn.execute("PRAGMA table_info(fees)")}
                email = conn.execute("SELECT email FROM users WHERE username = ?", ("admin",)).fetchone()[0]
            finally:
                conn.close()

            self.assertIn("email", users_columns)
            self.assertIn("created_at", users_columns)
            self.assertEqual(email, "admin@barsiele.ac.ke")
            self.assertIn("transaction_code", payments_columns)
            self.assertIn("bank_reference", payments_columns)
            self.assertIn("mpesa_code", payments_columns)
            self.assertIn("verified", payments_columns)
            self.assertIn("boarding_fee", fees_columns)

            user = Auth.authenticate("admin", "secret")
            self.assertIsNotNone(user)
            self.assertEqual(user["username"], "admin")


if __name__ == "__main__":
    unittest.main()
