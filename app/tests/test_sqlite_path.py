"""SQLITE_PATH must resolve relative to the project root, not process cwd."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.core.config import PROJECT_ROOT, get_sqlite_path


class TestSqlitePathResolution(unittest.TestCase):
    def setUp(self):
        self._orig_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._orig_cwd)

    def test_relative_env_path_ignores_cwd(self):
        relative = "app/data/school_fees.db"
        expected = (PROJECT_ROOT / relative).resolve()

        with mock.patch.dict(os.environ, {"SQLITE_PATH": relative}, clear=False):
            from_root = Path(get_sqlite_path()).resolve()

            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                from_other_cwd = Path(get_sqlite_path()).resolve()

        self.assertEqual(from_root, expected)
        self.assertEqual(from_other_cwd, expected)
        self.assertTrue(from_other_cwd.is_absolute())

    def test_absolute_env_path_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            absolute = str((Path(tmp) / "custom.db").resolve())
            with mock.patch.dict(os.environ, {"SQLITE_PATH": absolute}, clear=False):
                self.assertEqual(Path(get_sqlite_path()).resolve(), Path(absolute))

    def test_db_manager_opens_same_file_from_other_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_file = str((Path(tmp) / "fee.db").resolve())
            with mock.patch.dict(os.environ, {"SQLITE_PATH": db_file, "DB_TYPE": "sqlite"}, clear=False):
                from app.core.db_manager import DBManager

                with DBManager() as db:
                    db.execute(
                        "CREATE TABLE IF NOT EXISTS probe (id INTEGER PRIMARY KEY, note TEXT)"
                    )
                    db.execute("DELETE FROM probe")
                    db.execute("INSERT INTO probe (note) VALUES (?)", ("from-root",))

                other = Path(tmp) / "elsewhere"
                other.mkdir()
                os.chdir(other)
                with DBManager() as db:
                    row = db.fetch_one("SELECT note FROM probe")
                    self.assertIsNotNone(row)
                    self.assertEqual(row[0], "from-root")


if __name__ == "__main__":
    unittest.main()
