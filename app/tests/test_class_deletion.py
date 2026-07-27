import os
import tempfile
import unittest

from ..core.class_manager import ClassHasStudentsError, delete_class
from ..core.db_manager import DBManager
from ..core.models import tables
from ..core.student_manager import create_student


class TestClassDeletion(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_db_path = os.environ.get("SQLITE_PATH")
        os.environ["SQLITE_PATH"] = os.path.join(self.temp_dir.name, "school.db")

        with DBManager() as db:
            for table_sql in tables:
                db.execute(table_sql)
            db.execute("INSERT INTO classes (name) VALUES (?)", ("Grade 7",))
            db.execute(
                "INSERT INTO class_fees (class_id, term, amount) VALUES (?, ?, ?)",
                (1, 1, 10000),
            )
            db.execute(
                """
                INSERT INTO food_requirements (class_id, maize_kg, beans_kg, millet_kg)
                VALUES (?, ?, ?, ?)
                """,
                (1, 15, 6, 6),
            )

    def tearDown(self):
        if self.previous_db_path is None:
            os.environ.pop("SQLITE_PATH", None)
        else:
            os.environ["SQLITE_PATH"] = self.previous_db_path
        self.temp_dir.cleanup()

    def test_refuses_to_detach_enrolled_students(self):
        create_student("ADM001", "Annet Chepkemoi", 1, "0700000000")

        with self.assertRaises(ClassHasStudentsError):
            delete_class("Grade 7")

        with DBManager() as db:
            self.assertIsNotNone(
                db.fetch_one("SELECT id FROM classes WHERE name = ?", ("Grade 7",))
            )
            student = db.fetch_one(
                "SELECT class_id FROM students WHERE admission_number = ?",
                ("ADM001",),
            )
            self.assertEqual(student[0], 1)
            # Arrears-style INNER JOIN must still find the student.
            joined = db.fetch_one(
                """
                SELECT s.name, c.name
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.admission_number = ?
                """,
                ("ADM001",),
            )
            self.assertEqual(joined[1], "Grade 7")

    def test_deletes_empty_class_and_scoped_config(self):
        self.assertTrue(delete_class("Grade 7"))

        with DBManager() as db:
            self.assertIsNone(
                db.fetch_one("SELECT id FROM classes WHERE name = ?", ("Grade 7",))
            )
            self.assertIsNone(
                db.fetch_one("SELECT class_id FROM class_fees WHERE class_id = ?", (1,))
            )
            self.assertIsNone(
                db.fetch_one(
                    "SELECT class_id FROM food_requirements WHERE class_id = ?",
                    (1,),
                )
            )

    def test_recreated_class_does_not_claim_orphaned_students(self):
        """Document the failure mode this guard prevents."""
        create_student("ADM002", "Faith Chepkemoi", 1, "0700000001")

        with DBManager() as db:
            # Simulate the old unsafe delete path.
            db.execute("DELETE FROM classes WHERE name = ?", ("Grade 7",))
            db.execute("INSERT INTO classes (name) VALUES (?)", ("Grade 7",))
            new_class = db.fetch_one(
                "SELECT id FROM classes WHERE name = ?", ("Grade 7",)
            )
            student = db.fetch_one(
                "SELECT class_id FROM students WHERE admission_number = ?",
                ("ADM002",),
            )
            self.assertNotEqual(student[0], new_class[0])
            self.assertIsNone(
                db.fetch_one(
                    """
                    SELECT s.id
                    FROM students s
                    JOIN classes c ON s.class_id = c.id
                    WHERE s.admission_number = ?
                    """,
                    ("ADM002",),
                )
            )


if __name__ == "__main__":
    unittest.main()
