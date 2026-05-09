import unittest
from unittest.mock import patch

from app.core import initialize_db


class TestInitDb(unittest.TestCase):
    def test_locked_database_is_not_removed(self):
        class FakeDBManager:
            enter_count = 0

            def __enter__(self):
                type(self).enter_count += 1
                if type(self).enter_count == 1:
                    raise Exception("database is locked")
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

            def execute(self, query):
                return None

        FakeDBManager.enter_count = 0

        with (
            patch.object(initialize_db, "DBManager", FakeDBManager),
            patch.object(initialize_db, "ensure_initial_data"),
            patch.object(initialize_db.os.path, "exists", return_value=True),
            patch.object(initialize_db.os, "makedirs"),
            patch.object(initialize_db.os, "remove") as remove_db,
            patch.object(initialize_db.time, "sleep"),
        ):
            initialize_db.init_db()

        remove_db.assert_not_called()
        self.assertEqual(FakeDBManager.enter_count, 2)


if __name__ == "__main__":
    unittest.main()
