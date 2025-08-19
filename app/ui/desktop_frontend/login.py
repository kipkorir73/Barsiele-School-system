from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
from ...core.auth import validate_login
from .main import MainWindow

class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 200)
        
        self.username = QLineEdit(self)
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit(self)
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_btn = QPushButton("Login", self)
        
        layout = QVBoxLayout()
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)
        
        self.login_btn.clicked.connect(self.login)
        self.password.returnPressed.connect(self.login)

    def login(self):
        try:
            user = validate_login(self.username.text(), self.password.text())
            if user:
                self.close()
                self.main_window = MainWindow(user)
                self.main_window.show()
            else:
                QMessageBox.warning(self, "Error", "Invalid credentials")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")