from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QComboBox, QMessageBox
from ...core.auth import create_user

class UserTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        layout.addWidget(self.username)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password)
        self.role = QComboBox()
        self.role.addItems(["admin", "clerk"])
        layout.addWidget(self.role)
        add_btn = QPushButton("Add User")
        add_btn.clicked.connect(self.add_user)
        layout.addWidget(add_btn)
        self.setLayout(layout)

    def add_user(self):
        username = self.username.text()
        pw = self.password.text()
        role = self.role.currentText()
        if username and pw:
            create_user(username, pw, role)
            QMessageBox.information(self, "Success", "User added")
        else:
            QMessageBox.warning(self, "Error", "Fill all fields")