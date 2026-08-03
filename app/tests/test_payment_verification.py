import os
import tempfile
import unittest

from app.core.db_manager import DBManager
from app.core.fee_manager import set_fee
from app.core.models import tables
from app.core.payment_manager import get_balance, record_payment
from app.core.student_manager import create_student


class TestPaymentVerification(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._prev_sqlite = os.environ.get("SQLITE_PATH")
        self._prev_db_type = os.environ.get("DB_TYPE")
        os.environ["SQLITE_PATH"] = os.path.join(self._tmpdir.name, "school_fees.db")
        os.environ["DB_TYPE"] = "sqlite"
        with DBManager() as db:
            for table_sql in tables:
                db.execute(table_sql)
            db.execute("INSERT INTO classes (name) VALUES (?)", ("Grade 1",))
            self.class_id = db.fetch_one("SELECT id FROM classes LIMIT 1")[0]
            # Avoid passlib/bcrypt: store a placeholder hash for FK only.
            db.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                ("clerk1", "clerk1@example.com", "unused-hash", "clerk"),
            )
            self.clerk_id = db.fetch_one("SELECT id FROM users WHERE username = ?", ("clerk1",))[0]
        self.student_id = create_student("ADM001", "Test Student", self.class_id, None)
        set_fee(self.student_id, 10000.0)

    def tearDown(self):
        if self._prev_sqlite is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self._prev_sqlite
        if self._prev_db_type is None:
            os.environ.pop("DB_TYPE", None)
        else:
            os.environ["DB_TYPE"] = self._prev_db_type
        self._tmpdir.cleanup()

    def _payment_count(self):
        with DBManager() as db:
            return db.fetch_one("SELECT COUNT(*) FROM payments")[0]

    def test_cash_still_allowed_without_reference(self):
        record_payment(self.student_id, 500.0, "Cash", "2025-08-15", self.clerk_id)
        self.assertEqual(self._payment_count(), 1)
        self.assertEqual(get_balance(self.student_id), 9500.0)

    def test_mpesa_rejects_missing_code(self):
        with self.assertRaises(ValueError) as ctx:
            record_payment(self.student_id, 500.0, "M-Pesa", "2025-08-15", self.clerk_id)
        self.assertIn("M-Pesa code is required", str(ctx.exception))
        self.assertEqual(self._payment_count(), 0)
        self.assertEqual(get_balance(self.student_id), 10000.0)

    def test_mpesa_rejects_blank_code(self):
        with self.assertRaises(ValueError):
            record_payment(
                self.student_id, 500.0, "M-Pesa", "2025-08-15", self.clerk_id, mpesa_code="   "
            )
        self.assertEqual(self._payment_count(), 0)

    def test_mpesa_duplicate_code_blocked(self):
        record_payment(
            self.student_id, 500.0, "M-Pesa", "2025-08-15", self.clerk_id, mpesa_code="QWER1234"
        )
        with self.assertRaises(ValueError) as ctx:
            record_payment(
                self.student_id, 500.0, "M-Pesa", "2025-08-16", self.clerk_id, mpesa_code="QWER1234"
            )
        self.assertIn("already exists", str(ctx.exception))
        self.assertEqual(self._payment_count(), 1)
        self.assertEqual(get_balance(self.student_id), 9500.0)

    def test_bank_and_cheque_require_references(self):
        with self.assertRaises(ValueError) as bank_ctx:
            record_payment(self.student_id, 100.0, "Bank Transfer", "2025-08-15", self.clerk_id)
        self.assertIn("Bank reference is required", str(bank_ctx.exception))

        with self.assertRaises(ValueError) as cheque_ctx:
            record_payment(self.student_id, 100.0, "Cheque", "2025-08-15", self.clerk_id)
        self.assertIn("Cheque number is required", str(cheque_ctx.exception))

        self.assertEqual(self._payment_count(), 0)

    def test_empty_code_no_longer_allows_duplicate_ledger_rows(self):
        """Regression: blank codes used to insert unlimited duplicate payments."""
        with self.assertRaises(ValueError):
            record_payment(self.student_id, 1000.0, "M-Pesa", "2025-08-15", self.clerk_id, mpesa_code=None)
        with self.assertRaises(ValueError):
            record_payment(self.student_id, 1000.0, "M-Pesa", "2025-08-15", self.clerk_id, mpesa_code="")
        self.assertEqual(self._payment_count(), 0)
        self.assertEqual(get_balance(self.student_id), 10000.0)


if __name__ == "__main__":
    unittest.main()
