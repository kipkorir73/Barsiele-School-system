from .db_manager import DBManager
from .models import tables
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _is_locked_error(error):
    return "database is locked" in str(error).lower()

def _table_exists(db, table_name):
    row = db.fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
    return row is not None

def _column_names(db, table_name):
    if not _table_exists(db, table_name):
        return set()
    return {column[1] for column in db.fetch_all(f"PRAGMA table_info({table_name})")}

def _add_column_if_missing(db, table_name, column_name, column_sql):
    columns = _column_names(db, table_name)
    if column_name not in columns:
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")
        logging.info(f"Added missing column {table_name}.{column_name}")

def ensure_schema_migrations(db):
    """Apply safe additive migrations for databases created by older app versions."""
    if _table_exists(db, "users"):
        _add_column_if_missing(db, "users", "email", "email TEXT")
        db.execute("UPDATE users SET email = username || '@barsiele.ac.ke' WHERE email IS NULL OR email = ''")
        _add_column_if_missing(db, "users", "created_at", "created_at TEXT")
        db.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL OR created_at = ''")

    if _table_exists(db, "fees"):
        _add_column_if_missing(db, "fees", "boarding_fee", "boarding_fee REAL NOT NULL DEFAULT 0.0")

    if _table_exists(db, "payments"):
        _add_column_if_missing(db, "payments", "transaction_code", "transaction_code TEXT")
        _add_column_if_missing(db, "payments", "bank_reference", "bank_reference TEXT")
        _add_column_if_missing(db, "payments", "mpesa_code", "mpesa_code TEXT")
        _add_column_if_missing(db, "payments", "verified", "verified BOOLEAN DEFAULT 0")

    if _table_exists(db, "audit_logs"):
        _add_column_if_missing(db, "audit_logs", "ip_address", "ip_address TEXT")
        _add_column_if_missing(db, "audit_logs", "user_agent", "user_agent TEXT")

def init_db():
    # Ensure the data directory exists
    db_path = os.getenv('SQLITE_PATH', 'app/data/school_fees.db')
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    # If database file exists and is locked, try to handle it
    if os.path.exists(db_path):
        try:
            # Test if we can access the database
            with DBManager() as db:
                db.execute("SELECT 1")
        except Exception as e:
            if _is_locked_error(e):
                logging.warning("Database is locked during startup check; will retry without deleting it")
                time.sleep(2)
            else:
                raise
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with DBManager() as db:
                for table_sql in tables:
                    db.execute(table_sql)
                    # Extract table name for logging
                    table_name = table_sql.split()[5] if len(table_sql.split()) > 5 else "unknown"
                    logging.info(f"Created/ensured table: {table_name}")

                ensure_schema_migrations(db)
                
                # Add some initial data if tables are empty
                ensure_initial_data(db)
                
            print("Database initialized successfully.")
            logging.info("Database initialization completed successfully")
            return
            
        except Exception as e:
            logging.error(f"Database initialization error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
            if _is_locked_error(e):
                logging.warning("Database is locked during initialization; retrying without deleting it")
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