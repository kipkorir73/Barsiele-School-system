import os
import tempfile
import unittest

from ..core.db_manager import DBManager
from ..core.models import tables
from ..core.student_manager import (
    StudentHasFinancialHistoryError,
    create_student,
    delete_student,
)


class TestStudentDeletion(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_db_path = os.environ.get("SQLITE_PATH")
        os.environ["SQLITE_PATH"] = os.path.join(self.temp_dir.name, "school.db")

        with DBManager() as db:
            for table_sql in tables:
                db.execute(table_sql)
            db.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                ("clerk", "clerk@example.com", "unused", "clerk"),
            )

    def tearDown(self):
        if self.previous_db_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self.previous_db_path
        self.temp_dir.cleanup()

    def create_student_with_fee(self, admission_number):
        student_id = create_student(
            admission_number, "Test Student", None, "guardian@example.com"
        )
        with DBManager() as db:
            db.execute(
                "INSERT INTO fees (student_id, total_fees) VALUES (?, ?)",
                (student_id, 1000),
            )
        return student_id

    def test_refuses_to_orphan_payment_history(self):
        student_id = self.create_student_with_fee("ADM001")
        with DBManager() as db:
            clerk_id = db.fetch_one(
                "SELECT id FROM users WHERE username = ?", ("clerk",)
            )[0]
            db.execute(
                """
                INSERT INTO payments
                    (student_id, amount, method, date, clerk_id, receipt_no)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (student_id, 500, "Cash", "2026-07-20", clerk_id, "receipt-1"),
            )

        with self.assertRaises(StudentHasFinancialHistoryError):
            delete_student(student_id)

        with DBManager() as db:
            self.assertIsNotNone(
                db.fetch_one("SELECT id FROM students WHERE id = ?", (student_id,))
            )
            self.assertIsNotNone(
                db.fetch_one(
                    "SELECT id FROM payments WHERE student_id = ?", (student_id,)
                )
            )

    def test_refuses_to_orphan_contribution_history(self):
        student_id = self.create_student_with_fee("ADM002")
        with DBManager() as db:
            db.execute(
                """
                INSERT INTO contributions
                    (student_id, item, quantity, cash_equivalent)
                VALUES (?, ?, ?, ?)
                """,
                (student_id, "Maize", 10, 500),
            )

        with self.assertRaises(StudentHasFinancialHistoryError):
            delete_student(student_id)

        with DBManager() as db:
            self.assertIsNotNone(
                db.fetch_one("SELECT id FROM students WHERE id = ?", (student_id,))
            )

    def test_deletes_unused_student_and_fee_assessment(self):
        student_id = self.create_student_with_fee("ADM003")

        self.assertTrue(delete_student(student_id))

        with DBManager() as db:
            self.assertIsNone(
                db.fetch_one("SELECT id FROM students WHERE id = ?", (student_id,))
            )
            self.assertIsNone(
                db.fetch_one("SELECT id FROM fees WHERE student_id = ?", (student_id,))
            )


if __name__ == "__main__":
    unittest.main()
