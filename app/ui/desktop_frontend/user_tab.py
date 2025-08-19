from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QComboBox, QMessageBox, QFormLayout, QTableWidget, QTableWidgetItem
from ...core.auth import create_user
from ...core.db_manager import DBManager
import logging

logging.basicConfig(filename='app/logs/user.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UserTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
            }
            QFormLayout {
                margin: 10px;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit, QComboBox {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QTableWidget {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout()
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
        
        add_btn = QPushButton("Add User")
        add_btn.clicked.connect(self.add_user)
        layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete User")
        delete_btn.clicked.connect(self.delete_user)
        layout.addWidget(delete_btn)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role"])
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
            self.username.clear()
            self.password.clear()
            self.load_users()
            QMessageBox.information(self, "Success", "User added successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add user: {str(e)}")

    def delete_user(self):
        selected = self.table.currentRow()
        if selected >= 0:
            try:
                user_id = int(self.table.item(selected, 0).text())
                reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this user?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    with DBManager() as db:
                        db.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    self.load_users()
                    QMessageBox.information(self, "Success", "User deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a user to delete")

    def load_users(self):
        try:
            with DBManager() as db:
                users = db.fetch_all("SELECT id, username, role FROM users ORDER BY id DESC")
                self.table.setRowCount(len(users))
                for row, user in enumerate(users):
                    for col, data in enumerate(user):
                        self.table.setItem(row, col, QTableWidgetItem(str(data or "")))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")