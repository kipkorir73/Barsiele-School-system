import os
import tempfile
import unittest

from app.core.db_manager import DBManager
from app.core.fee_manager import set_fee
from app.core.models import tables
from app.core.payment_manager import get_balance, record_payment
from app.core.student_manager import create_student


class TestPayment(unittest.TestCase):
    """Payment tests must never touch the live SQLITE_PATH database."""

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
            # Placeholder hash only — avoids passlib/bcrypt in unit tests.
            db.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                ("clerk1", "clerk1@example.com", "unused-hash", "clerk"),
            )
            self.clerk_id = db.fetch_one("SELECT id FROM users WHERE username = ?", ("clerk1",))[0]

        self.student_id = create_student("ADM001", "Test Student", self.class_id, None)
        set_fee(self.student_id, 1000.0)

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

    def test_balance(self):
        _, receipt_no = record_payment(
            self.student_id, 500.0, "Cash", "2025-08-15", self.clerk_id
        )
        self.assertTrue(receipt_no)
        self.assertEqual(get_balance(self.student_id), 500.0)

    def test_mpesa_case_and_spacing_variants_are_duplicates(self):
        """Regression: mixed-case / spaced codes used to insert a second credit."""
        record_payment(
            self.student_id,
            200.0,
            "M-Pesa",
            "2025-08-15",
            self.clerk_id,
            mpesa_code="Gh wtrye6772",
        )
        with self.assertRaises(ValueError) as ctx:
            record_payment(
                self.student_id,
                200.0,
                "M-Pesa",
                "2025-08-16",
                self.clerk_id,
                mpesa_code="gh wtrye6772",
            )
        self.assertIn("already exists", str(ctx.exception))
        self.assertEqual(self._payment_count(), 1)
        self.assertEqual(get_balance(self.student_id), 800.0)

        with self.assertRaises(ValueError):
            record_payment(
                self.student_id,
                200.0,
                "M-Pesa",
                "2025-08-17",
                self.clerk_id,
                mpesa_code="GHWTRYE6772",
            )
        self.assertEqual(self._payment_count(), 1)

    def test_bank_reference_case_variants_are_duplicates(self):
        record_payment(
            self.student_id,
            100.0,
            "Bank Transfer",
            "2025-08-15",
            self.clerk_id,
            bank_reference="Ref-Abc-01",
        )
        with self.assertRaises(ValueError):
            record_payment(
                self.student_id,
                100.0,
                "Bank Transfer",
                "2025-08-16",
                self.clerk_id,
                bank_reference="ref-abc-01",
            )
        self.assertEqual(self._payment_count(), 1)
        self.assertEqual(get_balance(self.student_id), 900.0)

    def test_canonical_form_is_persisted(self):
        record_payment(
            self.student_id,
            50.0,
            "M-Pesa",
            "2025-08-15",
            self.clerk_id,
            mpesa_code="ab cd 12",
        )
        with DBManager() as db:
            stored = db.fetch_one("SELECT mpesa_code FROM payments WHERE student_id = ?", (self.student_id,))[0]
        self.assertEqual(stored, "ABCD12")

    def test_detects_duplicate_against_legacy_mixed_case_row(self):
        """Existing rows may still have spaced/mixed-case codes from before normalization."""
        with DBManager() as db:
            db.execute(
                "INSERT INTO payments (student_id, amount, method, date, clerk_id, receipt_no, mpesa_code, verified) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (self.student_id, 200.0, "M-Pesa", "2025-08-15", self.clerk_id, "legacy01", "Gh wtrye6772", 1),
            )
        with self.assertRaises(ValueError) as ctx:
            record_payment(
                self.student_id,
                200.0,
                "M-Pesa",
                "2025-08-16",
                self.clerk_id,
                mpesa_code="GHWTRYE6772",
            )
        self.assertIn("already exists", str(ctx.exception))
        self.assertEqual(self._payment_count(), 1)
        self.assertEqual(get_balance(self.student_id), 800.0)


if __name__ == "__main__":
    unittest.main()
