import unittest
from ..core.db_manager import DBManager
from ..core.payment_manager import record_payment, get_balance
from ..core.fee_manager import set_fee
from ..core.student_manager import create_student

class TestPayment(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        self.db.execute("DELETE FROM payments")
        self.db.execute("DELETE FROM fees")
        self.db.execute("DELETE FROM students")
        self.student_id = create_student("ADM001", "Test Student", 1, "guardian@example.com")
        set_fee(self.student_id, 1000.0)

    def test_balance(self):
        _, receipt_no = record_payment(self.student_id, 500.0, "cash", "2025-08-15", 1)
        balance = get_balance(self.student_id)
        self.assertEqual(balance, 500.0)

    def tearDown(self):
        self.db.close()

if __name__ == "__main__":
    unittest.main()