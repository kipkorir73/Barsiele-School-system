import os
import sqlite3
import tempfile
import unittest

from ..core.user_manager import (
    LastAdminError,
    UserHasPaymentsError,
    delete_user,
    update_user,
)


class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "users.db")
        self.original_sqlite_path = os.environ.get("SQLITE_PATH")
        os.environ["SQLITE_PATH"] = self.db_path

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                );
                CREATE TABLE payments (
                    id INTEGER PRIMARY KEY,
                    clerk_id INTEGER NOT NULL
                );
                INSERT INTO users
                    (id, username, email, password, role)
                VALUES
                    (1, 'admin', 'admin@example.com', 'hash', 'admin'),
                    (2, 'clerk', 'clerk@example.com', 'hash', 'clerk');
                """
            )

    def tearDown(self):
        if self.original_sqlite_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self.original_sqlite_path
        self.temp_dir.cleanup()

    def fetch_user(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT username, email, password, role FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

    def test_cannot_delete_last_admin(self):
        with self.assertRaisesRegex(LastAdminError, "last administrator"):
            delete_user(1)

        self.assertIsNotNone(self.fetch_user(1))

    def test_cannot_demote_last_admin(self):
        with self.assertRaisesRegex(LastAdminError, "last administrator"):
            update_user(1, "admin", "admin@example.com", "clerk")

        self.assertEqual(self.fetch_user(1)[3], "admin")

    def test_admin_can_be_demoted_when_another_admin_exists(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO users (id, username, email, password, role)
                VALUES (3, 'backup-admin', 'backup@example.com', 'hash', 'admin')
                """
            )

        update_user(
            1,
            "renamed-admin",
            "renamed@example.com",
            "clerk",
            "new-hash",
        )

        self.assertEqual(
            self.fetch_user(1),
            ("renamed-admin", "renamed@example.com", "new-hash", "clerk"),
        )

    def test_cannot_delete_clerk_with_payment_history(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO payments (id, clerk_id) VALUES (1, 2)")

        with self.assertRaisesRegex(UserHasPaymentsError, "financial history"):
            delete_user(2)

        self.assertIsNotNone(self.fetch_user(2))

    def test_can_delete_clerk_without_payment_history(self):
        delete_user(2)

        self.assertIsNone(self.fetch_user(2))


if __name__ == "__main__":
    unittest.main()
