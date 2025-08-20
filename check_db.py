#!/usr/bin/env python3
"""
Database Structure Checker
Check what's actually in your database
"""
import os
import sys
import sqlite3
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_database():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        db_path = os.getenv('SQLITE_PATH', 'app/data/school_fees.db')
    except:
        db_path = 'app/data/school_fees.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file does not exist: {db_path}")
        return
    
    print(f"🔍 Checking database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n📊 Tables found: {[table[0] for table in tables]}")
        
        # Check each table structure
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Structure of table '{table_name}':")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        
        # Specifically check students table
        if 'students' in [t[0] for t in tables]:
            print("\n🎯 Testing students table query...")
            try:
                cursor.execute("""
                    SELECT s.id, s.admission_number, s.name, s.class_id, s.guardian_contact, 
                           s.profile_picture, s.bus_location, COALESCE(c.name, 'No Class') as class_name 
                    FROM students s 
                    LEFT JOIN classes c ON s.class_id = c.id 
                    LIMIT 1
                """)
                print("✅ Students query works correctly")
            except Exception as e:
                print(f"❌ Students query failed: {e}")
        
        # Check data counts
        print("\n📈 Data counts:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} records")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()