from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDateEdit, QPushButton, QMessageBox
from PyQt6.QtCore import QDate
from ...core.report_manager import generate_payment_summary

class ReportTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        layout.addWidget(self.start_date)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        layout.addWidget(self.end_date)
        gen_btn = QPushButton("Generate Summary")
        gen_btn.clicked.connect(self.generate)
        layout.addWidget(gen_btn)
        self.setLayout(layout)

    def generate(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        filename = generate_payment_summary(start, end)
        QMessageBox.information(self, "Success", f"Report generated: {filename}")