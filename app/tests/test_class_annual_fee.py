import os
import tempfile
import unittest
from unittest.mock import patch

from ..core.db_manager import DBManager
from ..core.fee_manager import get_class_annual_fee, set_class_term_fee


class TestClassAnnualFee(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "school_fees.db")
        self.env = patch.dict(os.environ, {"SQLITE_PATH": self.db_path})
        self.env.start()

        with DBManager() as db:
            db.execute(
                """
                CREATE TABLE class_fees (
                    class_id INTEGER NOT NULL,
                    term INTEGER NOT NULL,
                    amount REAL NOT NULL DEFAULT 0.0,
                    PRIMARY KEY (class_id, term)
                )
                """
            )

    def tearDown(self):
        self.env.stop()
        self.temp_dir.cleanup()

    def test_sums_each_configured_term_instead_of_repeating_term_one(self):
        set_class_term_fee(1, 1, 10000)
        set_class_term_fee(1, 2, 15000)
        set_class_term_fee(1, 3, 20000)

        self.assertEqual(get_class_annual_fee(1), 45000)


if __name__ == "__main__":
    unittest.main()
