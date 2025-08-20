#!/usr/bin/env python3
"""
Debug Database Script - Find and Fix the Issue
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_database():
    print("=" * 60)
    print("    DATABASE DEBUG AND FIX")
    print("=" * 60)
    
    # Step 1: Find the actual database file
    possible_db_paths = [
        "app/data/school_fees.db",
        "school_fees.db",
        "data/school_fees.db",
        os.path.expanduser("~/school_fees.db")
    ]
    
    print("\n🔍 Step 1: Finding database files...")
    found_dbs = []
    for db_path in possible_db_paths:
        if os.path.exists(db_path):
            print(f"   ✅ Found database: {db_path}")
            found_dbs.append(db_path)
        else:
            print(f"   ❌ Not found: {db_path}")
    
    # Check what the app is actually trying to use
    try:
        from dotenv import load_dotenv
        load_dotenv()
        env_db_path = os.getenv('SQLITE_PATH', 'app/data/school_fees.db')
        print(f"   📋 Environment DB path: {env_db_path}")
        if os.path.exists(env_db_path) and env_db_path not in found_dbs:
            found_dbs.append(env_db_path)
    except:
        print("   ⚠️  Could not load environment variables")
    
    # Step 2: Check each found database
    for db_path in found_dbs:
        print(f"\n🔍 Checking database: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            print(f"   📊 Tables: {tables}")
            
            # Check students table structure if it exists
            if 'students' in tables:
                cursor.execute("PRAGMA table_info(students)")
                columns = [(col[1], col[2]) for col in cursor.fetchall()]
                print(f"   📋 Students table columns: {columns}")
                
                # Check if class_id exists
                column_names = [col[0] for col in columns]
                if 'class_id' in column_names:
                    print("   ✅ class_id column exists")
                else:
                    print("   ❌ class_id column MISSING!")
            else:
                print("   ❌ Students table does not exist")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Error checking {db_path}: {e}")
    
    # Step 3: Force complete reset
    print(f"\n🔨 Step 3: Force complete database reset...")
    
    # Remove ALL possible database files
    for db_path in found_dbs + possible_db_paths:
        for suffix in ["", "-journal", "-wal", "-shm"]:
            file_to_remove = f"{db_path}{suffix}"
            if os.path.exists(file_to_remove):
                try:
                    os.remove(file_to_remove)
                    print(f"   ✅ Removed: {file_to_remove}")
                except Exception as e:
                    print(f"   ❌ Could not remove {file_to_remove}: {e}")
    
    # Step 4: Create the database with absolute certainty
    target_db = "app/data/school_fees.db"
    print(f"\n🏗️  Step 4: Creating fresh database at: {os.path.abspath(target_db)}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(target_db), exist_ok=True)
    
    try:
        # Create completely fresh database
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        
        print("   📝 Creating users table...")
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(255) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role VARCHAR(50) NOT NULL
            )
        """)
        
        print("   📝 Creating classes table...")
        cursor.execute("""
            CREATE TABLE classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        
        print("   📝 Creating students table with class_id...")
        cursor.execute("""
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admission_number VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                class_id INTEGER,
                guardian_contact VARCHAR(20),
                profile_picture TEXT,
                bus_location VARCHAR(100),
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
            )
        """)
        
        print("   📝 Creating fees table...")
        cursor.execute("""
            CREATE TABLE fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL,
                total_fees DECIMAL(10, 2) DEFAULT 0.0,
                bus_fee DECIMAL(10, 2) DEFAULT 0.0,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        
        print("   📝 Creating contributions table...")
        cursor.execute("""
            CREATE TABLE contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                item VARCHAR(50) NOT NULL,
                quantity DECIMAL(10, 2) NOT NULL,
                cash_equivalent DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        
        print("   📝 Creating payments table...")
        cursor.execute("""
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                method VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                clerk_id INTEGER NOT NULL,
                receipt_no VARCHAR(50) UNIQUE NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (clerk_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        print("   📝 Creating receipts table...")
        cursor.execute("""
            CREATE TABLE receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER UNIQUE NOT NULL,
                receipt_no VARCHAR(50) UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
        """)
        
        print("   📝 Creating audit_logs table...")
        cursor.execute("""
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # Add default data
        print("   📋 Adding default admin user...")
        try:
            from passlib.hash import bcrypt
            admin_password = bcrypt.hash("admin123")
        except ImportError:
            admin_password = "admin123"
        
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      ("admin", admin_password, "admin"))
        
        print("   📋 Adding default classes...")
        classes = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]
        for class_name in classes:
            cursor.execute("INSERT INTO classes (name) VALUES (?)", (class_name,))
        
        print("   📋 Adding test student...")
        cursor.execute("INSERT INTO students (admission_number, name, class_id, guardian_contact) VALUES (?, ?, ?, ?)",
                      ("ADM001", "Test Student", 1, "0700000000"))
        
        conn.commit()
        
        # Step 5: Final verification
        print("\n✅ Step 5: Final verification...")
        
        # Check students table structure
        cursor.execute("PRAGMA table_info(students)")
        columns = cursor.fetchall()
        print("   📋 Students table structure:")
        for col in columns:
            print(f"      - {col[1]} ({col[2]})")
        
        # Test the actual query from student_manager.py
        test_query = """
        SELECT s.id, s.admission_number, s.name, s.class_id, s.guardian_contact, 
               s.profile_picture, s.bus_location, COALESCE(c.name, 'No Class') as class_name 
        FROM students s 
        LEFT JOIN classes c ON s.class_id = c.id 
        ORDER BY c.name, s.name
        """
        
        print("   🧪 Testing the problematic query...")
        cursor.execute(test_query)
        results = cursor.fetchall()
        print(f"   ✅ Query successful! Found {len(results)} students")
        
        if results:
            print("   📄 Sample result:")
            print(f"      {results[0]}")
        
        conn.close()
        
        print(f"\n🎉 SUCCESS! Database created at: {os.path.abspath(target_db)}")
        print("\nLogin credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False

def test_student_manager():
    """Test if student_manager can now work"""
    print("\n🧪 Testing student_manager functions...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from app.core.student_manager import get_all_students
        
        students = get_all_students()
        print(f"   ✅ get_all_students() works! Found {len(students)} students")
        
        if students:
            print(f"   📄 Sample student: {students[0]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ student_manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if debug_database():
        print("\n" + "=" * 60)
        test_student_manager()
        print("\n✨ Try running your application now: python run.py")
    else:
        print("\n❌ Database fix failed.")