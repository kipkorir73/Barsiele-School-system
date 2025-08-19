#!/usr/bin/env python3
"""
Simple GUI starter - Use this if run.py doesn't work
"""
import sys
import os
from pathlib import Path
import logging

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(filename='app/logs/gui.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from PyQt6.QtWidgets import QApplication
    from app.ui.desktop_frontend.login import LoginWindow
    from app.core.initialize_db import init_db
    
    print("Initializing database...")
    logging.info("Starting database initialization")
    init_db()
    print("Database ready!")
    logging.info("Database initialized successfully")
    
    app = QApplication(sys.argv)
    app.setApplicationName("School Management System")
    app.setApplicationVersion("1.0")
    
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec())
    
except ImportError as e:
    print(f"Import error: {e}")
    logging.error(f"Import error: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
except Exception as e:
    print(f"Error: {e}")
    logging.error(f"Application error: {e}")
    input("Press Enter to exit...")