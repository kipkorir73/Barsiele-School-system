from .db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _fees_has_boarding_fee(db: DBManager) -> bool:
    """Detect if the fees table has the boarding_fee column (legacy DBs may lack it)."""
    try:
        cols = db.fetch_all("PRAGMA table_info(fees)")
        return any(c[1] == 'boarding_fee' for c in cols)
    except Exception:
        return False

def set_class_term_fee(class_id: int, term: int, amount: float):
    with DBManager() as db:
        try:
            db.execute(
                "INSERT OR REPLACE INTO class_fees (class_id, term, amount) VALUES (?, ?, ?)",
                (class_id, term, amount)
            )
            logging.info(f"Set class fee: class={class_id} term={term} amount={amount}")
        except Exception as e:
            logging.error(f"Error setting class term fee: {e}")
            raise

def get_class_term_fee(class_id: int, term: int) -> float:
    with DBManager() as db:
        try:
            row = db.fetch_one("SELECT amount FROM class_fees WHERE class_id = ? AND term = ?", (class_id, term))
            return row[0] if row else 0.0
        except Exception as e:
            logging.error(f"Error getting class term fee: {e}")
            raise

def set_bus_location(name: str, fee_per_term: float):
    with DBManager() as db:
        try:
            db.execute(
                "INSERT OR REPLACE INTO bus_locations (id, name, fee_per_term) VALUES ((SELECT id FROM bus_locations WHERE name = ?), ?, ?)",
                (name, name, fee_per_term)
            )
        except Exception as e:
            logging.error(f"Error setting bus location: {e}")
            raise

def get_bus_locations():
    with DBManager() as db:
        try:
            return db.fetch_all("SELECT id, name, fee_per_term FROM bus_locations ORDER BY name")
        except Exception as e:
            logging.error(f"Error getting bus locations: {e}")
            raise

def set_fee(student_id, total_fees, bus_fee=0.0):
    with DBManager() as db:
        try:
            # SQLite syntax - use INSERT OR REPLACE instead of ON DUPLICATE KEY UPDATE
            if _fees_has_boarding_fee(db):
                db.execute(
                    "INSERT OR REPLACE INTO fees (student_id, total_fees, bus_fee, boarding_fee) VALUES (?, ?, ?, COALESCE((SELECT boarding_fee FROM fees WHERE student_id = ?), 0))",
                    (student_id, total_fees, bus_fee, student_id)
                )
            else:
                db.execute(
                    "INSERT OR REPLACE INTO fees (student_id, total_fees, bus_fee) VALUES (?, ?, ?)",
                    (student_id, total_fees, bus_fee)
                )
            logging.info(f"Fee set for student {student_id}: {total_fees}, Bus: {bus_fee}")
        except Exception as e:
            logging.error(f"Error setting fee for student {student_id}: {e}")
            raise

def get_fee(student_id):
    with DBManager() as db:
        try:
            if _fees_has_boarding_fee(db):
                result = db.fetch_one("SELECT total_fees, bus_fee, COALESCE(boarding_fee, 0) FROM fees WHERE student_id = ?", (student_id,))
                return {'total_fees': result[0] if result else 0.0, 'bus_fee': result[1] if result else 0.0, 'boarding_fee': result[2] if result else 0.0}
            else:
                result = db.fetch_one("SELECT total_fees, bus_fee FROM fees WHERE student_id = ?", (student_id,))
                return {'total_fees': result[0] if result else 0.0, 'bus_fee': result[1] if result else 0.0, 'boarding_fee': 0.0}
        except Exception as e:
            logging.error(f"Error getting fee for student {student_id}: {e}")
            raise

def set_boarding_fee_for_class(class_id: int, amount: float):
    """Set boarding fee for all students in a class (e.g., Grade 7,8,9). Creates fee rows if missing."""
    with DBManager() as db:
        try:
            if not _fees_has_boarding_fee(db):
                logging.warning("Skipping set_boarding_fee_for_class because fees.boarding_fee column does not exist")
                return
            # Ensure fee rows exist
            students = db.fetch_all("SELECT id FROM students WHERE class_id = ?", (class_id,))
            for (sid,) in students:
                db.execute(
                    "INSERT OR IGNORE INTO fees (student_id, total_fees, bus_fee, boarding_fee) VALUES (?, 0, 0, 0)",
                    (sid,)
                )
                db.execute(
                    "UPDATE fees SET boarding_fee = ? WHERE student_id = ?",
                    (amount, sid)
                )
            logging.info(f"Set boarding fee {amount} for class {class_id} ({len(students)} students)")
        except Exception as e:
            logging.error(f"Error setting boarding fee for class {class_id}: {e}")
            raise

def set_food_requirements(class_id: int, maize_kg: float, beans_kg: float, millet_kg: float):
    with DBManager() as db:
        try:
            db.execute(
                "INSERT OR REPLACE INTO food_requirements (class_id, maize_kg, beans_kg, millet_kg) VALUES (?, ?, ?, ?)",
                (class_id, maize_kg, beans_kg, millet_kg)
            )
            logging.info(f"Set food requirements for class {class_id}: maize={maize_kg}, beans={beans_kg}, millet={millet_kg}")
        except Exception as e:
            logging.error(f"Error setting food requirements: {e}")
            raise

def get_food_requirements(class_id: int):
    with DBManager() as db:
        try:
            row = db.fetch_one("SELECT maize_kg, beans_kg, millet_kg FROM food_requirements WHERE class_id = ?", (class_id,))
            if row:
                return {'maize_kg': row[0], 'beans_kg': row[1], 'millet_kg': row[2]}
            return {'maize_kg': 0.0, 'beans_kg': 0.0, 'millet_kg': 0.0}
        except Exception as e:
            logging.error(f"Error getting food requirements for class {class_id}: {e}")
            raise