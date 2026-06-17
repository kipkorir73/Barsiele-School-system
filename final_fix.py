#!/usr/bin/env python3
"""
Final Fix - Force the app to use the correct database
"""
import os
import sys
import sqlite3
from pathlib import Path
import shutil

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def final_fix():
    print("=" * 60)
    print("    FINAL DATABASE FIX")
    print("=" * 60)
    
    # Step 1: Create/update .env file to ensure consistent database path
    print("\n📝 Step 1: Setting up environment configuration...")
    env_content = """# Database Configuration
DB_TYPE=sqlite
SQLITE_PATH=app/data/school_fees.db

# Other Settings
SECRET_KEY=your-secret-key-here
LOG_PATH=app/logs/school_fees.log
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("   ✅ Created .env file")
    
    # Step 2: Ensure all directories exist
    print("\n📁 Step 2: Creating directories...")
    directories = ["app/data", "app/logs", "app/receipts", "app/backups", "reports"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ Created/verified: {directory}")
    
    # Step 3: Remove any existing database files
    print("\n🗑️  Step 3: Cleaning existing databases...")
    db_path = "app/data/school_fees.db"
    
    # List of all possible database files
    db_files_to_remove = [
        db_path,
        f"{db_path}-journal",
        f"{db_path}-wal", 
        f"{db_path}-shm"
    ]
    
    for file in db_files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"   ✅ Removed: {file}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {file}: {e}")
    
    # Step 4: Create database using the EXACT same connection method as db_manager.py
    print(f"\n🔨 Step 4: Creating database using app's connection method...")
    
    # Import and use the actual DBManager class
    try:
        from app.core.db_manager import DBManager
        print("   ✅ Successfully imported DBManager")
        
        # Test basic connection
        with DBManager() as db:
            print("   ✅ DBManager connection successful")
            
            # Create tables in the exact order
            print("   📝 Creating users table...")
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL
                )
            """)
            
            print("   📝 Creating classes table...")
            db.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) UNIQUE NOT NULL
                )
            """)
            
            print("   📝 Creating students table...")
            db.execute("""
                CREATE TABLE IF NOT EXISTS students (
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
            db.execute("""
                CREATE TABLE IF NOT EXISTS fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER UNIQUE NOT NULL,
                    total_fees DECIMAL(10, 2) DEFAULT 0.0,
                    bus_fee DECIMAL(10, 2) DEFAULT 0.0,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                )
            """)
            
            print("   📝 Creating contributions table...")
            db.execute("""
                CREATE TABLE IF NOT EXISTS contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    item VARCHAR(50) NOT NULL,
                    quantity DECIMAL(10, 2) NOT NULL,
                    cash_equivalent DECIMAL(10, 2) NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                )
            """)
            
            print("   📝 Creating payments table...")
            db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
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
            db.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id INTEGER UNIQUE NOT NULL,
                    receipt_no VARCHAR(50) UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
                )
            """)
            
            print("   📝 Creating audit_logs table...")
            db.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            print("   📋 Adding default data...")
            
            # Add admin user
            try:
                import bcrypt
                admin_password = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            except ImportError:
                admin_password = "admin123"
            
            # Check if admin already exists
            existing_admin = db.fetch_one("SELECT id FROM users WHERE username = 'admin'")
            if not existing_admin:
                db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                          ("admin", admin_password, "admin"))
                print("   ✅ Added admin user")
            
            # Add classes
            classes = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]
            for class_name in classes:
                existing_class = db.fetch_one("SELECT id FROM classes WHERE name = ?", (class_name,))
                if not existing_class:
                    db.execute("INSERT INTO classes (name) VALUES (?)", (class_name,))
            print("   ✅ Added default classes")
            
            # Add test student
            existing_student = db.fetch_one("SELECT id FROM students WHERE admission_number = 'ADM001'")
            if not existing_student:
                db.execute("INSERT INTO students (admission_number, name, class_id, guardian_contact) VALUES (?, ?, ?, ?)",
                          ("ADM001", "Test Student", 1, "0700000000"))
                print("   ✅ Added test student")
        
        print("   ✅ Database creation completed using DBManager")
        
    except Exception as e:
        print(f"   ❌ Error with DBManager: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Verify everything works
    print("\n🧪 Step 5: Testing all functions...")
    
    try:
        # Test DBManager connection
        with DBManager() as db:
            # List all tables
            tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [t[0] for t in tables]
            print(f"   📊 Tables in database: {table_names}")
            
            # Check students table structure
            if 'students' in table_names:
                students_info = db.fetch_all("PRAGMA table_info(students)")
                columns = [col[1] for col in students_info]
                print(f"   📋 Students columns: {columns}")
                
                if 'class_id' in columns:
                    print("   ✅ class_id column exists")
                else:
                    print("   ❌ class_id column missing!")
                    return False
            else:
                print("   ❌ Students table missing!")
                return False
        
        # Test student_manager functions
        from app.core.student_manager import get_all_students
        students = get_all_students()
        print(f"   ✅ get_all_students() works! Found {len(students)} students")
        
        if students:
            print(f"   📄 Sample student: {students[0]}")
        
        print("\n🎉 SUCCESS! Everything is working correctly.")
        print("\nLogin credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Final test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_backup_start_script():
    """Create a simple startup script that ensures database is ready"""
    script_content = '''#!/usr/bin/env python3
"""
Safe Application Starter
Run this instead of run.py to ensure database is properly initialized
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def ensure_database():
    """Ensure database exists and has correct structure"""
    try:
        from app.core.db_manager import DBManager
        from app.core.student_manager import get_all_students
        
        # Test if we can connect and query
        with DBManager() as db:
            db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        
        # Test student manager
        get_all_students()
        
        print("✅ Database is ready!")
        return True
        
    except Exception as e:
        print(f"❌ Database issue: {e}")
        print("🔧 Attempting to fix...")
        
        # Try to reinitialize
        try:
            from app.core.initialize_db import init_db
            init_db()
            print("✅ Database reinitialized!")
            return True
        except Exception as e2:
            print(f"❌ Could not fix database: {e2}")
            return False

def main():
    print("🚀 Starting School Management System...")
    
    if not ensure_database():
        print("❌ Cannot start - database issues")
        return
    
    # Import and run the main application
    from run import main as run_main
    run_main()

if __name__ == "__main__":
    main()
'''
    
    with open('safe_start.py', 'w') as f:
        f.write(script_content)
    print("   ✅ Created safe_start.py script")

if __name__ == "__main__":
    if final_fix():
        create_backup_start_script()
        print("\n" + "=" * 60)
        print("✨ Database is now ready!")
        print("✨ Try running: python run.py")
        print("✨ Or use the safe starter: python safe_start.py")
        print("=" * 60)
    else:
        print("\n❌ Fix failed. Please check the errors above.")