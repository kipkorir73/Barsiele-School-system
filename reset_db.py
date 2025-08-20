#!/usr/bin/env python3
"""
Database Reset Utility
Use this to completely reset the database if you encounter issues
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def reset_database():
    """Reset the database completely"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        db_path = os.getenv('SQLITE_PATH', 'app/data/school_fees.db')
        
        print("🗑️  Resetting database...")
        
        # Remove existing database file
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✅ Removed existing database: {db_path}")
        
        # Remove any lock files
        lock_files = [f"{db_path}-journal", f"{db_path}-wal", f"{db_path}-shm"]
        for lock_file in lock_files:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"✅ Removed lock file: {lock_file}")
        
        # Initialize fresh database
        from app.core.initialize_db import init_db
        init_db()
        
        print("\n🎉 Database reset complete!")
        print("\nDefault login credentials:")
        print("Username: admin")
        print("Password: admin123")
        print("Role: admin")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_database()