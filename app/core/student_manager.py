from .db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StudentHasFinancialHistoryError(ValueError):
    """Raised when deleting a student would orphan financial records."""


def create_student(admission_number, name, class_id, guardian_contact, profile_picture=None, bus_location=None):
    with DBManager() as db:
        try:
            db.execute(
                "INSERT INTO students (admission_number, class_id, name, guardian_contact, profile_picture, bus_location) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (admission_number, class_id, name, guardian_contact, profile_picture, bus_location)
            )
            student_id = db.cursor.lastrowid  # SQLite way to get last inserted ID
            logging.info(f"Created student: {name} (ID: {student_id})")
            return student_id
        except Exception as e:
            logging.error(f"Error creating student {name}: {e}")
            raise

def update_student(student_id, **kwargs):
    if not kwargs:
        return
    with DBManager() as db:
        try:
            set_clause = ', '.join(f"{k} = ?" for k in kwargs)
            params = list(kwargs.values()) + [student_id]
            db.execute(f"UPDATE students SET {set_clause} WHERE id = ?", params)
            logging.info(f"Updated student {student_id}")
        except Exception as e:
            logging.error(f"Error updating student {student_id}: {e}")
            raise


def delete_student(student_id):
    """Delete an unused student without orphaning financial history."""
    with DBManager() as db:
        try:
            # Serialize this check with payment/contribution writes so the
            # deletion decision and the delete happen atomically.
            db.cursor.execute("BEGIN IMMEDIATE")
            has_history = db.fetch_one(
                """
                SELECT
                    EXISTS(SELECT 1 FROM payments WHERE student_id = ?)
                    OR EXISTS(SELECT 1 FROM contributions WHERE student_id = ?)
                """,
                (student_id, student_id)
            )
            if has_history and has_history[0]:
                raise StudentHasFinancialHistoryError(
                    "Students with payment or contribution history cannot be deleted."
                )

            # SQLite foreign keys are not enabled by DBManager, so remove the
            # non-historical fee assessment explicitly before the student.
            db.cursor.execute("DELETE FROM fees WHERE student_id = ?", (student_id,))
            db.cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            deleted = db.cursor.rowcount > 0
            if deleted:
                logging.info(f"Deleted unused student {student_id}")
            return deleted
        except StudentHasFinancialHistoryError:
            raise
        except Exception as e:
            logging.error(f"Error deleting student {student_id}: {e}")
            raise


def get_student(student_id):
    with DBManager() as db:
        try:
            return db.fetch_one("SELECT * FROM students WHERE id = ?", (student_id,))
        except Exception as e:
            logging.error(f"Error fetching student {student_id}: {e}")
            raise

def get_all_students():
    with DBManager() as db:
        try:
            return db.fetch_all("""
                SELECT s.id, s.admission_number, s.name, s.class_id, s.guardian_contact, 
                       s.profile_picture, s.bus_location, COALESCE(c.name, 'No Class') as class_name 
                FROM students s 
                LEFT JOIN classes c ON s.class_id = c.id 
                ORDER BY c.name, s.name
            """)
        except Exception as e:
            logging.error(f"Error fetching all students: {e}")
            raise

def search_students(query):
    if not query.strip():
        return get_all_students()
    with DBManager() as db:
        try:
            search_pattern = f"%{query}%"
            return db.fetch_all("""
                SELECT s.id, s.admission_number, s.name, s.class_id, s.guardian_contact, 
                       s.profile_picture, s.bus_location, COALESCE(c.name, 'No Class') as class_name 
                FROM students s 
                LEFT JOIN classes c ON s.class_id = c.id 
                WHERE s.name LIKE ? OR s.admission_number LIKE ? 
                ORDER BY c.name, s.name
            """, (search_pattern, search_pattern))
        except Exception as e:
            logging.error(f"Error searching students for query '{query}': {e}")
            raise

def get_highest_admission_number():
    with DBManager() as db:
        try:
            result = db.fetch_one("SELECT MAX(admission_number) FROM students")
            return result[0] or "ADM000"
        except Exception as e:
            logging.error(f"Error fetching highest admission number: {e}")
            raise