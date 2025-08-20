from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QComboBox, QProgressBar, QLineEdit, QMessageBox, QInputDialog, QDialog, QFrame
from PyQt6.QtCore import Qt
from ...core.db_manager import DBManager
from ...core.fee_manager import set_class_term_fee, get_class_term_fee, set_bus_location, get_bus_locations
from ...core.student_manager import get_all_students
from ...core.student_manager import create_student, update_student, get_student
from ...core.auth import Auth  # Use Auth class
from ...core.payment_manager import get_balance  # Import the missing function
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

        # Greeting header
        greeting = self._greeting(self.user.get('username', 'Admin'))
        self.header = QLabel(greeting)
        self.header.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(self.header)
        
        # Action buttons
        actions = QHBoxLayout()
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_report)
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self.load_data)
        actions.addWidget(export_btn)
        actions.addWidget(refresh_btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        # KPI cards like the screenshot
        kpi_layout = QHBoxLayout()
        self.kpi_paid = self._create_kpi_card("Total Paid This Month", "KSh 0")
        self.kpi_arrears = self._create_kpi_card("Total Arrears", "KSh 0")
        self.kpi_students = self._create_kpi_card("Total Students", "0")
        self.kpi_classes = self._create_kpi_card("Active Classes", "0")
        for card in (self.kpi_paid, self.kpi_arrears, self.kpi_students, self.kpi_classes):
            kpi_layout.addWidget(card)
        layout.addLayout(kpi_layout)
        
        # Class-wise Arrears
        layout.addWidget(QLabel("Arrears by Class:"))
        self.class_arrears_table = QTableWidget()
        self.class_arrears_table.setColumnCount(3)
        self.class_arrears_table.setHorizontalHeaderLabels(["Class", "Students", "Arrears"])
        layout.addWidget(self.class_arrears_table)
        self.class_arrears_table.cellDoubleClicked.connect(self.show_students_for_class)
        
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

        # Per-term fee controls
        self.term_combo = QComboBox()
        self.term_combo.addItems(["Term 1", "Term 2", "Term 3"])
        self.term_amount = QLineEdit()
        self.term_amount.setPlaceholderText("Amount")
        save_term_btn = QPushButton("Save Term Fee")
        save_term_btn.clicked.connect(self.save_term_fee)
        class_layout.addWidget(QLabel(" | Term:"))
        class_layout.addWidget(self.term_combo)
        class_layout.addWidget(self.term_amount)
        class_layout.addWidget(save_term_btn)
        layout.addLayout(class_layout)
        
        # User Management
        user_layout = QHBoxLayout()
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Role"])
        self.load_users()
        user_layout.addWidget(self.user_table)
        
        user_btn_layout = QVBoxLayout()
        add_user_btn = QPushButton("Add User")
        add_user_btn.clicked.connect(self.add_user)
        delete_user_btn = QPushButton("Delete User")
        delete_user_btn.clicked.connect(self.delete_user)
        user_btn_layout.addWidget(add_user_btn)
        user_btn_layout.addWidget(delete_user_btn)
        user_layout.addLayout(user_btn_layout)
        layout.addLayout(user_layout)
        
        # Bus locations management
        bus_layout = QHBoxLayout()
        self.bus_name = QLineEdit()
        self.bus_name.setPlaceholderText("Bus location name")
        self.bus_fee = QLineEdit()
        self.bus_fee.setPlaceholderText("Fee per term")
        save_bus_btn = QPushButton("Save Bus Location")
        save_bus_btn.clicked.connect(self.save_bus_location)
        bus_layout.addWidget(QLabel("Bus Location:"))
        bus_layout.addWidget(self.bus_name)
        bus_layout.addWidget(self.bus_fee)
        bus_layout.addWidget(save_bus_btn)
        layout.addLayout(bus_layout)

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
            self.class_combo.clear()
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
                
                # KPI - Total Paid This Month and trend vs last month
                start_this, end_this = self._month_range(0)
                start_prev, end_prev = self._month_range(-1)
                r_this = db.fetch_one("SELECT SUM(amount) FROM payments WHERE date BETWEEN ? AND ?", (start_this, end_this))
                r_prev = db.fetch_one("SELECT SUM(amount) FROM payments WHERE date BETWEEN ? AND ?", (start_prev, end_prev))
                total_paid_this = r_this[0] if r_this and r_this[0] else 0
                total_paid_prev = r_prev[0] if r_prev and r_prev[0] else 0
                change = 0 if total_paid_prev == 0 else ((total_paid_this - total_paid_prev) / total_paid_prev) * 100
                self._set_kpi_value(self.kpi_paid, f"KSh {total_paid_this:,.0f}", change)
                
                # Total Arrears - calculate from students
                students = get_all_students()
                total_arrears = 0
                for student in students:
                    balance = get_balance(student[0])  # student[0] is the ID
                    if balance > 0:
                        total_arrears += balance
                self._set_kpi_value(self.kpi_arrears, f"KSh {total_arrears:,.0f}")
                
                # Total Contributions
                total_contrib_result = db.fetch_one("SELECT SUM(cash_equivalent) FROM contributions")
                total_contrib = total_contrib_result[0] if total_contrib_result and total_contrib_result[0] else 0
                # Show contributions in header as part of greeting subtitle
                self.header.setText(self._greeting(self.user.get('username', 'Admin')) + f"  |  Contributions: KSh {total_contrib:,.0f}")

                # Total Students and Classes
                count_students = db.fetch_one("SELECT COUNT(*) FROM students")[0]
                count_classes = db.fetch_one("SELECT COUNT(*) FROM classes")[0]
                self._set_kpi_value(self.kpi_students, f"{count_students}")
                self._set_kpi_value(self.kpi_classes, f"{count_classes}")

                # How many should be paid and how much received
                fees_total = db.fetch_one("SELECT SUM(total_fees + bus_fee) FROM fees")[0]
                paid_total = db.fetch_one("SELECT SUM(amount) FROM payments")[0]
                fees_total = fees_total if fees_total else 0
                paid_total = paid_total if paid_total else 0
                remaining = fees_total - paid_total
                # Reuse contributions in header; append school totals
                self.header.setText(self.header.text() + f"  |  Students: {count_students}  |  Should Pay: KSh {fees_total:,.0f}  |  Received: KSh {paid_total:,.0f}  |  Arrears: KSh {remaining:,.0f}")
                
                # Class-wise Arrears
                class_arrears = db.fetch_all("""
                    SELECT c.name,
                           COUNT(s.id) as num_students,
                           SUM(COALESCE(f.total_fees, 0) + COALESCE(f.bus_fee, 0) - 
                               COALESCE((SELECT SUM(amount) FROM payments p WHERE p.student_id = s.id), 0)) as arrears
                    FROM classes c
                    LEFT JOIN students s ON c.id = s.class_id
                    LEFT JOIN fees f ON s.id = f.student_id
                    GROUP BY c.name
                """)
                self.class_arrears_table.setRowCount(len(class_arrears))
                for row, (class_name, num_students, arrears) in enumerate(class_arrears):
                    self.class_arrears_table.setItem(row, 0, QTableWidgetItem(class_name or ""))
                    self.class_arrears_table.setItem(row, 1, QTableWidgetItem(str(num_students or 0)))
                    arrears_value = arrears if arrears and arrears > 0 else 0
                    self.class_arrears_table.setItem(row, 2, QTableWidgetItem(f"KSh {arrears_value:,.2f}"))
                
                # High Arrears Students
                high_arrears_students = []
                for student in students:
                    balance = get_balance(student[0])
                    if balance > 500:
                        high_arrears_students.append((student[0], student[2], student[7], balance))  # id, name, class_name, balance
                
                self.high_arrears_table.setRowCount(len(high_arrears_students))
                for row, (id, name, class_name, arrears) in enumerate(high_arrears_students):
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

    def show_students_for_class(self, row, column):
        try:
            class_name_item = self.class_arrears_table.item(row, 0)
            if not class_name_item:
                return
            class_name = class_name_item.text()
            with DBManager() as db:
                class_row = db.fetch_one("SELECT id FROM classes WHERE name = ?", (class_name,))
                if not class_row:
                    return
                class_id = class_row[0]
                students = db.fetch_all("SELECT admission_number, name FROM students WHERE class_id = ? ORDER BY name", (class_id,))
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Students - {class_name}")
            v = QVBoxLayout(dialog)
            table = QTableWidget(len(students), 2)
            table.setHorizontalHeaderLabels(["Adm No", "Name"])
            for r, s in enumerate(students):
                table.setItem(r, 0, QTableWidgetItem(str(s[0] or "")))
                table.setItem(r, 1, QTableWidgetItem(str(s[1] or "")))
            v.addWidget(table)
            dialog.setLayout(v)
            dialog.resize(400, 300)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show students: {str(e)}")

    def _greeting(self, username: str) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            prefix = "Good morning"
        elif 12 <= hour < 17:
            prefix = "Good afternoon"
        else:
            prefix = "Good evening"
        return f"{prefix} {username}"

    def _create_kpi_card(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("QFrame { background: white; border: 1px solid #bdc3c7; border-radius: 8px; padding: 12px; }")
        v = QVBoxLayout(frame)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color:#7f8c8d; font-size:12px;")
        value_lbl = QLabel(value)
        value_lbl.setObjectName("value")
        value_lbl.setStyleSheet("font-size:22px; font-weight:bold; color:#2c3e50;")
        change_lbl = QLabel("")
        change_lbl.setObjectName("change")
        change_lbl.setStyleSheet("font-size:12px;")
        v.addWidget(title_lbl)
        v.addWidget(value_lbl)
        v.addWidget(change_lbl)
        return frame

    def _set_kpi_value(self, frame: QFrame, value_text: str, change_pct: float | None = None):
        value_lbl = frame.findChild(QLabel, "value")
        change_lbl = frame.findChild(QLabel, "change")
        if value_lbl:
            value_lbl.setText(value_text)
        if change_lbl is not None and change_pct is not None:
            sign = "+" if change_pct >= 0 else ""
            color = "#2ecc71" if change_pct >= 0 else "#e74c3c"
            change_lbl.setText(f"{sign}{change_pct:.1f}% vs last month")
            change_lbl.setStyleSheet(f"font-size:12px; color:{color};")
        elif change_lbl is not None:
            change_lbl.setText("")

    def _month_range(self, relative_month: int):
        # relative_month=0 -> current month, -1 -> previous month
        base = datetime.now()
        year = base.year
        month = base.month + relative_month
        while month <= 0:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        start = datetime(year, month, 1).strftime('%Y-%m-%d')
        # next month start - 1 day
        if month == 12:
            end_dt = datetime(year + 1, 1, 1)
        else:
            end_dt = datetime(year, month + 1, 1)
        end = (end_dt).strftime('%Y-%m-%d')
        return start, end

    def export_report(self):
        try:
            from ...core.report_manager import generate_student_balance_report
            filename = generate_student_balance_report()
            QMessageBox.information(self, "Report", f"Student balance report saved: {filename}")
            import os
            os.startfile(os.path.dirname(filename))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")

    def add_class(self):
        try:
            class_name, ok = QInputDialog.getText(self, "Add Class", "Enter class name:")
            if ok and class_name.strip():
                with DBManager() as db:
                    db.execute("INSERT OR IGNORE INTO classes (name) VALUES (?)", (class_name.strip(),))
                self.load_classes()
                self.load_data()
                QMessageBox.information(self, "Success", f"Class {class_name} added")
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

    def save_term_fee(self):
        try:
            class_name = self.class_combo.currentText()
            if not class_name:
                QMessageBox.warning(self, "Warning", "Select a class first")
                return
            with DBManager() as db:
                row = db.fetch_one("SELECT id FROM classes WHERE name = ?", (class_name,))
                if not row:
                    QMessageBox.warning(self, "Warning", "Unknown class")
                    return
                class_id = row[0]
            term = self.term_combo.currentIndex() + 1
            amount = float(self.term_amount.text() or 0)
            set_class_term_fee(class_id, term, amount)
            QMessageBox.information(self, "Saved", f"Saved fee for {class_name} - Term {term}: KSh {amount:,.2f}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save term fee: {str(e)}")

    def save_bus_location(self):
        try:
            name = self.bus_name.text().strip()
            amount = float(self.bus_fee.text() or 0)
            if not name:
                QMessageBox.warning(self, "Warning", "Enter a bus location name")
                return
            set_bus_location(name, amount)
            QMessageBox.information(self, "Saved", f"Saved bus location {name}: KSh {amount:,.2f} per term")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save bus location: {str(e)}")

    def add_user(self):
        try:
            username, ok1 = QInputDialog.getText(self, "Add User", "Enter username:")
            if not ok1 or not username.strip():
                return
            password, ok2 = QInputDialog.getText(self, "Add User", "Enter password:", QLineEdit.EchoMode.Password)
            if not ok2 or not password:
                return
            role, ok3 = QInputDialog.getItem(self, "Add User", "Select role:", ["admin", "clerk"], 0, False)
            if not ok3 or not role:
                return
            Auth.create_user(username.strip(), password, role)
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
                username = self.user_table.item(selected, 1).text()
                reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete user '{username}'?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    with DBManager() as db:
                        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    self.load_users()
                    self.load_data()
                    QMessageBox.information(self, "Success", f"User '{username}' deleted")
            else:
                QMessageBox.warning(self, "Warning", "Please select a user to delete")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")