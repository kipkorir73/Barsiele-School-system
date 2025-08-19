from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLineEdit, QPushButton, QFormLayout, 
                             QFileDialog, QDialog, QMessageBox, QLabel, QSpinBox)
from PyQt6.QtCore import Qt
from ...core.student_manager import get_all_students, create_student, update_student, get_student, search_students
from ...core.fee_manager import set_fee, get_fee
from ...core.payment_manager import get_payments_for_student, get_balance

class StudentTab(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        layout = QVBoxLayout()
        
        # Search bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or admission number")
        self.search.textChanged.connect(self.load_students)
        layout.addWidget(self.search)
        
        # Students table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Adm No", "Name", "Class", "Guardian"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        # Buttons
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
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.load_students()

    def load_students(self):
        try:
            students = search_students(self.search.text())
            self.table.setRowCount(len(students))
            for row, student in enumerate(students):
                for col, data in enumerate(student[:5]):
                    self.table.setItem(row, col, QTableWidgetItem(str(data or "")))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load students: {str(e)}")

    def add_student(self):
        dialog = StudentFormDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                values = dialog.get_values()
                student_id = create_student(**values)
                set_fee(student_id, dialog.get_fee())
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
                dialog = StudentFormDialog(student, current_fee)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    values = dialog.get_values()
                    update_student(student_id, **values)
                    set_fee(student_id, dialog.get_fee())
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
                
                # Show profile dialog
                profile = StudentProfileDialog(student, payments, balance, total_fee)
                profile.exec()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to view profile: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a student to view")

class StudentFormDialog(QDialog):
    def __init__(self, student=None, current_fee=0.0):
        super().__init__()
        self.student = student
        self.setWindowTitle("Add Student" if not student else "Edit Student")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QFormLayout()
        
        self.adm_no = QLineEdit()
        self.name = QLineEdit()
        self.class_ = QLineEdit()
        self.guardian = QLineEdit()
        self.picture = QLineEdit()
        self.fee = QSpinBox()
        self.fee.setMaximum(999999)
        self.fee.setValue(int(current_fee))
        
        browse_btn = QPushButton("Browse Picture")
        browse_btn.clicked.connect(self.browse_picture)
        
        layout.addRow("Admission No*", self.adm_no)
        layout.addRow("Name*", self.name)
        layout.addRow("Class*", self.class_)
        layout.addRow("Guardian Contact", self.guardian)
        layout.addRow("Total Fee", self.fee)
        
        pic_layout = QHBoxLayout()
        pic_layout.addWidget(self.picture)
        pic_layout.addWidget(browse_btn)
        layout.addRow("Profile Picture", pic_layout)
        
        # Buttons
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
            self.class_.setText(student[3] or "")
            self.guardian.setText(student[4] or "")
            self.picture.setText(student[5] or "")

    def browse_picture(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.picture.setText(file)

    def save(self):
        if not self.adm_no.text().strip() or not self.name.text().strip() or not self.class_.text().strip():
            QMessageBox.warning(self, "Warning", "Please fill all required fields (marked with *)")
            return
        self.accept()

    def get_values(self):
        return {
            "admission_number": self.adm_no.text().strip(),
            "name": self.name.text().strip(),
            "class_": self.class_.text().strip(),
            "guardian_contact": self.guardian.text().strip(),
            "profile_picture": self.picture.text().strip() if self.picture.text().strip() else None
        }

    def get_fee(self):
        return float(self.fee.value())

class StudentProfileDialog(QDialog):
    def __init__(self, student, payments, balance, total_fee):
        super().__init__()
        self.setWindowTitle(f"Student Profile - {student[2]}")
        self.setGeometry(100, 100, 600, 500)
        
        layout = QVBoxLayout()
        
        # Student details
        details_layout = QFormLayout()
        details_layout.addRow("ID:", QLabel(str(student[0])))
        details_layout.addRow("Admission No:", QLabel(student[1] or ""))
        details_layout.addRow("Name:", QLabel(student[2] or ""))
        details_layout.addRow("Class:", QLabel(student[3] or ""))
        details_layout.addRow("Guardian:", QLabel(student[4] or ""))
        if student[5]:
            details_layout.addRow("Picture:", QLabel(student[5]))
        
        layout.addLayout(details_layout)
        
        # Fee information
        fee_layout = QFormLayout()
        fee_layout.addRow("Total Fee:", QLabel(f"KSh {total_fee:,.2f}"))
        total_paid = total_fee - balance
        fee_layout.addRow("Total Paid:", QLabel(f"KSh {total_paid:,.2f}"))
        fee_layout.addRow("Balance:", QLabel(f"KSh {balance:,.2f}"))
        
        layout.addLayout(fee_layout)
        
        # Payment history
        layout.addWidget(QLabel("Payment History:"))
        payment_table = QTableWidget(len(payments), 4)
        payment_table.setHorizontalHeaderLabels(["Amount", "Method", "Date", "Clerk ID"])
        
        for r, p in enumerate(payments):
            payment_table.setItem(r, 0, QTableWidgetItem(f"KSh {p[2]:,.2f}"))
            payment_table.setItem(r, 1, QTableWidgetItem(p[3] or ""))
            payment_table.setItem(r, 2, QTableWidgetItem(p[4] or ""))
            payment_table.setItem(r, 3, QTableWidgetItem(str(p[5]) if p[5] else ""))
        
        layout.addWidget(payment_table)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
