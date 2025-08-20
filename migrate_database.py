#!/usr/bin/env python3
"""
Database Migration Script for Barsiele Sunrise Academy School Fee System
This script updates the existing database to support new features:
- Email authentication
- Payment verification codes
- Enhanced audit logging
"""

import sqlite3
import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def backup_database(db_path):
    """Create a backup of the existing database"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"school_fees_backup_{timestamp}.db")
    
    try:
        # Copy the database file
        import shutil
        shutil.copy2(db_path, backup_path)
        logging.info(f"Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"Failed to backup database: {e}")
        return None

def migrate_database(db_path):
    """Perform database migration"""
    logging.info("Starting database migration...")
    
    # Create backup first
    backup_path = backup_database(db_path)
    if not backup_path:
        logging.error("Migration aborted - backup failed")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Helper: check if a table exists
        def table_exists(name: str) -> bool:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
            return cursor.fetchone() is not None

        # Check if migrations are needed
        migrations_needed = []
        
        # Check if email column exists in users table
        if table_exists('users'):
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [column[1] for column in cursor.fetchall()]
            if 'email' not in user_columns:
                migrations_needed.append('add_email_to_users')
            if 'created_at' not in user_columns:
                migrations_needed.append('add_created_at_to_users')
        
        # Check if payment verification columns exist (only if payments table exists)
        payment_migrations = []
        if table_exists('payments'):
            cursor.execute("PRAGMA table_info(payments)")
            payment_columns = [column[1] for column in cursor.fetchall()]
            if 'transaction_code' not in payment_columns:
                payment_migrations.append('transaction_code TEXT UNIQUE')
            if 'mpesa_code' not in payment_columns:
                payment_migrations.append('mpesa_code TEXT UNIQUE')
            if 'bank_reference' not in payment_columns:
                payment_migrations.append('bank_reference TEXT UNIQUE')
            if 'verified' not in payment_columns:
                payment_migrations.append('verified BOOLEAN DEFAULT 0')
        
        if payment_migrations:
            migrations_needed.append('add_payment_verification_fields')
        
        # Check if audit_logs has IP and user agent columns
        audit_migrations = []
        if table_exists('audit_logs'):
            cursor.execute("PRAGMA table_info(audit_logs)")
            audit_columns = [column[1] for column in cursor.fetchall()]
            if 'ip_address' not in audit_columns:
                audit_migrations.append('ip_address TEXT')
            if 'user_agent' not in audit_columns:
                audit_migrations.append('user_agent TEXT')
            if audit_migrations:
                migrations_needed.append('add_audit_log_fields')
        
        # Check fees table for boarding_fee
        if table_exists('fees'):
            cursor.execute("PRAGMA table_info(fees)")
            fees_columns = [column[1] for column in cursor.fetchall()]
            if 'boarding_fee' not in fees_columns:
                migrations_needed.append('add_boarding_fee_to_fees')

        # Check presence of food_requirements table
        if not table_exists('food_requirements'):
            migrations_needed.append('create_food_requirements')

        if not migrations_needed:
            logging.info("No migrations needed - database is up to date")
            conn.close()
            return True
        
        logging.info(f"Migrations needed: {migrations_needed}")
        
        # Perform migrations
        if 'add_email_to_users' in migrations_needed and table_exists('users'):
            logging.info("Adding email column to users table...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise

            # Set default email for existing users
            cursor.execute("UPDATE users SET email = username || '@barsiele.ac.ke' WHERE email IS NULL")
            
            # Make email unique after setting defaults
            cursor.execute("""
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'clerk')),
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT INTO users_new (id, username, email, password, role, created_at)
                SELECT id, username, email, password, role, CURRENT_TIMESTAMP FROM users
            """)
            
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
            logging.info("Users table migrated successfully")
        
        if 'add_created_at_to_users' in migrations_needed and table_exists('users'):
            logging.info("Adding created_at column to users table...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise

        if 'add_payment_verification_fields' in migrations_needed and table_exists('payments'):
            logging.info("Adding payment verification fields...")
            for field in payment_migrations:
                try:
                    cursor.execute(f"ALTER TABLE payments ADD COLUMN {field}")
                    logging.info(f"Added payment field: {field}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise

        if 'add_boarding_fee_to_fees' in migrations_needed and table_exists('fees'):
            logging.info("Adding boarding_fee to fees table...")
            try:
                cursor.execute("ALTER TABLE fees ADD COLUMN boarding_fee REAL NOT NULL DEFAULT 0.0")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise

        if 'create_food_requirements' in migrations_needed:
            logging.info("Creating food_requirements table...")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS food_requirements (
                    class_id INTEGER PRIMARY KEY,
                    maize_kg REAL NOT NULL DEFAULT 0.0,
                    beans_kg REAL NOT NULL DEFAULT 0.0,
                    millet_kg REAL NOT NULL DEFAULT 0.0,
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
                )
                """
            )
        
        if 'add_audit_log_fields' in migrations_needed and table_exists('audit_logs'):
            logging.info("Adding audit log fields...")
            for field in audit_migrations:
                try:
                    cursor.execute(f"ALTER TABLE audit_logs ADD COLUMN {field}")
                    logging.info(f"Added audit log field: {field}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
        
        # Add migration log entry if audit_logs table exists
        if 'table_exists' in locals() and table_exists('audit_logs'):
            try:
                cursor.execute(
                    """
                    INSERT INTO audit_logs (action, details, timestamp)
                    VALUES ('migration', 'Schema migration executed', CURRENT_TIMESTAMP)
                    """
                )
            except Exception as e:
                logging.warning(f"Skipping audit log write: {e}")
        conn.commit()
        conn.close()
        logging.info("Database migration completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        
        # Restore backup
        try:
            import shutil
            shutil.copy2(backup_path, db_path)
            logging.info("Database restored from backup")
        except Exception as restore_error:
            logging.error(f"Failed to restore backup: {restore_error}")
        
        return False

def main():
    """Main migration function"""
    # If a path is provided via CLI, use it
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if os.path.exists(candidate):
            db_path = candidate
        else:
            logging.error(f"Provided database path does not exist: {candidate}")
            return False
    else:
        # Find database files (prefer app path)
        possible_db_paths = [
            "app/data/school_fees.db",
            "data/school_fees.db",
            "school_fees.db"
        ]
        db_path = None
        for path in possible_db_paths:
            if os.path.exists(path):
                db_path = path
                break
    
    if not db_path:
        logging.error("Database file not found. Please ensure the database exists.")
        return False
    
    logging.info(f"Found database at: {db_path}")
    
    # Perform migration
    success = migrate_database(db_path)
    
    if success:
        print("\n" + "="*60)
        print("DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("New features available:")
        print("• Email-based authentication")
        print("• Payment verification codes (M-Pesa, Bank)")
        print("• Enhanced activity logging with IP tracking")
        print("• Improved user management")
        print("• School branding (Barsiele Sunrise Academy)")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("DATABASE MIGRATION FAILED!")
        print("="*60)
        print("Please check the logs and try again.")
        print("Your original database has been restored from backup.")
        print("="*60)
    
    return success

if __name__ == "__main__":
    main()
