import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMenuBar, QStatusBar, QProgressBar, QToolBar, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer, QEvent
from .student_tab import StudentTab
from .payment_tab import PaymentTab
from .report_tab import ReportTab
from .user_tab import UserTab
from .admin_dashboard import AdminDashboard
from .settings_tab import SettingsTab
import logging
from datetime import datetime

logging.basicConfig(filename='app/logs/main.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"School Management System - {user.get('username', 'User')} ({user.get('role', 'Unknown').title()})")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # Styling
        self.setStyleSheet("""
            QMainWindow { background-color: #ecf0f1; }
            QTabWidget::pane { border: 1px solid #bdc3c7; background-color: white; border-radius: 5px; }
            QTabBar::tab {
                background-color: #3498db; color: white; padding: 10px 15px; margin-right: 2px; border-radius: 5px;
            }
            QTabBar::tab:selected { background-color: #2980b9; border-bottom: 2px solid #2980b9; }
            QStatusBar { background-color: #2c3e50; color: white; }
        """)
        
        self.create_menu_bar()
        greeting = self._greeting(user.get('username', 'User'))
        today = datetime.now().strftime('%B %d, %Y')
        self.statusBar().showMessage(f"{greeting} | {today} | Role: {user.get('role', 'Unknown').title()}")
        self.create_toolbar()
        self.create_tabs()
        
        # Logout timer
        self.logout_timer = QTimer(self)
        self.logout_timer.timeout.connect(self.check_inactivity)
        self.logout_timer.start(300000)  # 5 minutes
        self.last_activity = datetime.now()

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        logout_action = file_menu.addAction('Logout')
        logout_action.triggered.connect(self.logout)
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        help_menu = menubar.addMenu('Help')
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
        help_action = help_menu.addAction('Help')
        help_action.triggered.connect(self.show_help)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        toolbar.setMovable(False)

        # Left: App label
        toolbar_label = QLabel("School Fee Management")
        toolbar.addWidget(toolbar_label)
        toolbar.addSeparator()

        # Right: Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        toolbar.addWidget(logout_btn)

    def create_tabs(self):
        tabs = QTabWidget()
        if self.user.get('role') == 'admin':
            # Dashboard first for admins
            tabs.addTab(AdminDashboard(self.user), "🏠 Dashboard")
            tabs.addTab(StudentTab(self.user), "👥 Students")
            tabs.addTab(PaymentTab(self.user), "💰 Payments")
            tabs.addTab(ReportTab(), "📊 Reports")
            tabs.addTab(UserTab(), "👤 Users")
            tabs.addTab(SettingsTab(), "⚙️ Settings")
            tabs.setCurrentIndex(0)
        else:
            tabs.addTab(StudentTab(self.user), "👥 Students")
            tabs.addTab(PaymentTab(self.user), "💰 Payments")
        self.setCentralWidget(tabs)

    def logout(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?', 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            from .login import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()

    def show_about(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About School Management System",
                         "School Management System v1.0\n\nA comprehensive solution for managing school fees,\n"
                         "student records, and payment tracking.\n\nDeveloped with PyQt6 and SQLite.")

    def show_help(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Help",
                              "Welcome to the School Management System!\n\n"
                              "- Use the Students tab to add/edit students.\n"
                              "- Record payments and print receipts in the Payments tab.\n"
                              "- Admins can manage reports, users, and settings.\n"
                              "- Contact support for assistance.")

    def closeEvent(self, event):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, 'Exit Application', 'Are you sure you want to exit?', 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def check_inactivity(self):
        if (datetime.now() - self.last_activity).total_seconds() > 300:
            self.logout()

    def event(self, event):
        # Fixed: Use QEvent.Type enum values instead of accessing them from the event object
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress):
            self.last_activity = datetime.now()
        return super().event(event)

    def _greeting(self, username: str) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            prefix = "Good morning"
        elif 12 <= hour < 17:
            prefix = "Good afternoon"
        else:
            prefix = "Good evening"
        return f"{prefix} {username}"