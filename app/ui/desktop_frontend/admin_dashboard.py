from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QComboBox, QProgressBar, QLineEdit, QMessageBox, QInputDialog, QDialog, QFrame, QGridLayout, QScrollArea
from PyQt6.QtCore import Qt
from ...core.db_manager import DBManager
from ...core.fee_manager import (
    set_class_term_fee,
    get_class_term_fee,
    set_bus_location,
    get_bus_locations,
    set_boarding_fee_for_class,
    set_food_requirements,
    get_food_requirements,
)
from ...core.student_manager import get_all_students
from ...core.student_manager import create_student, update_student, get_student
from ...core.auth import Auth  # Use Auth class
from ...core.payment_manager import get_balance  # Import the missing function
from .user_management import UserManagementDialog
from .arrears_detail import ArrearsDetailDialog, HighArrearsDialog
from .activity_logs import ActivityLogsDialog
import logging
import time
from datetime import datetime

logging.basicConfig(filename='app/logs/admin.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AdminDashboard(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setStyleSheet("""
            QWidget { background-color: #f8f9fa; }
            QLabel { color: #2c3e50; font-size: 14px; font-weight: bold; }
            QTableWidget { 
                border: 2px solid #3498db; 
                background-color: white; 
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
            }
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                border-radius: 8px; 
                padding: 12px 20px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #2471a3; }
            QComboBox, QLineEdit { 
                border: 2px solid #3498db; 
                border-radius: 8px; 
                padding: 8px; 
                background-color: white; 
                font-size: 14px;
            }
            QComboBox:focus, QLineEdit:focus { border-color: #2980b9; }
            QProgressBar { 
                border: 2px solid #3498db; 
                border-radius: 8px; 
                text-align: center; 
                font-weight: bold;
            }
        """)
        
        # Use a scroll area to allow vertical scrolling when content overflows
        outer_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        # School Header
        school_header = QLabel("Barsiele Sunrise Academy")
        school_header.setStyleSheet("font-size: 28px; font-weight: bold; color: #3498db; margin-bottom: 5px;")
        school_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(school_header)
        
        school_info = QLabel("P.O Box 117 LONDIANI")
        school_info.setStyleSheet("font-size: 16px; color: #7f8c8d; margin-bottom: 5px;")
        school_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(school_info)
        
        motto = QLabel("Together we Rise")
        motto.setStyleSheet("font-size: 18px; font-style: italic; color: #3498db; margin-bottom: 20px;")
        motto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(motto)

        # Greeting header
        greeting = self._greeting(self.user.get('username', 'Admin'))
        self.header = QLabel(greeting)
        self.header.setStyleSheet("font-size:18px; font-weight:bold; color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(self.header)
        
        # Management Cards
        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(8)
        cards_layout.setVerticalSpacing(8)
        cards_layout.setContentsMargins(6, 6, 6, 6)
        
        # User Management Card
        user_mgmt_card = self._create_management_card("User Management", "Manage admin and clerk accounts", self.open_user_management)
        cards_layout.addWidget(user_mgmt_card, 0, 0)
        
        # Arrears Management Card
        arrears_card = self._create_management_card("Arrears Details", "View detailed arrears by class", self.open_arrears_detail)
        cards_layout.addWidget(arrears_card, 0, 1)
        
        # High Arrears Card
        high_arrears_card = self._create_management_card("High Arrears", "Students with arrears > KSh 1,000", self.open_high_arrears)
        cards_layout.addWidget(high_arrears_card, 0, 2)
        
        # Activity Logs Card
        logs_card = self._create_management_card("Activity Logs", "View system activity and login logs", self.open_activity_logs)
        cards_layout.addWidget(logs_card, 1, 0)
        
        # Food Collection Overview Card
        food_card = self._create_management_card("Food Collection", "Totals collected vs required; see classes with biggest deficit", self.open_food_overview)
        cards_layout.addWidget(food_card, 1, 1)
        
        layout.addLayout(cards_layout)
        
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

        # KPI cards removed per request to simplify dashboard
        
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

        # Progress Bar (moved to bottom below logs summary)

        # Food Requirements and Boarding Fee Controls
        controls = QHBoxLayout()
        # Food requirements
        self.food_maize = QLineEdit(); self.food_maize.setPlaceholderText("Maize kg")
        self.food_beans = QLineEdit(); self.food_beans.setPlaceholderText("Beans kg")
        self.food_millet = QLineEdit(); self.food_millet.setPlaceholderText("Millet kg")
        save_food_btn = QPushButton("Save Food Requirements")
        save_food_btn.clicked.connect(self.save_food_requirements)
        controls.addWidget(QLabel("Food (per class):"))
        controls.addWidget(self.food_maize)
        controls.addWidget(self.food_beans)
        controls.addWidget(self.food_millet)
        controls.addWidget(save_food_btn)
        # Boarding fee
        self.boarding_amount = QLineEdit(); self.boarding_amount.setPlaceholderText("Boarding fee")
        apply_boarding_btn = QPushButton("Apply Boarding Fee to Class")
        apply_boarding_btn.clicked.connect(self.apply_boarding_fee)
        controls.addWidget(QLabel(" | Boarding:"))
        controls.addWidget(self.boarding_amount)
        controls.addWidget(apply_boarding_btn)
        layout.addLayout(controls)

        # Load existing food requirements for selected class initially
        self.class_combo.currentTextChanged.connect(self.load_food_requirements)
        self.load_food_requirements()
        
        # Move Recent Actions Summary to the bottom of the page
        layout.addWidget(QLabel("Recent Actions Summary:"))
        self.logs_summary = QLabel("Loading recent activity...")
        self.logs_summary.setStyleSheet("padding: 10px; background-color: #ecf0f1; border-radius: 5px; margin-bottom: 10px;")
        layout.addWidget(self.logs_summary)
        
        # Progress Bar - bottom most
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        self.load_data()

    def load_classes(self):
        with DBManager() as db:
            classes = db.fetch_all("SELECT name FROM classes")
            self.class_combo.clear()
            self.class_combo.addItems([c[0] for c in classes])

    def _create_management_card(self, title, description, click_handler):
        """Create a clickable management card"""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame { 
                background: white; 
                border: 1px solid #3498db; 
                border-radius: 6px; 
                padding: 8px;
                margin: 2px;
            }
            QFrame:hover { 
                background: #f0f6ff; 
                border-color: #2980b9;
            }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db; margin-bottom: 4px;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11px; color: #7f8c8d; margin-bottom: 4px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Make the card clickable
        card.mousePressEvent = lambda event: click_handler()
        
        return card
    
    def open_user_management(self):
        dialog = UserManagementDialog(self)
        dialog.exec()
        
    def open_arrears_detail(self):
        dialog = ArrearsDetailDialog(parent=self)
        dialog.exec()
        
    def open_high_arrears(self):
        dialog = HighArrearsDialog(self)
        dialog.exec()
        
    def open_activity_logs(self):
        dialog = ActivityLogsDialog(self)
        dialog.exec()

    def open_food_overview(self):
        """Show totals collected vs required overall and per class, with deficits."""
        try:
            with DBManager() as db:
                # Validate required tables
                tables = {row[0] for row in db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")}
                if not {'classes', 'students', 'contributions', 'food_requirements'} <= tables:
                    QMessageBox.warning(self, "Unavailable", "Food tracking tables are missing.")
                    return

                classes = db.fetch_all("SELECT id, name FROM classes ORDER BY name")

                # Build per-class student counts
                counts = {cid: 0 for cid, _ in classes}
                for (cid,) in db.fetch_all("SELECT class_id FROM students WHERE class_id IS NOT NULL"):
                    if cid in counts:
                        counts[cid] += 1

                # Requirements per class (per-student quotas x student count)
                req_map = {cid: {'maize': 0.0, 'beans': 0.0, 'millet': 0.0} for cid, _ in classes}
                for (cid, maize, beans, millet) in db.fetch_all("SELECT class_id, maize_kg, beans_kg, millet_kg FROM food_requirements"):
                    if cid in counts and cid in req_map:
                        req_map[cid]['maize'] = float(maize or 0) * counts[cid]
                        req_map[cid]['beans'] = float(beans or 0) * counts[cid]
                        req_map[cid]['millet'] = float(millet or 0) * counts[cid]

                # Collected per class from contributions
                coll_map = {cid: {'maize': 0.0, 'beans': 0.0, 'millet': 0.0} for cid, _ in classes}
                rows = db.fetch_all(
                    """
                    SELECT s.class_id, c.item, SUM(c.quantity)
                    FROM contributions c
                    JOIN students s ON s.id = c.student_id
                    WHERE s.class_id IS NOT NULL
                    GROUP BY s.class_id, c.item
                    """
                )
                for (cid, item, qty) in rows:
                    key = (item or '').strip().lower()
                    if cid in coll_map and key in coll_map[cid]:
                        coll_map[cid][key] += float(qty or 0)

                # Overall totals
                total_req = {'maize': 0.0, 'beans': 0.0, 'millet': 0.0}
                total_coll = {'maize': 0.0, 'beans': 0.0, 'millet': 0.0}
                for cid, _ in classes:
                    for k in total_req:
                        total_req[k] += req_map[cid][k]
                        total_coll[k] += coll_map[cid][k]

            # Build dialog UI
            d = QDialog(self)
            d.setWindowTitle("Food Collection Overview")
            v = QVBoxLayout(d)

            # Overall table
            v.addWidget(QLabel("Overall Totals:"))
            overall = QTableWidget(3, 4)
            overall.setHorizontalHeaderLabels(["Item", "Required (kg)", "Collected (kg)", "Remaining (kg)"])
            items = ["maize", "beans", "millet"]
            for r, it in enumerate(items):
                req = total_req[it]
                coll = total_coll[it]
                rem = max(0.0, req - coll)
                overall.setItem(r, 0, QTableWidgetItem(it.capitalize()))
                overall.setItem(r, 1, QTableWidgetItem(f"{req:g}"))
                overall.setItem(r, 2, QTableWidgetItem(f"{coll:g}"))
                overall.setItem(r, 3, QTableWidgetItem(f"{rem:g}"))
            v.addWidget(overall)

            # Per-class table, ranked by total remaining desc
            v.addWidget(QLabel("Per Class Totals (ranked by deficit):"))
            per_class = QTableWidget(len(classes), 5)
            per_class.setHorizontalHeaderLabels(["Class", "Required (kg)", "Collected (kg)", "Remaining (kg)", "Students"])

            # Compute rankings
            rank_data = []
            for cid, cname in classes:
                req_sum = req_map[cid]['maize'] + req_map[cid]['beans'] + req_map[cid]['millet']
                coll_sum = coll_map[cid]['maize'] + coll_map[cid]['beans'] + coll_map[cid]['millet']
                rem_sum = max(0.0, req_sum - coll_sum)
                rank_data.append((rem_sum, cid, cname, req_sum, coll_sum))
            rank_data.sort(reverse=True)

            per_class.setRowCount(len(rank_data))
            for r, (rem_sum, cid, cname, req_sum, coll_sum) in enumerate(rank_data):
                per_class.setItem(r, 0, QTableWidgetItem(cname))
                per_class.setItem(r, 1, QTableWidgetItem(f"{req_sum:g}"))
                per_class.setItem(r, 2, QTableWidgetItem(f"{coll_sum:g}"))
                per_class.setItem(r, 3, QTableWidgetItem(f"{rem_sum:g}"))
                per_class.setItem(r, 4, QTableWidgetItem(str(counts.get(cid, 0))))
            v.addWidget(per_class)

            close_btn = QPushButton("Close"); close_btn.clicked.connect(d.accept)
            v.addWidget(close_btn)
            d.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Food Overview: {e}")

    def load_data(self):
        try:
            with DBManager() as db:
                # Simulate progress
                for i in range(0, 101, 20):
                    self.progress_bar.setValue(i)
                    time.sleep(0.1)
                
                # KPI calculations removed
                students = get_all_students()

                # Keep header clean
                self.header.setText(self._greeting(self.user.get('username', 'Admin')))
                
                # Class-wise Arrears (handle pre-migration DBs that may not have boarding_fee)
                fees_cols = db.fetch_all("PRAGMA table_info(fees)")
                has_boarding = any(col[1] == 'boarding_fee' for col in fees_cols)
                amount_expr = "COALESCE(f.total_fees, 0) + COALESCE(f.bus_fee, 0)"
                if has_boarding:
                    amount_expr += " + COALESCE(f.boarding_fee, 0)"
                class_arrears = db.fetch_all(f"""
                    SELECT c.name,
                           COUNT(s.id) as num_students,
                           SUM({amount_expr} - 
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
                
                # Logs summary (replace old table usage)
                logs = db.fetch_all("SELECT user_id, action, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 5")
                summary_lines = []
                for (user_id, action, timestamp) in logs:
                    summary_lines.append(f"{timestamp} - User {user_id or 'N/A'}: {action}")
                self.logs_summary.setText("\n".join(summary_lines) if summary_lines else "No recent activity.")
                
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
            # Single-accent color for consistency
            color = "#3498db"
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

    def load_food_requirements(self):
        try:
            class_name = self.class_combo.currentText()
            if not class_name:
                return
            with DBManager() as db:
                row = db.fetch_one("SELECT id FROM classes WHERE name = ?", (class_name,))
            if not row:
                return
            class_id = row[0]
            req = get_food_requirements(class_id)
            self.food_maize.setText(str(req.get('maize_kg', 0)))
            self.food_beans.setText(str(req.get('beans_kg', 0)))
            self.food_millet.setText(str(req.get('millet_kg', 0)))
        except Exception as e:
            logging.error(f"Failed loading food requirements: {e}")

    def save_food_requirements(self):
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
            maize = float(self.food_maize.text() or 0)
            beans = float(self.food_beans.text() or 0)
            millet = float(self.food_millet.text() or 0)
            set_food_requirements(class_id, maize, beans, millet)
            QMessageBox.information(self, "Saved", f"Saved food requirements for {class_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save food requirements: {str(e)}")

    def apply_boarding_fee(self):
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
            amount = float(self.boarding_amount.text() or 0)
            set_boarding_fee_for_class(class_id, amount)
            QMessageBox.information(self, "Saved", f"Applied boarding fee KSh {amount:,.2f} to {class_name}")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply boarding fee: {str(e)}")

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