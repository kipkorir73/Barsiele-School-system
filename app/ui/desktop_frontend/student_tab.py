from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QFormLayout, QFileDialog, QDialog, QMessageBox, QLabel, QComboBox, QSpinBox
from PyQt6.QtCore import Qt
from ...core.student_manager import get_all_students, create_student, update_student, get_student, search_students, get_highest_admission_number
from ...core.fee_manager import set_fee, get_fee
from ...core.payment_manager import get_payments_for_student, get_balance
from ...core.config import BUS_FEES
from ...core.db_manager import DBManager
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
                # student structure: [id, admission_number, name, class_id, guardian_contact, profile_picture, bus_location, class_name]
                self.table.setItem(row, 0, QTableWidgetItem(str(student[0])))  # ID
                self.table.setItem(row, 1, QTableWidgetItem(str(student[1] or "")))  # Admission number
                self.table.setItem(row, 2, QTableWidgetItem(str(student[2] or "")))  # Name
                self.table.setItem(row, 3, QTableWidgetItem(str(student[7] or "")))  # Class name
                self.table.setItem(row, 4, QTableWidgetItem(str(student[4] or "")))  # Guardian contact
                self.table.setItem(row, 5, QTableWidgetItem(str(student[6] or "")))  # Bus location
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load students: {str(e)}")

    def add_student(self):
        dialog = StudentFormDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                values = dialog.get_values()
                # Auto-generate admission number
                highest_adm = get_highest_admission_number()
                new_adm_no = self.increment_admission_number(highest_adm)
                values['admission_number'] = new_adm_no
                student_id = create_student(**values)
                set_fee(student_id, dialog.get_fee(), dialog.get_bus_fee())
                self.load_students()
                QMessageBox.information(self, "Success", f"Student added successfully with admission number: {new_adm_no}")
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
                    # Don't update admission number when editing
                    if 'admission_number' in values:
                        del values['admission_number']
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
                student_name = self.table.item(selected, 2).text()
                reply = QMessageBox.question(self, "Confirm Delete", 
                                           f"Are you sure you want to delete student '{student_name}'?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    with DBManager() as db:
                        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
                    self.load_students()
                    QMessageBox.information(self, "Success", "Student deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete student: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a student to delete")

    def increment_admission_number(self, adm_no):
        if not adm_no or adm_no == "ADM000":
            return "ADM001"
        try:
            # Extract the numeric part
            if adm_no.startswith("ADM"):
                num = int(adm_no[3:])
                return f"ADM{str(num + 1).zfill(3)}"
            else:
                return "ADM001"
        except:
            return "ADM001"

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
        
        self.name = QLineEdit()
        self.name.setPlaceholderText("Enter student name")
        layout.addRow("Name*:", self.name)
        
        self.class_ = QComboBox()
        self.load_classes()
        layout.addRow("Class*:", self.class_)
        
        self.guardian = QLineEdit()
        self.guardian.setPlaceholderText("Enter guardian contact")
        layout.addRow("Guardian Contact:", self.guardian)
        
        self.fee = QSpinBox()
        self.fee.setMaximum(999999)
        self.fee.setValue(int(current_fee))
        layout.addRow("Total Fee (KSh):", self.fee)
        
        self.bus_fee = QComboBox()
        self.bus_fee.addItems(list(BUS_FEES.keys()) + ["None"])
        if student and len(student) > 6 and student[6] in BUS_FEES:
            self.bus_fee.setCurrentText(student[6])
        else:
            self.bus_fee.setCurrentText("None")
        layout.addRow("Bus Location:", self.bus_fee)
        
        self.picture = QLineEdit()
        self.picture.setPlaceholderText("Browse for profile picture")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_picture)
        
        pic_layout = QHBoxLayout()
        pic_layout.addWidget(self.picture)
        pic_layout.addWidget(browse_btn)
        layout.addRow("Profile Picture:", pic_layout)
        
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
            # student structure: [id, admission_number, name, class_id, guardian_contact, profile_picture, bus_location]
            self.name.setText(student[2] or "")
            if len(student) > 3 and student[3]:
                self.set_class_by_id(student[3])
            self.guardian.setText(student[4] or "")
            if len(student) > 5:
                self.picture.setText(student[5] or "")

    def load_classes(self):
        try:
            with DBManager() as db:
                classes = db.fetch_all("SELECT id, name FROM classes ORDER BY name")
                for class_id, class_name in classes:
                    self.class_.addItem(class_name, class_id)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not load classes: {e}")

    def set_class_by_id(self, class_id):
        for i in range(self.class_.count()):
            if self.class_.itemData(i) == class_id:
                self.class_.setCurrentIndex(i)
                break

    def browse_picture(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.picture.setText(file)

    def save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter student name")
            return
        if self.class_.currentData() is None:
            QMessageBox.warning(self, "Warning", "Please select a class")
            return
        self.accept()

    def get_values(self):
        bus_location = self.bus_fee.currentText() if self.bus_fee.currentText() != "None" else None
        return {
            "name": self.name.text().strip(),
            "class_id": self.class_.currentData(),
            "guardian_contact": self.guardian.text().strip() if self.guardian.text().strip() else None,
            "profile_picture": self.picture.text().strip() if self.picture.text().strip() else None,
            "bus_location": bus_location
        }

    def get_fee(self):
        return float(self.fee.value())

    def get_bus_fee(self):
        return BUS_FEES.get(self.bus_fee.currentText(), 0.0) if self.bus_fee.currentText() != "None" else 0.0

class StudentProfileDialog(QDialog):
    def __init__(self, student, payments, balance, total_fee):
        super().__init__()
        self.setWindowTitle(f"Student Profile - {student[2] if len(student) > 2 else 'Unknown'}")
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
        
        # student structure: [id, admission_number, name, class_id, guardian_contact, profile_picture, bus_location]
        details_layout.addRow("ID:", QLabel(str(student[0])))
        details_layout.addRow("Admission No:", QLabel(student[1] or ""))
        details_layout.addRow("Name:", QLabel(student[2] or ""))
        
        # Get class name
        class_name = "Unknown"
        if len(student) > 3 and student[3]:
            try:
                with DBManager() as db:
                    class_result = db.fetch_one("SELECT name FROM classes WHERE id = ?", (student[3],))
                    if class_result:
                        class_name = class_result[0]
            except:
                pass
        details_layout.addRow("Class:", QLabel(class_name))
        
        details_layout.addRow("Guardian:", QLabel(student[4] or ""))
        if len(student) > 5 and student[5]:
            details_layout.addRow("Picture:", QLabel(student[5]))
        if len(student) > 6 and student[6]:
            details_layout.addRow("Bus Location:", QLabel(student[6]))
        
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
            payment_table.setItem(r, 0, QTableWidgetItem(f"KSh {p[2]:,.2f}"))  # amount
            payment_table.setItem(r, 1, QTableWidgetItem(p[3] or ""))  # method
            payment_table.setItem(r, 2, QTableWidgetItem(str(p[4]) if p[4] else ""))  # date
            payment_table.setItem(r, 3, QTableWidgetItem(str(p[5]) if p[5] else ""))  # clerk_id
            payment_table.setItem(r, 4, QTableWidgetItem(p[6] or ""))  # receipt_no
        layout.addWidget(payment_table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)