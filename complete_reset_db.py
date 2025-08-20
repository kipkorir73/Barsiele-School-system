#!/usr/bin/env python3
"""
Complete Database Reset and Verification
Place this file in your project root directory
"""
import os
import sys
import sqlite3
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def complete_reset():
    print("🔄 Starting complete database reset...")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        db_path = os.getenv('SQLITE_PATH', 'app/data/school_fees.db')
    except:
        db_path = 'app/data/school_fees.db'
    
    # Step 1: Remove all database files
    db_files = [db_path, f"{db_path}-journal", f"{db_path}-wal", f"{db_path}-shm"]
    for file in db_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Removed: {file}")
            except Exception as e:
                print(f"⚠️  Could not remove {file}: {e}")
    
    # Step 2: Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Step 3: Create fresh database with correct SQLite syntax
    print(f"📝 Creating fresh database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables with correct SQLite syntax
        tables = [
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
                class_id INTEGER,
                name VARCHAR(255) NOT NULL,
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
                total_fees DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
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
                FOREIGN KEY (clerk_id) REFERENCES users(id) ON DELETE CASCADE
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
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        ]
        
        # Execute table creation
        for i, table_sql in enumerate(tables):
            cursor.execute(table_sql)
            table_name = table_sql.strip().split('\n')[1].strip().split()[0]
            print(f"✅ Created table: {table_name}")
        
        # Add initial data
        print("📋 Adding initial data...")
        
        # Hash the password properly
        try:
            from passlib.hash import bcrypt
            hashed_password = bcrypt.hash("admin123")
        except:
            # Fallback if passlib not available
            hashed_password = "admin123"
        
        # Insert default admin user
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      ("admin", hashed_password, "admin"))
        print("✅ Created admin user (admin/admin123)")
        
        # Insert default classes
        default_classes = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]
        for class_name in default_classes:
            cursor.execute("INSERT INTO classes (name) VALUES (?)", (class_name,))
        print(f"✅ Created {len(default_classes)} default classes")
        
        conn.commit()
        
        # Step 4: Verify database structure
        print("\n🔍 Verifying database structure...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_created = cursor.fetchall()
        print(f"📊 Tables created: {[table[0] for table in tables_created]}")
        
        # Check students table structure specifically
        cursor.execute("PRAGMA table_info(students)")
        student_columns = cursor.fetchall()
        print(f"📋 Students table columns: {[col[1] for col in student_columns]}")
        
        # Check if we can do a basic join
        cursor.execute("""
            SELECT s.id, s.admission_number, s.name, s.class_id, s.guardian_contact, 
                   s.profile_picture, s.bus_location, COALESCE(c.name, 'No Class') as class_name 
            FROM students s 
            LEFT JOIN classes c ON s.class_id = c.id 
            LIMIT 1
        """)
        print("✅ Join query test passed")
        
        conn.close()
        print("\n🎉 Database reset and verification complete!")
        print("\nLogin credentials:")
        print("Username: admin")
        print("Password: admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during database creation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if complete_reset():
        print("\n✨ You can now run: python run.py")
    else:
        print("\n❌ Reset failed. Please check the errors above.")