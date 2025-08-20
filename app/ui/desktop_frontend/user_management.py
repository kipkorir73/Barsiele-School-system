from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QLineEdit, QMessageBox, QInputDialog, QComboBox, QDialog, QFormLayout
from PyQt6.QtCore import Qt
from ...core.db_manager import DBManager
from ...core.auth import Auth
import logging
import re

logging.basicConfig(filename='app/logs/user_management.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UserManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Management - Barsiele Sunrise Academy")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QLabel { color: #2c3e50; font-size: 14px; font-weight: bold; }
            QTableWidget { 
                border: 2px solid #27ae60; 
                background-color: white; 
                gridline-color: #bdc3c7;
                selection-background-color: #27ae60;
            }
            QPushButton { 
                background-color: #27ae60; 
                color: white; 
                border-radius: 8px; 
                padding: 12px 20px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:pressed { background-color: #1e8449; }
            QLineEdit, QComboBox { 
                border: 2px solid #27ae60; 
                border-radius: 8px; 
                padding: 8px; 
                background-color: white; 
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #229954; }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("User Management")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #27ae60; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # School motto
        motto = QLabel("Together we Rise")
        motto.setStyleSheet("font-size: 16px; font-style: italic; color: #7f8c8d; margin-bottom: 20px;")
        motto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(motto)
        
        # User table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Email", "Role", "Created"])
        layout.addWidget(self.user_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add New User")
        add_btn.clicked.connect(self.add_user)
        edit_btn = QPushButton("Edit User")
        edit_btn.clicked.connect(self.edit_user)
        delete_btn = QPushButton("Delete User")
        delete_btn.clicked.connect(self.delete_user)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_users)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_users()
    
    def load_users(self):
        try:
            with DBManager() as db:
                users = db.fetch_all("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC")
                self.user_table.setRowCount(len(users))
                for row, user in enumerate(users):
                    for col, data in enumerate(user):
                        self.user_table.setItem(row, col, QTableWidgetItem(str(data or "")))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")
    
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def add_user(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New User")
        dialog.setMinimumSize(400, 300)
        
        layout = QFormLayout()
        
        username_edit = QLineEdit()
        email_edit = QLineEdit()
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        role_combo = QComboBox()
        role_combo.addItems(["admin", "clerk"])
        
        layout.addRow("Username:", username_edit)
        layout.addRow("Email:", email_edit)
        layout.addRow("Password:", password_edit)
        layout.addRow("Role:", role_combo)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        def save_user():
            username = username_edit.text().strip()
            email = email_edit.text().strip()
            password = password_edit.text()
            role = role_combo.currentText()
            
            if not username or not email or not password:
                QMessageBox.warning(dialog, "Warning", "All fields are required!")
                return
            
            if not self.validate_email(email):
                QMessageBox.warning(dialog, "Warning", "Please enter a valid email address!")
                return
            
            if len(password) < 6:
                QMessageBox.warning(dialog, "Warning", "Password must be at least 6 characters long!")
                return
            
            try:
                with DBManager() as db:
                    # Check if username or email already exists
                    existing = db.fetch_one("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
                    if existing:
                        QMessageBox.warning(dialog, "Warning", "Username or email already exists!")
                        return
                    
                    hashed_password = Auth.hash_password(password)
                    db.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                              (username, email, hashed_password, role))
                    
                    # Log the action
                    db.execute("INSERT INTO audit_logs (user_id, action) VALUES (?, ?)",
                              (1, f"Created new user: {username} ({email}) with role {role}"))
                
                QMessageBox.information(dialog, "Success", f"User {username} created successfully!")
                dialog.accept()
                self.load_users()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to create user: {str(e)}")
        
        save_btn.clicked.connect(save_user)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def edit_user(self):
        selected = self.user_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Warning", "Please select a user to edit!")
            return
        
        user_id = int(self.user_table.item(selected, 0).text())
        current_username = self.user_table.item(selected, 1).text()
        current_email = self.user_table.item(selected, 2).text()
        current_role = self.user_table.item(selected, 3).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit User: {current_username}")
        dialog.setMinimumSize(400, 300)
        
        layout = QFormLayout()
        
        username_edit = QLineEdit(current_username)
        email_edit = QLineEdit(current_email)
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_edit.setPlaceholderText("Leave empty to keep current password")
        role_combo = QComboBox()
        role_combo.addItems(["admin", "clerk"])
        role_combo.setCurrentText(current_role)
        
        layout.addRow("Username:", username_edit)
        layout.addRow("Email:", email_edit)
        layout.addRow("New Password:", password_edit)
        layout.addRow("Role:", role_combo)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        cancel_btn = QPushButton("Cancel")
        
        def save_changes():
            username = username_edit.text().strip()
            email = email_edit.text().strip()
            password = password_edit.text()
            role = role_combo.currentText()
            
            if not username or not email:
                QMessageBox.warning(dialog, "Warning", "Username and email are required!")
                return
            
            if not self.validate_email(email):
                QMessageBox.warning(dialog, "Warning", "Please enter a valid email address!")
                return
            
            try:
                with DBManager() as db:
                    # Check if username or email already exists for other users
                    existing = db.fetch_one("SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?", 
                                          (username, email, user_id))
                    if existing:
                        QMessageBox.warning(dialog, "Warning", "Username or email already exists!")
                        return
                    
                    if password:
                        if len(password) < 6:
                            QMessageBox.warning(dialog, "Warning", "Password must be at least 6 characters long!")
                            return
                        hashed_password = Auth.hash_password(password)
                        db.execute("UPDATE users SET username = ?, email = ?, password = ?, role = ? WHERE id = ?",
                                  (username, email, hashed_password, role, user_id))
                    else:
                        db.execute("UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?",
                                  (username, email, role, user_id))
                    
                    # Log the action
                    db.execute("INSERT INTO audit_logs (user_id, action) VALUES (?, ?)",
                              (1, f"Updated user: {username} ({email})"))
                
                QMessageBox.information(dialog, "Success", f"User {username} updated successfully!")
                dialog.accept()
                self.load_users()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to update user: {str(e)}")
        
        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def delete_user(self):
        selected = self.user_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Warning", "Please select a user to delete!")
            return
        
        user_id = int(self.user_table.item(selected, 0).text())
        username = self.user_table.item(selected, 1).text()
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete user '{username}'?\n\nThis action cannot be undone.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with DBManager() as db:
                    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    
                    # Log the action
                    db.execute("INSERT INTO audit_logs (user_id, action) VALUES (?, ?)",
                              (1, f"Deleted user: {username}"))
                
                QMessageBox.information(self, "Success", f"User '{username}' deleted successfully!")
                self.load_users()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")
