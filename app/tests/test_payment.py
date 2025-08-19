import unittest
from app.payment_manager import PaymentManager
from app.student_manager import StudentManager
from app.initialize_db import init_db
from decimal import Decimal

class PaymentTestCase(unittest.TestCase):
    def setUp(self):
        init_db()
        self.sm = StudentManager()
        self.sm.add_student('ADMTEST1', 'Test Student', 'Form 1', 'A')
        self.pm = PaymentManager()

    def test_calculation(self):
        total, mr, irr = self.pm.calculate_total(1000, 50, 25)
        expected = Decimal('1000') + Decimal(50) * self.pm.fee_manager.get_conversion_rate('maize') + Decimal(25) * self.pm.fee_manager.get_conversion_rate('millet')
        self.assertAlmostEqual(total, expected)

if __name__ == '__main__':
    unittest.main()
