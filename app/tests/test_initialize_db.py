import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from app.core.initialize_db import init_db


class TestInitializeDb(unittest.TestCase):
    def test_locked_database_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "school_fees.db")
            sqlite3.connect(db_path).close()

            def locked_db(*args, **kwargs):
                raise sqlite3.OperationalError("database is locked")

            with mock.patch.dict(os.environ, {"SQLITE_PATH": db_path}), \
                 mock.patch("app.core.initialize_db.DBManager", side_effect=locked_db), \
                 mock.patch("app.core.initialize_db.time.sleep", return_value=None):
                with self.assertRaises(sqlite3.OperationalError):
                    init_db()

            self.assertTrue(os.path.exists(db_path))


if __name__ == "__main__":
    unittest.main()
