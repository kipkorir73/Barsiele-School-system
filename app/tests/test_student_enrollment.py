"""Regression tests for atomic student + fee enrollment."""
import os
import sqlite3
import tempfile
import unittest


class TestStudentEnrollmentAtomicity(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "enrollment_test.db")
        self._prev_db_type = os.environ.get("DB_TYPE")
        self._prev_sqlite_path = os.environ.get("SQLITE_PATH")
        os.environ["DB_TYPE"] = "sqlite"
        os.environ["SQLITE_PATH"] = self.db_path

        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admission_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                class_id INTEGER,
                guardian_contact TEXT,
                profile_picture TEXT,
                bus_location TEXT
            );
            CREATE TABLE fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL,
                total_fees REAL NOT NULL DEFAULT 0.0,
                bus_fee REAL NOT NULL DEFAULT 0.0
            );
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                date TEXT NOT NULL,
                clerk_id INTEGER NOT NULL,
                receipt_no TEXT UNIQUE NOT NULL
            );
            INSERT INTO classes (id, name) VALUES (1, 'Grade 1');
            """
        )
        conn.commit()
        conn.close()

        import app.core.db_manager as db_manager
        import app.core.student_manager as student_manager
        import app.core.fee_manager as fee_manager
        import app.core.payment_manager as payment_manager
        importlib_reload = __import__("importlib").reload
        importlib_reload(db_manager)
        importlib_reload(student_manager)
        importlib_reload(fee_manager)
        importlib_reload(payment_manager)
        self.student_manager = student_manager
        self.fee_manager = fee_manager
        self.payment_manager = payment_manager

    def tearDown(self):
        if self._prev_db_type is None:
            os.environ.pop("DB_TYPE", None)
        else:
            os.environ["DB_TYPE"] = self._prev_db_type
        if self._prev_sqlite_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self._prev_sqlite_path
        self._tmpdir.cleanup()

    def _counts(self):
        conn = sqlite3.connect(self.db_path)
        students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        fees = conn.execute("SELECT COUNT(*) FROM fees").fetchone()[0]
        conn.close()
        return students, fees

    def test_legacy_create_without_fees_looks_fully_paid(self):
        """create_student commits immediately; without a fee row balance is 0."""
        student_id = self.student_manager.create_student(
            "ADM100", "Orphan Risk", 1, "0700000000"
        )
        # End state after create_student commits and set_fee never lands.
        students, fees = self._counts()
        self.assertEqual(students, 1)
        self.assertEqual(fees, 0)
        # Missing fee row is treated as zero assessment → looks fully paid.
        self.assertEqual(self.payment_manager.get_balance(student_id), 0)

    def test_create_student_with_fees_rolls_back_when_fee_insert_fails(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP TABLE fees")
        conn.commit()
        conn.close()

        with self.assertRaises(sqlite3.OperationalError):
            self.student_manager.create_student_with_fees(
                "ADM101",
                "Atomic Student",
                1,
                "0700000001",
                12000.0,
                1500.0,
            )

        conn = sqlite3.connect(self.db_path)
        students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        conn.close()
        self.assertEqual(students, 0)

    def test_create_student_with_fees_persists_both_rows(self):
        student_id = self.student_manager.create_student_with_fees(
            "ADM102",
            "Complete Student",
            1,
            "0700000002",
            12000.0,
            1500.0,
        )
        students, fees = self._counts()
        self.assertEqual(students, 1)
        self.assertEqual(fees, 1)
        self.assertEqual(self.payment_manager.get_balance(student_id), 13500.0)

        fee = self.fee_manager.get_fee(student_id)
        self.assertEqual(fee["total_fees"], 12000.0)
        self.assertEqual(fee["bus_fee"], 1500.0)


if __name__ == "__main__":
    unittest.main()
