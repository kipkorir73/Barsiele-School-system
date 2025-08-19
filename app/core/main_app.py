import logging
import os
import sys
from pathlib import Path
from .auth import create_user, validate_login
from .student_manager import create_student, get_all_students, search_students
from .payment_manager import record_payment, get_balance
from .fee_manager import set_fee
from .initialize_db import init_db

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        filename=log_dir / 'app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    """Main CLI application"""
    setup_logging()
    
    print("=== School Management System CLI ===")
    print("Initializing database...")
    
    try:
        init_db()
        print("Database ready!")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return
    
    current_user = None
    
    while True:
        if not current_user:
            print("\n--- Main Menu ---")
            print("1. Create User")
            print("2. Login")
            print("3. Exit")
            
            choice = input("Enter choice (1-3): ").strip()
            
            if choice == '1':
                create_user_cli()
            elif choice == '2':
                current_user = login_cli()
            elif choice == '3':
                print("Goodbye!")
                break
            else:
                print("Invalid choice!")
        else:
            print(f"\n--- Logged in as {current_user['role']} ---")
            print("1. Student Management")
            print("2. Payment Management")
            print("3. Reports (Admin only)")
            print("4. Logout")
            
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                student_menu(current_user)
            elif choice == '2':
                payment_menu(current_user)
            elif choice == '3':
                if current_user['role'] == 'admin':
                    reports_menu()
                else:
                    print("Access denied. Admin only.")
            elif choice == '4':
                current_user = None
                print("Logged out successfully!")
            else:
                print("Invalid choice!")

def create_user_cli():
    """Create user via CLI"""
    try:
        print("\n--- Create User ---")
        username = input("Username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return
            
        password = input("Password: ").strip()
        if not password:
            print("Password cannot be empty!")
            return
            
        role = input("Role (admin/clerk): ").strip().lower()
        if role not in ['admin', 'clerk']:
            print("Invalid role! Must be 'admin' or 'clerk'")
            return
            
        user_id = create_user(username, password, role)
        print(f"User created successfully with ID: {user_id}")
        logging.info(f"User created: {username} ({role})")
        
    except Exception as e:
        print(f"Failed to create user: {e}")
        logging.error(f"User creation failed: {e}")

def login_cli():
    """Login via CLI"""
    try:
        print("\n--- Login ---")
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        user = validate_login(username, password)
        if user:
            print(f"Login successful! Welcome, {username} ({user['role']})")
            logging.info(f"User logged in: {username}")
            return user
        else:
            print("Invalid credentials!")
            return None
            
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def student_menu(user):
    """Student management menu"""
    while True:
        print("\n--- Student Management ---")
        print("1. Add Student")
        print("2. List All Students")
        print("3. Search Students")
        print("4. Set Student Fee")
        print("5. Back to Main Menu")
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == '1':
            add_student_cli()
        elif choice == '2':
            list_students_cli()
        elif choice == '3':
            search_students_cli()
        elif choice == '4':
            set_fee_cli()
        elif choice == '5':
            break
        else:
            print("Invalid choice!")

def add_student_cli():
    """Add student via CLI"""
    try:
        print("\n--- Add Student ---")
        adm_no = input("Admission Number: ").strip()
        name = input("Student Name: ").strip()
        class_ = input("Class: ").strip()
        guardian = input("Guardian Contact: ").strip()
        
        if not all([adm_no, name, class_]):
            print("Admission number, name, and class are required!")
            return
            
        student_id = create_student(adm_no, name, class_, guardian)
        print(f"Student added successfully with ID: {student_id}")
        
        # Set initial fee
        fee = input("Set initial fee (or press Enter for 0): ").strip()
        try:
            fee = float(fee) if fee else 0.0
            set_fee(student_id, fee)
            print(f"Fee set to KSh {fee:,.2f}")
        except ValueError:
            print("Invalid fee amount, set to KSh 0.00")
            set_fee(student_id, 0.0)
            
    except Exception as e:
        print(f"Failed to add student: {e}")

def list_students_cli():
    """List all students"""
    try:
        students = get_all_students()
        if not students:
            print("No students found.")
            return
            
        print(f"\n{'ID':<5} {'Adm No':<10} {'Name':<25} {'Class':<10} {'Guardian':<15}")
        print("-" * 70)
        
        for student in students:
            print(f"{student[0]:<5} {student[1]:<10} {student[2]:<25} {student[3]:<10} {student[4] or '':<15}")
            
    except Exception as e:
        print(f"Failed to list students: {e}")

def search_students_cli():
    """Search students"""
    try:
        query = input("Search query (name or admission number): ").strip()
        students = search_students(query)
        
        if not students:
            print("No students found matching your search.")
            return
            
        print(f"\n{'ID':<5} {'Adm No':<10} {'Name':<25} {'Class':<10}")
        print("-" * 55)
        
        for student in students:
            print(f"{student[0]:<5} {student[1]:<10} {student[2]:<25} {student[3]:<10}")
            
    except Exception as e:
        print(f"Search failed: {e}")

def set_fee_cli():
    """Set student fee"""
    try:
        student_id = input("Student ID: ").strip()
        try:
            student_id = int(student_id)
        except ValueError:
            print("Invalid student ID!")
            return
            
        fee = input("Total fee amount: ").strip()
        try:
            fee = float(fee)
        except ValueError:
            print("Invalid fee amount!")
            return
            
        set_fee(student_id, fee)
        print(f"Fee set to KSh {fee:,.2f} for student ID {student_id}")
        
    except Exception as e:
        print(f"Failed to set fee: {e}")

def payment_menu(user):
    """Payment management menu"""
    while True:
        print("\n--- Payment Management ---")
        print("1. Record Payment")
        print("2. Check Student Balance")
        print("3. Back to Main Menu")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            record_payment_cli(user)
        elif choice == '2':
            check_balance_cli()
        elif choice == '3':
            break
        else:
            print("Invalid choice!")

def record_payment_cli(user):
    """Record payment via CLI"""
    try:
        print("\n--- Record Payment ---")
        student_id = input("Student ID: ").strip()
        try:
            student_id = int(student_id)
        except ValueError:
            print("Invalid student ID!")
            return
            
        amount = input("Amount: ").strip()
        try:
            amount = float(amount)
        except ValueError:
            print("Invalid amount!")
            return
            
        method = input("Payment method (Cash/M-Pesa/Bank Transfer/Cheque): ").strip()
        date = input("Date (YYYY-MM-DD) or press Enter for today: ").strip()
        
        if not date:
            from datetime import datetime
            date = datetime.now().strftime('%Y-%m-%d')
            
        payment_id = record_payment(student_id, amount, method, date, user['id'])
        print(f"Payment recorded successfully with ID: {payment_id}")
        
        # Show new balance
        balance = get_balance(student_id)
        print(f"New balance: KSh {balance:,.2f}")
        
    except Exception as e:
        print(f"Failed to record payment: {e}")

def check_balance_cli():
    """Check student balance"""
    try:
        student_id = input("Student ID: ").strip()
        try:
            student_id = int(student_id)
        except ValueError:
            print("Invalid student ID!")
            return
            
        balance = get_balance(student_id)
        print(f"Current balance for student ID {student_id}: KSh {balance:,.2f}")
        
    except Exception as e:
        print(f"Failed to check balance: {e}")

def reports_menu():
    """Reports menu (admin only)"""
    print("\n--- Reports ---")
    print("Report generation available in desktop application.")
    print("Use: python app/ui/desktop_frontend/main.py")

if __name__ == "__main__":
    main()