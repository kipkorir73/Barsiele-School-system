import os
import tempfile
import unittest
from unittest.mock import patch

from app.core import initialize_db


class LockedDBManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute(self, query):
        raise Exception("database is locked")


class TestInitializeDb(unittest.TestCase):
    def test_locked_database_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "school_fees.db")
            original_contents = b"existing school data"
            with open(db_path, "wb") as db_file:
                db_file.write(original_contents)

            with patch.dict(os.environ, {"SQLITE_PATH": db_path}), \
                 patch.object(initialize_db, "DBManager", LockedDBManager), \
                 patch.object(initialize_db.time, "sleep", return_value=None):
                with self.assertRaises(Exception):
                    initialize_db.init_db()

            self.assertTrue(os.path.exists(db_path))
            with open(db_path, "rb") as db_file:
                self.assertEqual(db_file.read(), original_contents)


if __name__ == "__main__":
    unittest.main()
