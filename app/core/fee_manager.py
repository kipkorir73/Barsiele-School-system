from .db_manager import DBManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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