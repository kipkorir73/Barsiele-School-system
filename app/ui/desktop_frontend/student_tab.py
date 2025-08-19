from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QFormLayout, QFileDialog, QDialog, QMessageBox, QLabel
from ...core.student_manager import get_all_students, create_student, update_student, get_student
from ...core.fee_manager import set_fee

class StudentTab(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        layout = QVBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or admission number")
        self.search.textChanged.connect(self.load_students)
        layout.addWidget(self.search)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Adm No", "Name", "Class", "Guardian"])
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
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.load_students()

    def load_students(self):
        students = search_students(self.search.text())
        self.table.setRowCount(len(students))
        for row, student in enumerate(students):
            for col, data in enumerate(student[:5]):
                self.table.setItem(row, col, QTableWidgetItem(str(data)))

    def add_student(self):
        dialog = StudentFormDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            student_id = create_student(**values)
            set_fee(student_id, 0.0)  # Default fee, edit later
            self.load_students()

    def edit_student(self):
        selected = self.table.currentRow()
        if selected >= 0:
            student_id = int(self.table.item(selected, 0).text())
            student = get_student(student_id)
            dialog = StudentFormDialog(student)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                values = dialog.get_values()
                update_student(student_id, **values)
                self.load_students()

    def view_profile(self):
        selected = self.table.currentRow()
        if selected >= 0:
            student_id = int(self.table.item(selected, 0).text())
            student = get_student(student_id)
            # Show profile details, payments, balance
            profile = QDialog(self)
            layout = QVBoxLayout()
            for label, value in zip(["ID", "Adm No", "Name", "Class", "Guardian", "Picture"], student):
                layout.addWidget(QLabel(f"{label}: {value}"))
            # Add payment history table
            payments = get_payments_for_student(student_id)
            balance = get_balance(student_id)
            layout.addWidget(QLabel(f"Balance: {balance}"))
            payment_table = QTableWidget(len(payments), 4)
            payment_table.setHorizontalHeaderLabels(["Amount", "Method", "Date", "Clerk"])
            for r, p in enumerate(payments):
                payment_table.setItem(r, 0, QTableWidgetItem(str(p[2])))
                payment_table.setItem(r, 1, QTableWidgetItem(p[3]))
                payment_table.setItem(r, 2, QTableWidgetItem(p[4]))
                payment_table.setItem(r, 3, QTableWidgetItem(str(p[5])))
            layout.addWidget(payment_table)
            profile.setLayout(layout)
            profile.exec()

class StudentFormDialog(QDialog):
    def __init__(self, student=None):
        super().__init__()
        self.student = student
        layout = QFormLayout()
        self.adm_no = QLineEdit()
        self.name = QLineEdit()
        self.class_ = QLineEdit()
        self.guardian = QLineEdit()
        self.picture = QLineEdit()
        browse_btn = QPushButton("Browse Picture")
        browse_btn.clicked.connect(self.browse_picture)
        layout.addRow("Admission No", self.adm_no)
        layout.addRow("Name", self.name)
        layout.addRow("Class", self.class_)
        layout.addRow("Guardian Contact", self.guardian)
        pic_layout = QHBoxLayout()
        pic_layout.addWidget(self.picture)
        pic_layout.addWidget(browse_btn)
        layout.addRow("Profile Picture", pic_layout)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        layout.addRow(save_btn)
        self.setLayout(layout)
        if student:
            self.adm_no.setText(student[1])
            self.name.setText(student[2])
            self.class_.setText(student[3])
            self.guardian.setText(student[4])
            self.picture.setText(student[5] or "")

    def browse_picture(self):
        file = QFileDialog.getOpenFileName(self, "Select Picture", "", "Images (*.png *.jpg)")[0]
        if file:
            self.picture.setText(file)

    def get_values(self):
        return {
            "admission_number": self.adm_no.text(),
            "name": self.name.text(),
            "class_": self.class_.text(),
            "guardian_contact": self.guardian.text(),
            "profile_picture": self.picture.text()
        }