#!/usr/bin/env python3
"""
Complete Database Fix for School Management System
This script will completely reset your database with the correct schema
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def complete_database_fix():
    print("=" * 60)
    print("    SCHOOL MANAGEMENT SYSTEM - DATABASE FIXER")
    print("=" * 60)
    
    # Step 1: Remove all existing database files
    print("\n🗑️  Step 1: Removing existing database files...")
    db_path = "app/data/school_fees.db"
    db_files = [db_path, f"{db_path}-journal", f"{db_path}-wal", f"{db_path}-shm"]
    
    for file in db_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"   ✅ Removed: {file}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {file}: {e}")
    
    # Step 2: Create directory structure
    print("\n📁 Step 2: Creating directory structure...")
    directories = ["app/data", "app/logs", "app/receipts", "app/backups", "reports"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ Ensured directory: {directory}")
    
    # Step 3: Create fresh database with correct schema
    print(f"\n🔨 Step 3: Creating fresh database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables with proper SQLite syntax - FIXED SCHEMA
        tables_sql = [
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(255) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role VARCHAR(50) NOT NULL
            )
            """,
            """
            CREATE TABLE classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL
            )
            """,
            """
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
            """,
            """
            CREATE TABLE fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL,
                total_fees DECIMAL(10, 2) DEFAULT 0.0,
                bus_fee DECIMAL(10, 2) DEFAULT 0.0,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                item VARCHAR(50) NOT NULL,
                quantity DECIMAL(10, 2) NOT NULL,
                cash_equivalent DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
            """,
            """
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
            """,
            """
            CREATE TABLE receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER UNIQUE NOT NULL,
                receipt_no VARCHAR(50) UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """
        ]
        
        # Create each table
        table_names = ["users", "classes", "students", "fees", "contributions", "payments", "receipts", "audit_logs"]
        for i, table_sql in enumerate(tables_sql):
            cursor.execute(table_sql)
            print(f"   ✅ Created table: {table_names[i]}")
        
        # Step 4: Add initial data
        print("\n📋 Step 4: Adding initial data...")
        
        # Create admin user with hashed password
        try:
            from passlib.hash import bcrypt
            admin_password = bcrypt.hash("admin123")
            print("   ✅ Using bcrypt for password hashing")
        except ImportError:
            admin_password = "admin123"  # Fallback
            print("   ⚠️  Using plain text password (bcrypt not available)")
        
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      ("admin", admin_password, "admin"))
        print("   ✅ Created admin user (admin/admin123)")
        
        # Create test clerk user
        try:
            clerk_password = bcrypt.hash("clerk123") if 'bcrypt' in locals() else "clerk123"
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                          ("clerk1", clerk_password, "clerk"))
            print("   ✅ Created clerk user (clerk1/clerk123)")
        except:
            pass
        
        # Create default classes
        default_classes = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]
        for class_name in default_classes:
            cursor.execute("INSERT INTO classes (name) VALUES (?)", (class_name,))
        print(f"   ✅ Created {len(default_classes)} default classes")
        
        # Add a sample student for testing
        cursor.execute("INSERT INTO students (admission_number, name, class_id, guardian_contact) VALUES (?, ?, ?, ?)",
                      ("ADM001", "Test Student", 1, "0700000000"))
        student_id = cursor.lastrowid
        
        # Add fee for the sample student
        cursor.execute("INSERT INTO fees (student_id, total_fees, bus_fee) VALUES (?, ?, ?)",
                      (student_id, 5000.0, 500.0))
        print("   ✅ Created sample student with fees")
        
        conn.commit()
        
        # Step 5: Verify database structure
        print("\n🔍 Step 5: Verifying database structure...")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        created_tables = [table[0] for table in cursor.fetchall()]
        print(f"   📊 Tables created: {created_tables}")
        
        # Test the problematic student query
        cursor.execute("PRAGMA table_info(students)")
        student_columns = [col[1] for col in cursor.fetchall()]
        print(f"   📋 Students table columns: {student_columns}")
        
        # Verify class_id column exists
        if 'class_id' in student_columns:
            print("   ✅ class_id column exists in students table")
        else:
            print("   ❌ class_id column missing - this should not happen!")
        
        # Test the join query that was failing
        test_query = """
        SELECT s.id, s.admission_number, s.name, s.class_id, s.guardian_contact, 
               s.profile_picture, s.bus_location, COALESCE(c.name, 'No Class') as class_name 
        FROM students s 
        LEFT JOIN classes c ON s.class_id = c.id 
        ORDER BY c.name, s.name
        """
        
        cursor.execute(test_query)
        results = cursor.fetchall()
        print(f"   ✅ Test query executed successfully! Found {len(results)} students")
        
        conn.close()
        
        print("\n🎉 DATABASE FIX COMPLETE!")
        print("\nLogin credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Role: admin")
        print("\nAlternative login:")
        print("   Username: clerk1")
        print("   Password: clerk123")
        print("   Role: clerk")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during database creation: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False

def verify_app_structure():
    """Verify that all necessary app files exist"""
    print("\n🔍 Verifying application structure...")
    
    required_files = [
        "app/core/db_manager.py",
        "app/core/student_manager.py", 
        "app/core/auth.py",
        "app/core/models.py",
        "app/ui/desktop_frontend/login.py",
        "app/ui/desktop_frontend/main.py",
        "app/ui/desktop_frontend/student_tab.py"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Warning: {len(missing_files)} files are missing!")
        return False
    return True

def main():
    print("Checking application structure...")
    if not verify_app_structure():
        print("❌ Some application files are missing. Please ensure all files are in place.")
        return
    
    print("Starting database fix...")
    if complete_database_fix():
        print("\n✨ Success! Try running your application now:")
        print("   python run.py")
        print("   Choose option 1 for GUI")
    else:
        print("\n❌ Database fix failed. Check the errors above.")

if __name__ == "__main__":
    main()