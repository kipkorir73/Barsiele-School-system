"""Regression tests for blank fee amounts and class arrears netting."""

import os
import tempfile
import unittest
from unittest import mock


SCHEMA = """
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
    bus_fee REAL NOT NULL DEFAULT 0.0,
    boarding_fee REAL NOT NULL DEFAULT 0.0
);
CREATE TABLE class_fees (
    class_id INTEGER NOT NULL,
    term INTEGER NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (class_id, term)
);
CREATE TABLE bus_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    fee_per_term REAL NOT NULL DEFAULT 0.0
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
"""


class ParseRequiredAmountTests(unittest.TestCase):
    def test_blank_and_whitespace_rejected(self):
        from app.core.fee_manager import parse_required_amount

        for value in ("", "   ", None, "\t"):
            with self.assertRaises(ValueError):
                parse_required_amount(value)

    def test_legacy_blank_coercion_path_blocked(self):
        """The old UI used float(text or 0); blank must not become 0 via the parser."""
        from app.core.fee_manager import parse_required_amount

        with self.assertRaises(ValueError):
            parse_required_amount("")
        # Explicit zero remains allowed for intentional clears after UI confirmation.
        self.assertEqual(parse_required_amount("0"), 0.0)
        self.assertEqual(parse_required_amount("15000"), 15000.0)

    def test_negative_and_invalid_rejected(self):
        from app.core.fee_manager import parse_required_amount

        with self.assertRaises(ValueError):
            parse_required_amount("-1")
        with self.assertRaises(ValueError):
            parse_required_amount("abc")


class BlankBoardingFeeGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        self.env = mock.patch.dict(os.environ, {"SQLITE_PATH": self.db_path, "DB_TYPE": "sqlite"})
        self.env.start()

        from app.core.db_manager import DBManager

        with DBManager() as db:
            for stmt in SCHEMA.strip().split(";"):
                if stmt.strip():
                    db.execute(stmt)
            db.execute("INSERT INTO classes (name) VALUES (?)", ("Grade 7",))
            for i in range(1, 4):
                db.execute(
                    "INSERT INTO students (admission_number, name, class_id) VALUES (?, ?, ?)",
                    (f"ADM{i:03d}", f"Student {i}", 1),
                )
                db.execute(
                    "INSERT INTO fees (student_id, total_fees, bus_fee, boarding_fee) VALUES (?, ?, ?, ?)",
                    (i, 30000.0, 0.0, 15000.0),
                )

    def tearDown(self):
        self.env.stop()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_blank_amount_does_not_wipe_boarding_fees(self):
        from app.core.fee_manager import get_fee, parse_required_amount, set_boarding_fee_for_class

        before = [get_fee(i)["boarding_fee"] for i in range(1, 4)]
        self.assertEqual(before, [15000.0, 15000.0, 15000.0])

        # Simulate admin UI: blank field must fail before calling set_boarding_fee_for_class
        with self.assertRaises(ValueError):
            amount = parse_required_amount("")
            set_boarding_fee_for_class(1, amount)

        after = [get_fee(i)["boarding_fee"] for i in range(1, 4)]
        self.assertEqual(after, [15000.0, 15000.0, 15000.0])

    def test_explicit_zero_still_allowed_when_confirmed(self):
        from app.core.fee_manager import get_fee, parse_required_amount, set_boarding_fee_for_class

        amount = parse_required_amount("0")
        set_boarding_fee_for_class(1, amount)
        self.assertEqual([get_fee(i)["boarding_fee"] for i in range(1, 4)], [0.0, 0.0, 0.0])

    def test_blank_term_fee_does_not_overwrite_config(self):
        from app.core.fee_manager import (
            get_class_term_fee,
            parse_required_amount,
            set_class_term_fee,
        )

        set_class_term_fee(1, 1, 12000.0)
        with self.assertRaises(ValueError):
            amount = parse_required_amount("")
            set_class_term_fee(1, 1, amount)
        self.assertEqual(get_class_term_fee(1, 1), 12000.0)


class ClassArrearsNettingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        self.env = mock.patch.dict(os.environ, {"SQLITE_PATH": self.db_path, "DB_TYPE": "sqlite"})
        self.env.start()

        from app.core.db_manager import DBManager

        with DBManager() as db:
            for stmt in SCHEMA.strip().split(";"):
                if stmt.strip():
                    db.execute(stmt)
            db.execute("INSERT INTO classes (name) VALUES (?)", ("Grade 7",))
            # Student A owes 10000; Student B overpaid by 10000
            db.execute(
                "INSERT INTO students (admission_number, name, class_id) VALUES (?, ?, ?)",
                ("ADM001", "Owes Fees", 1),
            )
            db.execute(
                "INSERT INTO students (admission_number, name, class_id) VALUES (?, ?, ?)",
                ("ADM002", "Overpaid", 1),
            )
            db.execute(
                "INSERT INTO fees (student_id, total_fees, bus_fee, boarding_fee) VALUES (?, ?, ?, ?)",
                (1, 10000.0, 0.0, 0.0),
            )
            db.execute(
                "INSERT INTO fees (student_id, total_fees, bus_fee, boarding_fee) VALUES (?, ?, ?, ?)",
                (2, 10000.0, 0.0, 0.0),
            )
            db.execute(
                "INSERT INTO payments (student_id, amount, method, date, clerk_id, receipt_no) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (2, 20000.0, "Cash", "2025-08-01", 1, "rcpt-over"),
            )

    def tearDown(self):
        self.env.stop()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_class_arrears_ignore_overpayments(self):
        from app.core.payment_manager import get_class_arrears_summary

        rows = {name: arrears for name, _count, arrears in get_class_arrears_summary()}
        # Naive SUM of balances would be 0; correct total arrears is 10000.
        self.assertEqual(rows["Grade 7"], 10000.0)


if __name__ == "__main__":
    unittest.main()
