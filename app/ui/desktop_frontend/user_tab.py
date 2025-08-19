from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, 
                             QComboBox, QMessageBox, QFormLayout, QTableWidget,
                             QTableWidgetItem, QHBoxLayout)
from ...core.auth import create_user
from ...core.db_manager import DBManager

class UserTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # User form
        form_layout = QFormLayout()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        form_layout.addRow("Username:", self.username)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password)
        
        self.role = QComboBox()
        self.role.addItems(["admin", "clerk"])
        form_layout.addRow("Role:", self.role)
        
        layout.addLayout(form_layout)
        
        # Add user button
        add_btn = QPushButton("Add User")
        add_btn.clicked.connect(self.add_user)
        layout.addWidget(add_btn)
        
        # Users table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Created"])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.load_users()

    def add_user(self):
        try:
            username = self.username.text().strip()
            pw = self.password.text()
            role = self.role.currentText()
            
            if not username or not pw:
                QMessageBox.warning(self, "Warning", "Please fill all fields")
                return
                
            create_user(username, pw, role)
            
            # Clear form
            self.username.clear()
            self.password.clear()
            
            self.load_users()
            QMessageBox.information(self, "Success", "User added successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add user: {str(e)}")

    def load_users(self):
        try:
            db = DBManager()
            users = db.fetch_all("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC")
            db.close()
            
            self.table.setRowCount(len(users))
            for row, user in enumerate(users):
                for col, data in enumerate(user):
                    self.table.setItem(row, col, QTableWidgetItem(str(data or "")))
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")