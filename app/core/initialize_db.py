from .db_manager import DBManager
from .models import tables
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    with DBManager() as db:
        try:
            for table in tables:
                db.execute(table)
                table_name = table.split()[4]  # Extract table name
                logging.info(f"Created/ensured table: {table_name}")
            print("🎉 Database initialized successfully.")
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise

if __name__ == "__main__":
    init_db()