import os
import tempfile
import unittest
from unittest.mock import patch

from app.core import initialize_db


class LockedProbeDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute(self, query):
        if query == "SELECT 1":
            raise Exception("database is locked")


class TestInitializeDb(unittest.TestCase):
    def test_locked_existing_database_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "school_fees.db")
            with open(db_path, "wb") as db_file:
                db_file.write(b"existing data")

            with (
                patch.dict(os.environ, {"SQLITE_PATH": db_path}),
                patch.object(initialize_db, "DBManager", return_value=LockedProbeDB()),
                patch.object(initialize_db, "tables", ["CREATE TABLE IF NOT EXISTS sample (id INTEGER)"]),
                patch.object(initialize_db, "ensure_initial_data") as ensure_initial_data,
                patch.object(initialize_db.os, "remove") as remove,
            ):
                initialize_db.init_db()

            remove.assert_not_called()
            ensure_initial_data.assert_called_once()
            with open(db_path, "rb") as db_file:
                self.assertEqual(db_file.read(), b"existing data")


if __name__ == "__main__":
    unittest.main()
