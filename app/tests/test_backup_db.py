import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.scripts.backup_db import backup


class TestDatabaseBackup(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)

    def tearDown(self):
        os.chdir(self.previous_cwd)
        self.temp_dir.cleanup()

    @staticmethod
    def create_database(path, marker):
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE backup_marker (value TEXT NOT NULL)")
            connection.execute(
                "INSERT INTO backup_marker (value) VALUES (?)",
                (marker,),
            )

    def test_backup_uses_configured_live_database(self):
        live_database = Path("app/data/school_fees.db")
        stale_database = Path("data/school_fees.db")
        self.create_database(live_database, "live")
        self.create_database(stale_database, "stale")

        with patch.dict(
            os.environ,
            {"SQLITE_PATH": str(live_database)},
            clear=False,
        ):
            backup_path = backup()

        self.assertIsNotNone(backup_path)
        with sqlite3.connect(backup_path) as connection:
            marker = connection.execute(
                "SELECT value FROM backup_marker"
            ).fetchone()[0]

        self.assertEqual(marker, "live")


if __name__ == "__main__":
    unittest.main()
