import unittest
import os
import tempfile
from pathlib import Path

from ..core.initialize_db import init_db
from ..core.payment_manager import record_payment, get_balance
from ..core.fee_manager import set_fee
from ..core.student_manager import create_student

class TestPayment(unittest.TestCase):
    def setUp(self):
        self.original_sqlite_path = os.environ.get("SQLITE_PATH")
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["SQLITE_PATH"] = str(Path(self.temp_dir.name) / "school_fees.db")
        init_db()
        self.student_id = create_student("ADM001", "Test Student", 1, "guardian@example.com")
        set_fee(self.student_id, 1000.0)

    def test_balance(self):
        _, receipt_no = record_payment(self.student_id, 500.0, "cash", "2025-08-15", 1)
        balance = get_balance(self.student_id)
        self.assertEqual(balance, 500.0)

    def tearDown(self):
        if self.original_sqlite_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self.original_sqlite_path
        self.temp_dir.cleanup()

if __name__ == "__main__":
    unittest.main()