from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDateEdit, QPushButton, QMessageBox, QFormLayout, QLabel, QTableWidget, QTableWidgetItem, QComboBox
from PyQt6.QtCore import QDate
from ...core.report_manager import generate_payment_summary, generate_class_report
from ...core.db_manager import DBManager
import os
import logging

logging.basicConfig(filename='app/logs/report.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReportTab(QWidget):
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
            QDateEdit, QPushButton {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QTableWidget {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        form_layout.addRow("End Date:", self.end_date)
        
        layout.addLayout(form_layout)

        # Class report
        class_form = QFormLayout()
        self.class_combo = QComboBox()
        self._load_classes()
        class_form.addRow("Class:", self.class_combo)
        class_btn = QPushButton("Generate Class Report")
        class_btn.clicked.connect(self.generate_class_report)
        class_form.addRow(class_btn)
        layout.addLayout(class_form)
        
        gen_btn = QPushButton("Generate Payment Summary")
        gen_btn.clicked.connect(self.generate_summary)
        layout.addWidget(gen_btn)
        
        self.summary_label = QLabel("Summary will appear here...")
        layout.addWidget(self.summary_label)
        
        layout.addWidget(QLabel("Recent Payments:"))
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(7)
        self.payments_table.setHorizontalHeaderLabels(["ID", "Student ID", "Amount", "Method", "Date", "Clerk", "Receipt No"])
        layout.addWidget(self.payments_table)
        
        self.setLayout(layout)
        self.load_recent_payments()

    def generate_summary(self):
        try:
            start = self.start_date.date().toString("yyyy-MM-dd")
            end = self.end_date.date().toString("yyyy-MM-dd")
            if self.start_date.date() > self.end_date.date():
                QMessageBox.warning(self, "Warning", "Start date cannot be after end date")
                return
            filename = generate_payment_summary(start, end)
            with DBManager() as db:
                payments = db.fetch_all("SELECT * FROM payments WHERE date BETWEEN ? AND ?", (start, end))
                total_amount = sum(p[2] for p in payments)
                total_count = len(payments)
            self.summary_label.setText(
                f"Period: {start} to {end}\nTotal Payments: {total_count}\nTotal Amount: KSh {total_amount:,.2f}\nReport saved: {filename}"
            )
            self.load_payments_for_period(start, end)
            reply = QMessageBox.question(self, "Report Generated", f"Report generated!\n{filename}\nOpen file location?")
            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(os.path.dirname(filename))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def load_recent_payments(self):
        try:
            with DBManager() as db:
                payments = db.fetch_all("SELECT * FROM payments ORDER BY date DESC, id DESC LIMIT 50")
                self.payments_table.setRowCount(len(payments))
                for row, payment in enumerate(payments):
                    for col, data in enumerate(payment):
                        if col == 2:
                            self.payments_table.setItem(row, col, QTableWidgetItem(f"KSh {data:,.2f}"))
                        else:
                            self.payments_table.setItem(row, col, QTableWidgetItem(str(data or "")))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load payments: {str(e)}")

    def load_payments_for_period(self, start_date, end_date):
        try:
            with DBManager() as db:
                payments = db.fetch_all("SELECT * FROM payments WHERE date BETWEEN ? AND ? ORDER BY date DESC, id DESC", (start_date, end_date))
                self.payments_table.setRowCount(len(payments))
                for row, payment in enumerate(payments):
                    for col, data in enumerate(payment):
                        if col == 2:
                            self.payments_table.setItem(row, col, QTableWidgetItem(f"KSh {data:,.2f}"))
                        else:
                            self.payments_table.setItem(row, col, QTableWidgetItem(str(data or "")))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load payments for period: {str(e)}")

    def _load_classes(self):
        try:
            with DBManager() as db:
                classes = db.fetch_all("SELECT id, name FROM classes ORDER BY name")
                for cid, cname in classes:
                    self.class_combo.addItem(cname, cid)
        except Exception:
            pass

    def generate_class_report(self):
        try:
            class_id = self.class_combo.currentData()
            if not class_id:
                QMessageBox.warning(self, "Warning", "No class selected")
                return
            filename = generate_class_report(class_id)
            QMessageBox.information(self, "Report", f"Class report saved: {filename}")
            os.startfile(os.path.dirname(filename))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate class report: {str(e)}")