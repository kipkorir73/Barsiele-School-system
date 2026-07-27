from .db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ClassHasStudentsError(ValueError):
    """Raised when deleting a class would detach enrolled students."""


def delete_class(class_name: str) -> bool:
    """Delete an unused class without orphaning enrolled students.

    SQLite foreign keys are not enabled by DBManager, so ``DELETE FROM classes``
    leaves ``students.class_id`` pointing at a missing row. Arrears and report
    queries that ``JOIN classes`` then permanently hide those students, and
    recreating the same class name allocates a new id that does not reconnect
    them.
    """
    if not class_name or not class_name.strip():
        raise ValueError("Class name is required")

    class_name = class_name.strip()
    with DBManager() as db:
        try:
            # Serialize the enrollment check with the delete.
            db.cursor.execute("BEGIN IMMEDIATE")
            class_row = db.fetch_one(
                "SELECT id FROM classes WHERE name = ?",
                (class_name,),
            )
            if not class_row:
                return False

            class_id = class_row[0]
            enrolled = db.fetch_one(
                "SELECT COUNT(*) FROM students WHERE class_id = ?",
                (class_id,),
            )
            enrolled_count = enrolled[0] if enrolled else 0
            if enrolled_count:
                raise ClassHasStudentsError(
                    f"Cannot delete '{class_name}' while {enrolled_count} student(s) "
                    "are still enrolled. Reassign or remove those students first."
                )

            # Clean class-scoped config that would otherwise reference the
            # deleted id (foreign keys are not enforced).
            tables = {
                row[0]
                for row in db.fetch_all(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if "class_fees" in tables:
                db.cursor.execute(
                    "DELETE FROM class_fees WHERE class_id = ?",
                    (class_id,),
                )
            if "food_requirements" in tables:
                db.cursor.execute(
                    "DELETE FROM food_requirements WHERE class_id = ?",
                    (class_id,),
                )
            db.cursor.execute("DELETE FROM classes WHERE id = ?", (class_id,))
            deleted = db.cursor.rowcount > 0
            if deleted:
                logging.info(f"Deleted unused class {class_name} (id={class_id})")
            return deleted
        except ClassHasStudentsError:
            raise
        except Exception as e:
            logging.error(f"Error deleting class {class_name}: {e}")
            raise
