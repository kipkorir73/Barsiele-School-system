from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QDateEdit, QMessageBox, QFormLayout, QLabel, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QFrame
from PyQt6.QtCore import QDate
from ...core.student_manager import get_all_students
from ...core.payment_manager import record_payment, get_balance
from ...core.receipt_generator import generate_receipt
from ...core.config import DEFAULT_RATES
import logging
import os
from ...core.db_manager import DBManager

logging.basicConfig(filename='app/logs/payment.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PaymentTab(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setStyleSheet("""
            QWidget { background-color: #ecf0f1; }
            QFormLayout { margin: 10px; }
            QLabel { color: #2c3e50; }
            QDoubleSpinBox, QComboBox { border: 2px solid #3498db; border-radius: 5px; padding: 5px; background-color: white; }
            QPushButton { background-color: #2ecc71; color: white; border-radius: 5px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #27ae60; }
            QTableWidget { border: 1px solid #bdc3c7; background-color: white; }
        """)
        
        layout = QVBoxLayout()
        # Header: Clerk and date
        header = QHBoxLayout()
        self.header_label = QLabel(f"Clerk: {self.user.get('username', 'User')}")
        self.date_label = QLabel(QDate.currentDate().toString('MMMM d, yyyy'))
        header.addWidget(self.header_label)
        header.addStretch(1)
        header.addWidget(self.date_label)
        layout.addLayout(header)
        form_layout = QFormLayout()
        
        self.student_combo = QComboBox()
        self.load_students()
        form_layout.addRow("Student:", self.student_combo)
        
        self.amount = QDoubleSpinBox()
        self.amount.setMaximum(999999.99)
        self.amount.setDecimals(2)
        form_layout.addRow("Amount (KSh):", self.amount)
        
        self.method = QComboBox()
        self.method.addItems(["Cash", "M-Pesa", "Bank Transfer", "Cheque", "Maize", "Millet", "Beans"])
        form_layout.addRow("Payment Method:", self.method)
        
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date)
        # Quick range filter for history
        self.filter_start = QDate.currentDate().addDays(-7)
        self.filter_end = QDate.currentDate()
        
        self.balance_label = QLabel("Balance: KSh 0.00")
        form_layout.addRow("Current Balance:", self.balance_label)
        self.student_combo.currentTextChanged.connect(self.update_balance)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Record Payment")
        add_btn.clicked.connect(self.add_payment)
        btn_layout.addWidget(add_btn)
        
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(7)
        self.payment_table.setHorizontalHeaderLabels(["ID", "Student ID", "Amount", "Method", "Date", "Clerk", "Receipt No"])
        self.payment_table.setSortingEnabled(True)
        self.load_payments()
        layout.addWidget(self.payment_table)
        
        print_btn = QPushButton("Print Selected Receipt")
        print_btn.clicked.connect(self.print_receipt)
        btn_layout.addWidget(print_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.update_balance()

    def load_students(self):
        try:
            self.student_combo.clear()
            students = get_all_students()
            for student in students:
                self.student_combo.addItem(f"{student[2]} ({student[1]}) - {student[6]}", student[0])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load students: {str(e)}")

    def update_balance(self):
        try:
            student_id = self.student_combo.currentData()
            if student_id:
                balance = get_balance(student_id)
                self.balance_label.setText(f"Balance: KSh {balance:,.2f}")
            else:
                self.balance_label.setText("Balance: KSh 0.00")
        except Exception as e:
            self.balance_label.setText("Balance: Error loading")

    def load_payments(self):
        try:
            with DBManager() as db:
                payments = db.fetch_all("SELECT * FROM payments ORDER BY date DESC, id DESC LIMIT 20")
                self.payment_table.setRowCount(len(payments))
                for row, payment in enumerate(payments):
                    for col, data in enumerate(payment):
                        if col == 2:
                            self.payment_table.setItem(row, col, QTableWidgetItem(f"KSh {data:,.2f}"))
                        else:
                            self.payment_table.setItem(row, col, QTableWidgetItem(str(data or "")))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load payments: {str(e)}")

    def add_payment(self):
        try:
            student_id = self.student_combo.currentData()
            if not student_id:
                QMessageBox.warning(self, "Warning", "Please select a student")
                return
                
            amount = self.amount.value()
            if amount <= 0:
                QMessageBox.warning(self, "Warning", "Amount must be greater than 0")
                return
                
            method = self.method.currentText()
            date = self.date.date().toString("yyyy-MM-dd")
            # For in-kind, convert quantity to cash equivalent for balances and store both
            if method in ['Maize', 'Millet', 'Beans']:
                cash_equiv = amount * DEFAULT_RATES[method.lower()]
                payment_id, receipt_no = record_payment(student_id, cash_equiv, method, date, self.user['id'])
                with DBManager() as db:
                    db.execute("INSERT INTO contributions (student_id, item, quantity, cash_equivalent) VALUES (?, ?, ?, ?)",
                              (student_id, method, amount, cash_equiv))
            else:
                payment_id, receipt_no = record_payment(student_id, amount, method, date, self.user['id'])
            
            self.amount.setValue(0)
            self.update_balance()
            self.load_payments()
            QMessageBox.information(self, "Success", f"Payment recorded successfully!\nReceipt No: {receipt_no}")
            receipt_file = generate_receipt(payment_id, receipt_no)
            if receipt_file:
                QMessageBox.information(self, "Receipt", f"Receipt generated: {receipt_file}\nOpen it?")
                if QMessageBox.question(self, "Open Receipt", "Open the receipt now?", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    os.startfile(receipt_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}")

    def print_receipt(self):
        try:
            selected = self.payment_table.currentRow()
            if selected >= 0:
                payment_id = int(self.payment_table.item(selected, 0).text())
                receipt_no = self.payment_table.item(selected, 6).text()
                with DBManager() as db:
                    receipt = db.fetch_one("SELECT filename FROM receipts WHERE payment_id = ? AND receipt_no = ?", (payment_id, receipt_no))
                    if receipt and receipt[0]:
                        os.startfile(receipt[0])  # Opens the PDF
                        QMessageBox.information(self, "Success", f"Printing receipt: {receipt[0]}")
                    else:
                        QMessageBox.warning(self, "Warning", "Receipt not found. Generate it first.")
            else:
                QMessageBox.warning(self, "Warning", "Please select a payment to print")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print receipt: {str(e)}")