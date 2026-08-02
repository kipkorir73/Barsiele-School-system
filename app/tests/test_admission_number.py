import os
import tempfile
import unittest

from app.core.db_manager import DBManager
from app.core.models import tables
from app.core.student_manager import (
    create_student,
    get_highest_admission_number,
    _admission_sort_key,
)


class TestAdmissionNumber(unittest.TestCase):
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

    def _increment(self, adm_no: str) -> str:
        """Mirror StudentFormDialog._increment_admission_number."""
        stripped = "".join(ch for ch in adm_no if ch.isdigit())
        if not stripped:
            return "ADM001"
        next_num = str(int(stripped) + 1)
        prefix = adm_no[: adm_no.find(stripped)] if stripped in adm_no else "ADM"
        return f"{prefix}{next_num.zfill(len(stripped))}"

    def test_empty_database_defaults(self):
        self.assertEqual(get_highest_admission_number(), "ADM000")

    def test_sort_key_prefers_longer_numeric_values(self):
        self.assertGreater(_admission_sort_key("ADM1000"), _admission_sort_key("ADM999"))
        self.assertGreater(_admission_sort_key("ADM100"), _admission_sort_key("ADM99"))

    def test_highest_after_digit_length_rollover(self):
        create_student("ADM999", "Student 999", self.class_id, None)
        create_student("ADM1000", "Student 1000", self.class_id, None)

        highest = get_highest_admission_number()
        self.assertEqual(highest, "ADM1000")

        next_adm = self._increment(highest)
        self.assertEqual(next_adm, "ADM1001")

        # Must not collide with an existing admission number.
        with DBManager() as db:
            existing = db.fetch_one(
                "SELECT id FROM students WHERE admission_number = ?", (next_adm,)
            )
        self.assertIsNone(existing)
        create_student(next_adm, "Student 1001", self.class_id, None)

    def test_highest_ignores_lexicographic_trap_with_only_adm999(self):
        create_student("ADM998", "Student 998", self.class_id, None)
        create_student("ADM999", "Student 999", self.class_id, None)
        create_student("ADM1000", "Student 1000", self.class_id, None)
        create_student("ADM1005", "Student 1005", self.class_id, None)

        highest = get_highest_admission_number()
        self.assertEqual(highest, "ADM1005")
        self.assertEqual(self._increment(highest), "ADM1006")


if __name__ == "__main__":
    unittest.main()
