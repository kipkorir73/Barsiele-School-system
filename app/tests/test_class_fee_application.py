"""Class term fees must drive enrolled students' total_fees / arrears."""
import os
import tempfile
import unittest
from pathlib import Path


class ClassFeeApplicationTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmpdir.name) / "school_fees.db")
        os.environ["DB_TYPE"] = "sqlite"
        os.environ["SQLITE_PATH"] = self.db_path

        # DBManager reads SQLITE_PATH at connect time; force a clean import path.
        import app.core.db_manager as db_manager
        import app.core.fee_manager as fee_manager
        import app.core.initialize_db as initialize_db
        import app.core.models as models
        import app.core.payment_manager as payment_manager
        import app.core.student_manager as student_manager

        self.db_manager = db_manager
        self.fee_manager = fee_manager
        self.payment_manager = payment_manager
        self.student_manager = student_manager

        # Create schema without going through ensure_initial_data (passlib issues).
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with db_manager.DBManager() as db:
            for table_sql in models.tables:
                db.execute(table_sql)
            db.execute("INSERT INTO classes (name) VALUES (?)", ("Grade 7",))
            self.class_id = db.cursor.lastrowid

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_annual_fee_sums_all_three_terms(self):
        fm = self.fee_manager
        fm.set_class_term_fee(self.class_id, 1, 10000.0)
        fm.set_class_term_fee(self.class_id, 2, 10000.0)
        fm.set_class_term_fee(self.class_id, 3, 8000.0)
        self.assertEqual(fm.get_class_annual_fee(self.class_id), 28000.0)

    def test_annual_fee_is_not_term1_times_three(self):
        fm = self.fee_manager
        fm.set_class_term_fee(self.class_id, 1, 4500.0)
        fm.set_class_term_fee(self.class_id, 2, 4200.0)
        fm.set_class_term_fee(self.class_id, 3, 4300.0)
        self.assertEqual(fm.get_class_annual_fee(self.class_id), 13000.0)
        self.assertNotEqual(fm.get_class_annual_fee(self.class_id), 4500.0 * 3)

    def test_apply_class_fees_updates_zero_fee_students_and_preserves_bus(self):
        sm = self.student_manager
        fm = self.fee_manager
        pm = self.payment_manager

        sid = sm.create_student("ADM100", "Zero Fee Kid", self.class_id, "0700")
        fm.set_fee(sid, 0.0, 1500.0)

        fm.set_class_term_fee(self.class_id, 1, 10000.0)
        fm.set_class_term_fee(self.class_id, 2, 10000.0)
        fm.set_class_term_fee(self.class_id, 3, 8000.0)

        updated = fm.apply_class_fees_for_class(self.class_id)
        self.assertEqual(updated, 1)

        fee = fm.get_fee(sid)
        self.assertEqual(fee["total_fees"], 28000.0)
        self.assertEqual(fee["bus_fee"], 1500.0)
        self.assertEqual(pm.get_balance(sid), 28000.0 + 1500.0)

    def test_saving_term_schedule_then_apply_fixes_underreported_arrears(self):
        """Reproduce the live failure: students enrolled before term fees were set."""
        sm = self.student_manager
        fm = self.fee_manager
        pm = self.payment_manager

        sid_a = sm.create_student("ADM200", "Early Enrollee A", self.class_id, None)
        sid_b = sm.create_student("ADM201", "Early Enrollee B", self.class_id, None)
        # Mimic add_student when no class_fees exist yet: annual = 0.
        fm.set_fee(sid_a, 0.0, 0.0)
        fm.set_fee(sid_b, 0.0, 2000.0)

        self.assertEqual(pm.get_balance(sid_a), 0.0)
        self.assertEqual(pm.get_balance(sid_b), 2000.0)

        # Admin later configures the class schedule (as Save Term Fee does).
        fm.set_class_term_fee(self.class_id, 1, 10000.0)
        fm.set_class_term_fee(self.class_id, 2, 10000.0)
        fm.set_class_term_fee(self.class_id, 3, 8000.0)
        # Without apply, balances stay wrong — this is the bug.
        self.assertEqual(pm.get_balance(sid_a), 0.0)

        fm.apply_class_fees_for_class(self.class_id)
        self.assertEqual(pm.get_balance(sid_a), 28000.0)
        self.assertEqual(pm.get_balance(sid_b), 28000.0 + 2000.0)


if __name__ == "__main__":
    unittest.main()
