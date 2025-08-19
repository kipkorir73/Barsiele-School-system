import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from .login import LoginWindow
from .student_tab import StudentTab
from .payment_tab import PaymentTab
from .report_tab import ReportTab
from .user_tab import UserTab

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("School Management System")
        self.setGeometry(100, 100, 800, 600)
        tabs = QTabWidget()
        tabs.addTab(StudentTab(self.user), "Students")
        tabs.addTab(PaymentTab(self.user), "Payments")
        if self.user['role'] == 'admin':
            tabs.addTab(ReportTab(), "Reports")
            tabs.addTab(UserTab(), "Users")
        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())