import unittest

from ..core.fee_manager import annual_bus_fee


class TestAnnualBusFee(unittest.TestCase):
    def test_converts_per_term_fee_to_three_term_charge(self):
        self.assertEqual(annual_bus_fee(2000), 6000.0)

    def test_preserves_fractional_fee_values(self):
        self.assertEqual(annual_bus_fee(1250.50), 3751.50)


if __name__ == "__main__":
    unittest.main()
