from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QFormLayout, QFileDialog, QDialog, QMessageBox, QLabel, QComboBox
from PyQt6.QtCore import Qt
from ...core.student_manager import get_all_students, create_student, update_student, get_student, search_students, get_highest_admission_number
from ...core.fee_manager import set_fee, get_fee
from ...core.payment_manager import get_payments_for_student, get_balance
from ...core.config import BUS_FEES
import logging

logging.basicConfig(filename='app/logs/student.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StudentTab(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
            }
            QTableWidget {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QLineEdit, QComboBox {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #e67e22;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        
        layout = QVBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or admission number")
        self.search.textChanged.connect(self.load_students)
        layout.addWidget(self.search)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Adm No", "Name", "Class", "Guardian", "Bus Location"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Student")
        add_btn.clicked.connect(self.add_student)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit Student")
        edit_btn.clicked.connect(self.edit_student)
        btn_layout.addWidget(edit_btn)
        
        view_btn = QPushButton("View Profile")
        view_btn.clicked.connect(self.view_profile)
        btn_layout.addWidget(view_btn)
        
        delete_btn = QPushButton("Delete Student")
        delete_btn.clicked.connect(self.delete_student)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.load_students()

    def load_students(self):
        try:
            students = search_students(self.search.text())
            self.table.setRowCount(len(students))
            for row, student in enumerate(students):
                for col, data in enumerate(student[:6] + (student[6],)):
                    self.table.setItem(row, col, QTableWidgetItem(str(data or "")))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load students: {str(e)}")

    def add_student(self):
        dialog = StudentFormDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                values = dialog.get_values()
                adm_no = get_highest_admission_number()
                adm_no = self.increment_admission_number(adm_no)
                values['admission_number'] = adm_no
                student_id = create_student(**values)
                set_fee(student_id, dialog.get_fee(), dialog.get_bus_fee())
                self.load_students()
                QMessageBox.information(self, "Success", "Student added successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add student: {str(e)}")

    def edit_student(self):
        selected = self.table.currentRow()
        if selected >= 0:
            try:
                student_id = int(self.table.item(selected, 0).text())
                student = get_student(student_id)
                current_fee = get_fee(student_id)
                dialog = StudentFormDialog(student, current_fee['total_fees'], current_fee['bus_fee'])
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    values = dialog.get_values()
                    update_student(student_id, **values)
                    set_fee(student_id, dialog.get_fee(), dialog.get_bus_fee())
                    self.load_students()
                    QMessageBox.information(self, "Success", "Student updated successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to edit student: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a student to edit")

    def view_profile(self):
        selected = self.table.currentRow()
        if selected >= 0:
            try:
                student_id = int(self.table.item(selected, 0).text())
                student = get_student(student_id)
                payments = get_payments_for_student(student_id)
                balance = get_balance(student_id)
                total_fee = get_fee(student_id)
                profile = StudentProfileDialog(student, payments, balance, total_fee)
                profile.exec()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to view profile: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a student to view")

    def delete_student(self):
        selected = self.table.currentRow()
        if selected >= 0:
            try:
                student_id = int(self.table.item(selected, 0).text())
                reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this student?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    with DBManager() as db:
                        db.execute("DELETE FROM students WHERE id = %s", (student_id,))
                    self.load_students()
                    QMessageBox.information(self, "Success", "Student deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete student: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a student to delete")

    def increment_admission_number(self, adm_no):
        prefix = adm_no[:3]
        num = int(adm_no[3:])
        return f"{prefix}{str(num + 1).zfill(3)}"

class StudentFormDialog(QDialog):
    def __init__(self, student=None, current_fee=0.0, current_bus_fee=0.0):
        super().__init__()
        self.student = student
        self.setWindowTitle("Add Student" if not student else "Edit Student")
        self.setGeometry(100, 100, 400, 350)
        self.setStyleSheet("""
            QDialog {
                background-color: #ecf0f1;
            }
            QLineEdit, QSpinBox, QComboBox {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        layout = QFormLayout()
        self.adm_no = QLineEdit()
        self.name = QLineEdit()
        self.class_ = QComboBox()
        self.guardian = QLineEdit()
        self.picture = QLineEdit()
        self.fee = QSpinBox()
        self.fee.setMaximum(999999)
        self.fee.setValue(int(current_fee))
        self.bus_fee = QComboBox()
        self.bus_fee.addItems(list(BUS_FEES.keys()) + ["None"])
        self.bus_fee.setCurrentText(student[6] if student and student[6] in BUS_FEES else "None")
        
        browse_btn = QPushButton("Browse Picture")
        browse_btn.clicked.connect(self.browse_picture)
        
        layout.addRow("Admission No*", self.adm_no)
        layout.addRow("Name*", self.name)
        self.load_classes()
        layout.addRow("Class*", self.class_)
        layout.addRow("Guardian Contact", self.guardian)
        layout.addRow("Total Fee", self.fee)
        layout.addRow("Bus Location", self.bus_fee)
        
        pic_layout = QHBoxLayout()
        pic_layout.addWidget(self.picture)
        pic_layout.addWidget(browse_btn)
        layout.addRow("Profile Picture", pic_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)
        
        if student:
            self.adm_no.setText(student[1] or "")
            self.name.setText(student[2] or "")
            self.class_.setCurrentText(student[6] or "")
            self.guardian.setText(student[4] or "")
            self.picture.setText(student[5] or "")

    def load_classes(self):
        with DBManager() as db:
            classes = db.fetch_all("SELECT name FROM classes")
            self.class_.addItems([c[0] for c in classes])

    def browse_picture(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.picture.setText(file)

    def save(self):
        if not self.adm_no.text().strip() or not self.name.text().strip() or not self.class_.currentText():
            QMessageBox.warning(self, "Warning", "Please fill all required fields (marked with *)")
            return
        self.accept()

    def get_values(self):
        bus_location = self.bus_fee.currentText() if self.bus_fee.currentText() != "None" else None
        return {
            "admission_number": self.adm_no.text().strip(),
            "name": self.name.text().strip(),
            "class_id": self.get_class_id(self.class_.currentText()),
            "guardian_contact": self.guardian.text().strip(),
            "profile_picture": self.picture.text().strip() if self.picture.text().strip() else None,
            "bus_location": bus_location
        }

    def get_class_id(self, class_name):
        with DBManager() as db:
            result = db.fetch_one("SELECT id FROM classes WHERE name = %s", (class_name,))
            return result[0] if result else None

    def get_fee(self):
        return float(self.fee.value())

    def get_bus_fee(self):
        return BUS_FEES.get(self.bus_fee.currentText(), 0.0) if self.bus_fee.currentText() != "None" else 0.0

class StudentProfileDialog(QDialog):
    def __init__(self, student, payments, balance, total_fee):
        super().__init__()
        self.setWindowTitle(f"Student Profile - {student[2]}")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ecf0f1;
            }
            QFormLayout {
                margin: 10px;
            }
            QLabel {
                color: #2c3e50;
            }
            QTableWidget {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        layout = QVBoxLayout()
        details_layout = QFormLayout()
        details_layout.addRow("ID:", QLabel(str(student[0])))
        details_layout.addRow("Admission No:", QLabel(student[1] or ""))
        details_layout.addRow("Name:", QLabel(student[2] or ""))
        details_layout.addRow("Class:", QLabel(student[6] or ""))
        details_layout.addRow("Guardian:", QLabel(student[4] or ""))
        if student[5]:
            details_layout.addRow("Picture:", QLabel(student[5]))
        layout.addLayout(details_layout)
        
        fee_layout = QFormLayout()
        fee_layout.addRow("Total Fee:", QLabel(f"KSh {total_fee['total_fees']:,.2f}"))
        fee_layout.addRow("Bus Fee:", QLabel(f"KSh {total_fee['bus_fee']:,.2f}"))
        total_paid = total_fee['total_fees'] + total_fee['bus_fee'] - balance
        fee_layout.addRow("Total Paid:", QLabel(f"KSh {total_paid:,.2f}"))
        fee_layout.addRow("Balance:", QLabel(f"KSh {balance:,.2f}"))
        layout.addLayout(fee_layout)
        
        layout.addWidget(QLabel("Payment History:"))
        payment_table = QTableWidget(len(payments), 5)
        payment_table.setHorizontalHeaderLabels(["Amount", "Method", "Date", "Clerk ID", "Receipt No"])
        for r, p in enumerate(payments):
            payment_table.setItem(r, 0, QTableWidgetItem(f"KSh {p[2]:,.2f}"))
            payment_table.setItem(r, 1, QTableWidgetItem(p[3] or ""))
            payment_table.setItem(r, 2, QTableWidgetItem(p[4] or ""))
            payment_table.setItem(r, 3, QTableWidgetItem(str(p[5]) if p[5] else ""))
            payment_table.setItem(r, 4, QTableWidgetItem(p[6] or ""))
        layout.addWidget(payment_table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)