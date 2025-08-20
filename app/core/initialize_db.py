from .db_manager import DBManager
from .models import tables
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    # Ensure the data directory exists
    db_path = os.getenv('SQLITE_PATH', 'app/data/school_fees.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # If database file exists and is locked, try to handle it
    if os.path.exists(db_path):
        try:
            # Test if we can access the database
            with DBManager() as db:
                db.execute("SELECT 1")
        except Exception as e:
            if "database is locked" in str(e).lower():
                print("Database is locked. Waiting for it to be released...")
                time.sleep(2)
                try:
                    os.remove(db_path)
                    print("Removed locked database file. Creating new one...")
                except:
                    pass
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with DBManager() as db:
                for table_sql in tables:
                    db.execute(table_sql)
                    # Extract table name for logging
                    table_name = table_sql.split()[5] if len(table_sql.split()) > 5 else "unknown"
                    logging.info(f"Created/ensured table: {table_name}")
                
                # Add some initial data if tables are empty
                ensure_initial_data(db)
                
            print("Database initialized successfully.")
            logging.info("Database initialization completed successfully")
            return
            
        except Exception as e:
            logging.error(f"Database initialization error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)

def ensure_initial_data(db):
    """Add initial data if tables are empty"""
    try:
        # Check if we have any users
        result = db.fetch_one("SELECT COUNT(*) FROM users")
        if result[0] == 0:
            # Create default admin user
            from .auth import Auth
            Auth.create_user("admin", "admin@barsiele.ac.ke", "admin123", "admin")
            print("Default admin user created (admin/admin123)")
        
        # Check if we have any classes
        result = db.fetch_one("SELECT COUNT(*) FROM classes")
        if result[0] == 0:
            # Create default classes
            default_classes = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]
            for class_name in default_classes:
                db.execute("INSERT INTO classes (name) VALUES (?)", (class_name,))
            print("Default classes created")
            
    except Exception as e:
        logging.warning(f"Could not add initial data: {e}")
        # Don't raise here as initial data is optional

if __name__ == "__main__":
    init_db()