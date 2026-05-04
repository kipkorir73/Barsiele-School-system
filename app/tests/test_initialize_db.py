import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from app.core import initialize_db


class LockedDBManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute(self, query, params=None):
        raise sqlite3.OperationalError("database is locked")


class TestInitializeDB(unittest.TestCase):
    def test_locked_database_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "school_fees.db")
            with open(db_path, "wb") as db_file:
                db_file.write(b"existing database contents")

            with mock.patch.dict(os.environ, {"SQLITE_PATH": db_path}), \
                 mock.patch.object(initialize_db, "DBManager", LockedDBManager), \
                 mock.patch.object(initialize_db.time, "sleep"), \
                 mock.patch.object(initialize_db.os, "remove") as remove_mock:
                with self.assertRaises(sqlite3.OperationalError):
                    initialize_db.init_db()

            remove_mock.assert_not_called()
            self.assertTrue(os.path.exists(db_path))
            with open(db_path, "rb") as db_file:
                self.assertEqual(db_file.read(), b"existing database contents")


if __name__ == "__main__":
    unittest.main()
