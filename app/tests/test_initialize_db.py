import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.core import initialize_db


class TestInitializeDb(unittest.TestCase):
    def test_locked_database_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "school_fees.db")
            with open(db_path, "wb") as db_file:
                db_file.write(b"existing school data")

            class LockedDBManager:
                def __enter__(self):
                    raise sqlite3.OperationalError("database is locked")

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return False

            with patch.dict(os.environ, {"SQLITE_PATH": db_path}), \
                 patch.object(initialize_db, "DBManager", LockedDBManager), \
                 patch.object(initialize_db.time, "sleep", return_value=None), \
                 patch.object(initialize_db.os, "remove") as remove:
                with self.assertRaises(sqlite3.OperationalError):
                    initialize_db.init_db()

            remove.assert_not_called()
            self.assertTrue(os.path.exists(db_path))
            with open(db_path, "rb") as db_file:
                self.assertEqual(db_file.read(), b"existing school data")


if __name__ == "__main__":
    unittest.main()
