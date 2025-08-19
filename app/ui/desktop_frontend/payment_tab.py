from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLineEdit, QPushButton, QDateEdit, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import QDate
from ...core.student_manager import get_all_students
from ...core.payment_manager import record_payment, get_balance
from ...core.receipt_generator import generate_receipt

class PaymentTab(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        layout = QVBoxLayout()
        self.student_combo = QComboBox()
        self.load_students()
        layout.addWidget(self.student_combo)
        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Amount")
        layout.addWidget(self.amount)
        self.method = QComboBox()
        self.method.addItems(["Cash", "Card", "Bank Transfer"])
        layout.addWidget(self.method)
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        layout.addWidget(self.date)
        add_btn = QPushButton("Record Payment")
        add_btn.clicked.connect(self.add_payment)
        layout.addWidget(add_btn)
        self.setLayout(layout)

    def load_students(self):
        students = get_all_students()
        for student in students:
            self.student_combo.addItem(f"{student[2]} ({student[1]})", student[0])

    def add_payment(self):
        try:
            student_id = self.student_combo.currentData()
            amount = float(self.amount.text())
            method = self.method.currentText()
            date = self.date.date().toString("yyyy-MM-dd")
            payment_id = record_payment(student_id, amount, method, date, self.user['id'])
            receipt = generate_receipt(payment_id)
            QMessageBox.information(self, "Success", f"Payment recorded. Receipt: {receipt}")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid amount")