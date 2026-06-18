#!/usr/bin/env python3
"""
School Management System Launcher
Run this file to start the application
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    try:
        import PyQt6
        import bcrypt
        import fpdf
        from dotenv import load_dotenv
        load_dotenv()
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def ensure_directories():
    directories = ['app/data', 'app/logs', 'app/receipts', 'app/backups', 'reports']
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 50)
    print("    SCHOOL MANAGEMENT SYSTEM")
    print("=" * 50)
    
    if not check_dependencies():
        return
    
    ensure_directories()
    
    print("\nChoose how to run the application:")
    print("1. 🖥️  Desktop GUI Application (Recommended)")
    print("2. 💻 Command Line Interface")
    print("3. 🗄️  Initialize Database")
    print("4. 💾 Create Database Backup")
    print("5. ❌ Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice == '1':
                launch_gui()
                break
            elif choice == '2':
                launch_cli()
                break
            elif choice == '3':
                initialize_database()
                break
            elif choice == '4':
                backup_database()
                break
            elif choice == '5':
                print("Goodbye! 👋")
                break
            else:
                print("❌ Invalid choice! Please enter 1-5")
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def launch_gui():
    print("\n🚀 Starting Desktop Application...")
    try:
        from PyQt6.QtWidgets import QApplication
        from app.ui.desktop_frontend.login import LoginWindow
        from app.core.initialize_db import init_db
        init_db()
        print("Database ready!")
        app = QApplication(sys.argv)
        app.setApplicationName("School Management System")
        app.setApplicationVersion("1.0")
        login_window = LoginWindow()
        login_window.show()
        sys.exit(app.exec())
    except ImportError as e:
        print(f"❌ GUI Error: {e}")
        print("Make sure PyQt6 is installed: pip install PyQt6")
    except Exception as e:
        print(f"❌ Application Error: {e}")

def launch_cli():
    print("\n🚀 Starting Command Line Interface...")
    try:
        from app.core.main_app import main as cli_main
        cli_main()
    except Exception as e:
        print(f"❌ CLI Error: {e}")

def initialize_database():
    print("\n🗄️ Initializing Database...")
    try:
        from app.core.initialize_db import init_db
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

def backup_database():
    print("\n💾 Creating Database Backup...")
    try:
        from app.scripts.backup_db import backup
        backup()
    except Exception as e:
        print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    main()