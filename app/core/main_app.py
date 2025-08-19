import logging
from pathlib import Path
from .auth import create_user, validate_login
from .student_manager import create_student, get_all_students, search_students
from .payment_manager import record_payment, get_balance
from .fee_manager import set_fee
from .initialize_db import init_db
from datetime import datetime
import sys

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=log_dir / 'app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
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
            elif choice == '3' and current_user['role'] == 'admin':
                reports_menu()
            elif choice == '3':
                print("Access denied. Admin only.")
            elif choice == '4':
                current_user = None
                print("Logged out successfully!")
            else:
                print("Invalid choice!")

# [Rest of main_app.py functions remain similar with logging added]

def create_user_cli():
    try:
        username = input("Username: ").strip()
        pw = input("Password: ").strip()
        role = input("Role (admin/clerk): ").strip().lower()
        if role not in ['admin', 'clerk']:
            print("Invalid role!")
            return
        create_user(username, pw, role)
        print("User created successfully.")
    except Exception as e:
        print(f"Failed to create user: {e}")

def login_cli():
    try:
        username = input("Username: ").strip()
        pw = input("Password: ").strip()
        user = validate_login(username, pw)
        if user:
            print("Login successful!")
            return user
        print("Invalid credentials")
        return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

# [Other functions like student_menu, payment_menu follow similar pattern]

if __name__ == "__main__":
    main()