from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QComboBox, QLineEdit, QPushButton, 
                             QDateEdit, QMessageBox, QTableWidget, QTableWidgetItem, 
                             QFormLayout, QLabel, QDoubleSpinBox)
from PyQt6.QtCore import QDate
from ...core.student_manager import get_all_students
from ...core.payment_manager import record_payment, get_balance
from ...core.receipt_generator import generate_receipt

class PaymentTab(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        layout = QVBoxLayout()
        
        # Payment form
        form_layout = QFormLayout()
        
        self.student_combo = QComboBox()
        self.load_students()
        form_layout.addRow("Student:", self.student_combo)
        
        self.amount = QDoubleSpinBox()
        self.amount.setMaximum(999999.99)
        self.amount.setDecimals(2)
        form_layout.addRow("Amount (KSh):", self.amount)
        
        self.method = QComboBox()
        self.method.addItems(["Cash", "M-Pesa", "Bank Transfer", "Cheque"])
        form_layout.addRow("Payment Method:", self.method)
        
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date)
        
        # Balance display
        self.balance_label = QLabel("Balance: KSh 0.00")
        form_layout.addRow("Current Balance:", self.balance_label)
        
        layout.addLayout(form_layout)
        
        # Update balance when student changes
        self.student_combo.currentTextChanged.connect(self.update_balance)
        
        # Record payment button
        add_btn = QPushButton("Record Payment")
        add_btn.clicked.connect(self.add_payment)
        layout.addWidget(add_btn)
        
        self.setLayout(layout)
        self.update_balance()

    def load_students(self):
        try:
            self.student_combo.clear()
            students = get_all_students()
            for student in students:
                self.student_combo.addItem(f"{student[2]} ({student[1]})", student[0])
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
            
            payment_id = record_payment(student_id, amount, method, date, self.user['id'])
            receipt = generate_receipt(payment_id)
            
            # Reset form
            self.amount.setValue(0)
            self.update_balance()
            
            QMessageBox.information(self, "Success", f"Payment recorded successfully!\nReceipt saved: {receipt}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}")