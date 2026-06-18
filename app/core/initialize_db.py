from .db_manager import DBManager
from .models import tables
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    # Ensure the data directory exists
    db_path = os.getenv('SQLITE_PATH', 'app/data/school_fees.db')
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    max_retries = int(os.getenv('DB_INIT_MAX_RETRIES', '3'))
    retry_delay = float(os.getenv('DB_INIT_RETRY_DELAY', '1'))
    for attempt in range(max_retries):
        try:
            with DBManager() as db:
                for table_sql in tables:
                    db.execute(table_sql)
                    # Extract table name for logging
                    table_name = table_sql.split()[5] if len(table_sql.split()) > 5 else "unknown"
                    logging.info(f"Created/ensured table: {table_name}")

                migrate_legacy_schema(db)
                
                # Add some initial data if tables are empty
                ensure_initial_data(db)
                
            print("Database initialized successfully.")
            logging.info("Database initialization completed successfully")
            return
            
        except Exception as e:
            logging.error(f"Database initialization error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
            if "database is locked" in str(e).lower():
                print("Database is locked. Waiting for it to be released...")
            time.sleep(retry_delay)

def table_exists(db, table_name):
    result = db.fetch_one(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,)
    )
    return result is not None

def column_names(db, table_name):
    if not table_exists(db, table_name):
        return set()
    return {row[1] for row in db.fetch_all(f"PRAGMA table_info({table_name})")}

def add_column_if_missing(db, table_name, column_name, column_definition):
    if column_name not in column_names(db, table_name):
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")
        logging.info(f"Added legacy column {table_name}.{column_name}")

def create_unique_index_if_possible(db, index_name, table_name, column_name):
    try:
        db.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} "
            f"ON {table_name}({column_name}) WHERE {column_name} IS NOT NULL"
        )
    except Exception as e:
        logging.warning(f"Could not create unique index {index_name}: {e}")

def migrate_legacy_schema(db):
    """Bring existing SQLite databases up to the columns used by current code."""
    if table_exists(db, 'users'):
        users_columns = column_names(db, 'users')
        if 'email' not in users_columns:
            db.execute("ALTER TABLE users ADD COLUMN email TEXT")
            db.execute("UPDATE users SET email = username || '@barsiele.ac.ke' WHERE email IS NULL")
            logging.info("Added legacy column users.email")
        if 'created_at' not in users_columns:
            db.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
            db.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            logging.info("Added legacy column users.created_at")
        create_unique_index_if_possible(db, 'idx_users_email_unique', 'users', 'email')

    if table_exists(db, 'students'):
        add_column_if_missing(db, 'students', 'class_id', 'class_id INTEGER')
        add_column_if_missing(db, 'students', 'guardian_contact', 'guardian_contact TEXT')
        add_column_if_missing(db, 'students', 'profile_picture', 'profile_picture TEXT')
        add_column_if_missing(db, 'students', 'bus_location', 'bus_location TEXT')

    if table_exists(db, 'fees'):
        add_column_if_missing(db, 'fees', 'bus_fee', 'bus_fee REAL NOT NULL DEFAULT 0.0')
        add_column_if_missing(db, 'fees', 'boarding_fee', 'boarding_fee REAL NOT NULL DEFAULT 0.0')

    if table_exists(db, 'payments'):
        add_column_if_missing(db, 'payments', 'transaction_code', 'transaction_code TEXT')
        add_column_if_missing(db, 'payments', 'bank_reference', 'bank_reference TEXT')
        add_column_if_missing(db, 'payments', 'mpesa_code', 'mpesa_code TEXT')
        add_column_if_missing(db, 'payments', 'verified', 'verified BOOLEAN DEFAULT 0')
        create_unique_index_if_possible(db, 'idx_payments_transaction_code_unique', 'payments', 'transaction_code')

    if table_exists(db, 'audit_logs'):
        add_column_if_missing(db, 'audit_logs', 'ip_address', 'ip_address TEXT')
        add_column_if_missing(db, 'audit_logs', 'user_agent', 'user_agent TEXT')

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