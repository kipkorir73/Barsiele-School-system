from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QComboBox, QProgressBar, QLineEdit, QMessageBox, QInputDialog
from PyQt6.QtCore import Qt
from ...core.db_manager import DBManager
from ...core.student_manager import get_all_students
from ...core.student_manager import create_student, update_student, get_student
from ...core.auth import create_user
import logging
import time
from datetime import datetime

logging.basicConfig(filename='app/logs/admin.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AdminDashboard(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setStyleSheet("""
            QWidget { background-color: #ecf0f1; }
            QLabel { color: #2c3e50; font-size: 14px; }
            QTableWidget { border: 1px solid #bdc3c7; background-color: white; }
            QPushButton { background-color: #3498db; color: white; border-radius: 5px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
            QComboBox, QLineEdit { border: 2px solid #3498db; border-radius: 5px; padding: 5px; background-color: white; }
            QProgressBar { border: 2px solid #3498db; border-radius: 5px; text-align: center; }
        """)
        
        layout = QVBoxLayout()
        
        # Summary Section
        summary_layout = QHBoxLayout()
        self.total_paid_label = QLabel("Total Paid: KSh 0.00")
        self.total_arrears_label = QLabel("Total Arrears: KSh 0.00")
        self.total_contrib_label = QLabel("Total Contributions: KSh 0.00")
        summary_layout.addWidget(self.total_paid_label)
        summary_layout.addWidget(self.total_arrears_label)
        summary_layout.addWidget(self.total_contrib_label)
        layout.addLayout(summary_layout)
        
        # Class-wise Arrears
        layout.addWidget(QLabel("Arrears by Class:"))
        self.class_arrears_table = QTableWidget()
        self.class_arrears_table.setColumnCount(2)
        self.class_arrears_table.setHorizontalHeaderLabels(["Class", "Arrears"])
        layout.addWidget(self.class_arrears_table)
        
        # High Arrears Students
        layout.addWidget(QLabel("Students with High Arrears (> KSh 500):"))
        self.high_arrears_table = QTableWidget()
        self.high_arrears_table.setColumnCount(4)
        self.high_arrears_table.setHorizontalHeaderLabels(["ID", "Name", "Class", "Arrears"])
        layout.addWidget(self.high_arrears_table)
        
        # Class Management
        class_layout = QHBoxLayout()
        self.class_combo = QComboBox()
        self.load_classes()
        class_layout.addWidget(QLabel("Class:"))
        class_layout.addWidget(self.class_combo)
        add_class_btn = QPushButton("Add Class")
        add_class_btn.clicked.connect(self.add_class)
        delete_class_btn = QPushButton("Delete Class")
        delete_class_btn.clicked.connect(self.delete_class)
        class_layout.addWidget(add_class_btn)
        class_layout.addWidget(delete_class_btn)
        layout.addLayout(class_layout)
        
        # User Management
        user_layout = QHBoxLayout()
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Role"])
        self.load_users()
        user_layout.addWidget(self.user_table)
        
        add_user_btn = QPushButton("Add User")
        add_user_btn.clicked.connect(self.add_user)
        delete_user_btn = QPushButton("Delete User")
        delete_user_btn.clicked.connect(self.delete_user)
        user_layout.addWidget(add_user_btn)
        user_layout.addWidget(delete_user_btn)
        layout.addLayout(user_layout)
        
        # Logs
        layout.addWidget(QLabel("Recent Actions:"))
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(3)
        self.logs_table.setHorizontalHeaderLabels(["User ID", "Action", "Timestamp"])
        layout.addWidget(self.logs_table)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        self.load_data()

    def load_classes(self):
        with DBManager() as db:
            classes = db.fetch_all("SELECT name FROM classes")
            self.class_combo.addItems([c[0] for c in classes])

    def load_users(self):
        with DBManager() as db:
            users = db.fetch_all("SELECT id, username, role FROM users")
            self.user_table.setRowCount(len(users))
            for row, user in enumerate(users):
                for col, data in enumerate(user):
                    self.user_table.setItem(row, col, QTableWidgetItem(str(data or "")))

    def load_data(self):
        try:
            with DBManager() as db:
                # Simulate progress
                for i in range(0, 101, 20):
                    self.progress_bar.setValue(i)
                    time.sleep(0.1)
                
                # Total Paid
                total_paid = db.fetch_one("SELECT SUM(amount) FROM payments")[0] or 0
                self.total_paid_label.setText(f"Total Paid: KSh {total_paid:,.2f}")
                
                # Total Arrears
                students = get_all_students()
                total_arrears = sum(get_balance(s[0]) for s in students if get_balance(s[0]) > 0)
                self.total_arrears_label.setText(f"Total Arrears: KSh {total_arrears:,.2f}")
                
                # Total Contributions
                total_contrib = db.fetch_one("SELECT SUM(cash_equivalent) FROM contributions")[0] or 0
                self.total_contrib_label.setText(f"Total Contributions: KSh {total_contrib:,.2f}")
                
                # Class-wise Arrears
                class_arrears = db.fetch_all("""
                    SELECT c.name, SUM(COALESCE(f.total_fees, 0) + COALESCE(f.bus_fee, 0) - COALESCE(SUM(p.amount), 0)) as arrears
                    FROM classes c
                    LEFT JOIN students s ON c.id = s.class_id
                    LEFT JOIN fees f ON s.id = f.student_id
                    LEFT JOIN payments p ON s.id = p.student_id
                    GROUP BY c.name
                """)
                self.class_arrears_table.setRowCount(len(class_arrears))
                for row, (class_name, arrears) in enumerate(class_arrears):
                    self.class_arrears_table.setItem(row, 0, QTableWidgetItem(class_name or ""))
                    self.class_arrears_table.setItem(row, 1, QTableWidgetItem(f"KSh {arrears:,.2f}" if arrears else "KSh 0.00"))
                
                # High Arrears Students
                high_arrears = db.fetch_all("""
                    SELECT s.id, s.name, c.name as class_name, (COALESCE(f.total_fees, 0) + COALESCE(f.bus_fee, 0) - COALESCE(SUM(p.amount), 0)) as arrears
                    FROM students s
                    LEFT JOIN classes c ON s.class_id = c.id
                    LEFT JOIN fees f ON s.id = f.student_id
                    LEFT JOIN payments p ON s.id = p.student_id
                    GROUP BY s.id, s.name, c.name, f.total_fees, f.bus_fee
                    HAVING arrears > 500
                    ORDER BY arrears DESC
                """)
                self.high_arrears_table.setRowCount(len(high_arrears))
                for row, (id, name, class_name, arrears) in enumerate(high_arrears):
                    self.high_arrears_table.setItem(row, 0, QTableWidgetItem(str(id)))
                    self.high_arrears_table.setItem(row, 1, QTableWidgetItem(name or ""))
                    self.high_arrears_table.setItem(row, 2, QTableWidgetItem(class_name or ""))
                    self.high_arrears_table.setItem(row, 3, QTableWidgetItem(f"KSh {arrears:,.2f}"))
                
                # Logs
                logs = db.fetch_all("SELECT user_id, action, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 10")
                self.logs_table.setRowCount(len(logs))
                for row, (user_id, action, timestamp) in enumerate(logs):
                    self.logs_table.setItem(row, 0, QTableWidgetItem(str(user_id) if user_id else ""))
                    self.logs_table.setItem(row, 1, QTableWidgetItem(action or ""))
                    self.logs_table.setItem(row, 2, QTableWidgetItem(str(timestamp) if timestamp else ""))
                
                self.progress_bar.setValue(100)
        except Exception as e:
            logging.error(f"Error loading dashboard data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load dashboard: {str(e)}")

    def add_class(self):
        try:
            class_name = self.class_combo.currentText() or "New Class"
            with DBManager() as db:
                db.execute("INSERT OR IGNORE INTO classes (name) VALUES (?)", (class_name,))
            self.load_classes()
            self.load_data()
            QMessageBox.information(self, "Success", f"Class {class_name} added/updated")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add class: {str(e)}")

    def delete_class(self):
        try:
            class_name = self.class_combo.currentText()
            if class_name:
                reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {class_name}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    with DBManager() as db:
                        db.execute("DELETE FROM classes WHERE name = ?", (class_name,))
                    self.load_classes()
                    self.load_data()
                    QMessageBox.information(self, "Success", f"Class {class_name} deleted")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete class: {str(e)}")

    def add_user(self):
        try:
            username, ok1 = QInputDialog.getText(self, "Add User", "Enter username:")
            if not ok1 or not username:
                return
            password, ok2 = QInputDialog.getText(self, "Add User", "Enter password:", QLineEdit.EchoMode.Password)
            if not ok2 or not password:
                return
            role, ok3 = QInputDialog.getItem(self, "Add User", "Select role:", ["admin", "clerk"], 0, False)
            if not ok3 or not role:
                return
            create_user(username, password, role)
            self.load_users()
            self.load_data()  # Refresh logs
            QMessageBox.information(self, "Success", f"User {username} added")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add user: {str(e)}")

    def delete_user(self):
        try:
            selected = self.user_table.currentRow()
            if selected >= 0:
                user_id = int(self.user_table.item(selected, 0).text())
                reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete user ID {user_id}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    with DBManager() as db:
                        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    self.load_users()
                    self.load_data()
                    QMessageBox.information(self, "Success", f"User ID {user_id} deleted")
            else:
                QMessageBox.warning(self, "Warning", "Please select a user to delete")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")