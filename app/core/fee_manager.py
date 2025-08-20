from .db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            result = db.fetch_one("SELECT total_fees, bus_fee FROM fees WHERE student_id = ?", (student_id,))
            return {'total_fees': result[0] if result else 0.0, 'bus_fee': result[1] if result else 0.0}
        except Exception as e:
            logging.error(f"Error getting fee for student {student_id}: {e}")
            raise