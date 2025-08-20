from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QLabel
from PyQt6.QtCore import Qt
from ...core.auth import validate_login  # This function needs to be added to auth.py
import logging

logging.basicConfig(filename='app/logs/login.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("School Management System - Login")
        self.setGeometry(100, 100, 350, 200)
        self.setFixedSize(350, 200)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8;
                border-radius: 10px;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Title
        title = QLabel("School Management System")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Login form
        self.username = QLineEdit(self)
        self.username.setPlaceholderText("Username or Email")
        self.username.setMinimumHeight(35)
        main_layout.addWidget(self.username)
        
        self.password = QLineEdit(self)
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setMinimumHeight(35)
        main_layout.addWidget(self.password)
        
        self.login_btn = QPushButton("Login", self)
        self.login_btn.setMinimumHeight(40)
        main_layout.addWidget(self.login_btn)
        
        main_layout.addStretch()
        self.setLayout(main_layout)
        
        # Connect signals
        self.login_btn.clicked.connect(self.login)
        self.password.returnPressed.connect(self.login)
        self.username.returnPressed.connect(self.login)
        
        self.username.setFocus()
        self.current_user = None

    def login(self):
        try:
            username = self.username.text().strip()
            password = self.password.text()
            
            if not username or not password:
                QMessageBox.warning(self, "Input Error", "Please enter both username and password")
                return
                
            # Use the Auth.authenticate method
            from ...core.auth import Auth
            user = Auth.authenticate(username, password)
            if user:
                # Preserve username from DB (in case login used email)
                self.current_user = user
                from .main import MainWindow
                self.main_window = MainWindow(self.current_user)
                self.main_window.show()
                self.hide()
                logging.info(f"Successful login for user: {user['username']}")
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password")
                self.password.clear()
                self.username.setFocus()
                logging.warning(f"Failed login attempt for user: {username}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")
            logging.error(f"Login error for user {username}: {str(e)}")
            
    def get_user(self):
        return self.current_user