import os
import tempfile
import unittest
from unittest.mock import patch

from app.core import initialize_db
from app.core.auth import Auth
from app.core.db_manager import DBManager


class TestInitializeDb(unittest.TestCase):
    def test_locked_database_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "school_fees.db")
            original_contents = b"existing production data"
            with open(db_path, "wb") as db_file:
                db_file.write(original_contents)

            with patch.dict(os.environ, {"SQLITE_PATH": db_path}):
                with patch.object(initialize_db, "DBManager", side_effect=Exception("database is locked")):
                    with patch.object(initialize_db.time, "sleep"):
                        with self.assertRaisesRegex(Exception, "database is locked"):
                            initialize_db.init_db()

            self.assertTrue(os.path.exists(db_path))
            with open(db_path, "rb") as db_file:
                self.assertEqual(db_file.read(), original_contents)

    def test_fresh_database_gets_default_login_and_classes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "school_fees.db")

            with patch.dict(os.environ, {"SQLITE_PATH": db_path}):
                initialize_db.init_db()

                with DBManager() as db:
                    user = db.fetch_one(
                        "SELECT username, email, role FROM users WHERE username = ?",
                        ("admin",),
                    )
                    class_count = db.fetch_one("SELECT COUNT(*) FROM classes")[0]

                self.assertIsNotNone(user)
                self.assertEqual(user["email"], "admin@barsiele.ac.ke")
                self.assertEqual(user["role"], "admin")
                self.assertEqual(class_count, 8)
                self.assertIsNotNone(Auth.authenticate("admin", "admin123"))


if __name__ == "__main__":
    unittest.main()
