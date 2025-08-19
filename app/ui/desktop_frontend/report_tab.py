from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QDateEdit, QPushButton, 
                             QMessageBox, QFormLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QFileDialog)
from PyQt6.QtCore import QDate
from ...core.report_manager import generate_payment_summary
from ...core.db_manager import DBManager
import os

class ReportTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Date range selection
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
        
        # Generate report button
        gen_btn = QPushButton("Generate Payment Summary")
        gen_btn.clicked.connect(self.generate_summary)
        layout.addWidget(gen_btn)
        
        # Summary display
        self.summary_label = QLabel("Summary will appear here...")
        layout.addWidget(self.summary_label)
        
        # Recent payments table
        layout.addWidget(QLabel("Recent Payments:"))
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(6)
        self.payments_table.setHorizontalHeaderLabels(["ID", "Student ID", "Amount", "Method", "Date", "Clerk"])
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
            
            # Calculate summary statistics
            db = DBManager()
            payments = db.fetch_all("SELECT * FROM payments WHERE date BETWEEN ? AND ?", (start, end))
            db.close()
            
            total_amount = sum(p[2] for p in payments)
            total_count = len(payments)
            
            self.summary_label.setText(
                f"Period: {start} to {end}\n"
                f"Total Payments: {total_count}\n"
                f"Total Amount: KSh {total_amount:,.2f}\n"
                f"Report saved: {filename}"
            )
            
            # Load payments for the period
            self.load_payments_for_period(start, end)
            
            # Ask if user wants to open the file
            reply = QMessageBox.question(self, "Report Generated", 
                                       f"Report generated successfully!\n{filename}\n\nOpen file location?")
            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(os.path.dirname(filename))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

    def load_recent_payments(self):
        try:
            db = DBManager()
            payments = db.fetch_all("""
                SELECT p.id, p.student_id, p.amount, p.method, p.date, p.clerk_id 
                FROM payments p 
                ORDER BY p.date DESC, p.id DESC 
                LIMIT 50
            """)
            db.close()
            
            self.payments_table.setRowCount(len(payments))
            for row, payment in enumerate(payments):
                for col, data in enumerate(payment):
                    if col == 2:  # Amount column
                        self.payments_table.setItem(row, col, QTableWidgetItem(f"KSh {data:,.2f}"))
                    else:
                        self.payments_table.setItem(row, col, QTableWidgetItem(str(data or "")))
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load payments: {str(e)}")

    def load_payments_for_period(self, start_date, end_date):
        try:
            db = DBManager()
            payments = db.fetch_all("""
                SELECT p.id, p.student_id, p.amount, p.method, p.date, p.clerk_id 
                FROM payments p 
                WHERE p.date BETWEEN ? AND ?
                ORDER BY p.date DESC, p.id DESC
            """, (start_date, end_date))
            db.close()
            
            self.payments_table.setRowCount(len(payments))
            for row, payment in enumerate(payments):
                for col, data in enumerate(payment):
                    if col == 2:  # Amount column
                        self.payments_table.setItem(row, col, QTableWidgetItem(f"KSh {data:,.2f}"))
                    else:
                        self.payments_table.setItem(row, col, QTableWidgetItem(str(data or "")))
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load payments for period: {str(e)}")