from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QDialog, QMessageBox, QDateEdit, QComboBox
from PyQt6.QtCore import Qt, QDate
from ...core.db_manager import DBManager
import logging
from datetime import datetime, timedelta

logging.basicConfig(filename='app/logs/activity_logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ActivityLogsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Activity Logs - Barsiele Sunrise Academy")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QLabel { color: #2c3e50; font-size: 14px; font-weight: bold; }
            QTableWidget { 
                border: 2px solid #3498db; 
                background-color: white; 
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
            }
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                border-radius: 8px; 
                padding: 12px 20px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #21618c; }
            QDateEdit, QComboBox { 
                border: 2px solid #3498db; 
                border-radius: 8px; 
                padding: 8px; 
                background-color: white; 
                font-size: 14px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("System Activity Logs")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # School info
        school_info = QLabel("Barsiele Sunrise Academy - P.O Box 117 LONDIANI")
        school_info.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 5px;")
        school_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(school_info)
        
        motto = QLabel("Together we Rise")
        motto.setStyleSheet("font-size: 14px; font-style: italic; color: #7f8c8d; margin-bottom: 20px;")
        motto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(motto)
        
        # Filters
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("From Date:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))  # Default to last 30 days
        self.from_date.setCalendarPopup(True)
        filter_layout.addWidget(self.from_date)
        
        filter_layout.addWidget(QLabel("To Date:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        filter_layout.addWidget(self.to_date)
        
        filter_layout.addWidget(QLabel("User:"))
        self.user_filter = QComboBox()
        self.load_users()
        filter_layout.addWidget(self.user_filter)
        
        filter_btn = QPushButton("Apply Filter")
        filter_btn.clicked.connect(self.load_logs)
        filter_layout.addWidget(filter_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Summary stats
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db; margin: 15px 0; padding: 10px; background-color: #ebf3fd; border-left: 4px solid #3498db;")
        layout.addWidget(self.summary_label)
        
        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(6)
        self.logs_table.setHorizontalHeaderLabels(["Timestamp", "User", "Action", "IP Address", "User Agent", "Details"])
        layout.addWidget(self.logs_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export Logs")
        export_btn.clicked.connect(self.export_logs)
        clear_old_btn = QPushButton("Clear Old Logs")
        clear_old_btn.clicked.connect(self.clear_old_logs)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_logs)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(clear_old_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_logs()
    
    def load_users(self):
        try:
            with DBManager() as db:
                users = db.fetch_all("SELECT id, username FROM users ORDER BY username")
                self.user_filter.clear()
                self.user_filter.addItem("All Users", None)
                for user_id, username in users:
                    self.user_filter.addItem(username, user_id)
        except Exception as e:
            logging.error(f"Error loading users for filter: {e}")
    
    def load_logs(self):
        try:
            with DBManager() as db:
                # Build query based on filters
                query = """
                    SELECT al.timestamp, u.username, al.action, al.ip_address, al.user_agent, al.id
                    FROM audit_logs al
                    LEFT JOIN users u ON al.user_id = u.id
                    WHERE 1=1
                """
                params = []
                
                # Date filters
                from_date = self.from_date.date().toString("yyyy-MM-dd")
                to_date = self.to_date.date().toString("yyyy-MM-dd")
                query += " AND DATE(al.timestamp) BETWEEN ? AND ?"
                params.extend([from_date, to_date])
                
                # User filter
                selected_user_id = self.user_filter.currentData()
                if selected_user_id:
                    query += " AND al.user_id = ?"
                    params.append(selected_user_id)
                
                query += " ORDER BY al.timestamp DESC LIMIT 1000"
                
                logs = db.fetch_all(query, params)
                
                # Update summary
                total_logs = len(logs)
                unique_users = len(set(log[1] for log in logs if log[1]))
                date_range = f"{from_date} to {to_date}"
                summary_text = f"Showing {total_logs} log entries from {date_range} | {unique_users} unique users"
                self.summary_label.setText(summary_text)
                
                # Populate table
                self.logs_table.setRowCount(len(logs))
                for row, log_entry in enumerate(logs):
                    timestamp, username, action, ip_address, user_agent, log_id = log_entry
                    
                    # Format timestamp
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            formatted_time = str(timestamp)
                    else:
                        formatted_time = ""
                    
                    self.logs_table.setItem(row, 0, QTableWidgetItem(formatted_time))
                    self.logs_table.setItem(row, 1, QTableWidgetItem(username or "System"))
                    self.logs_table.setItem(row, 2, QTableWidgetItem(action or ""))
                    self.logs_table.setItem(row, 3, QTableWidgetItem(ip_address or ""))
                    
                    # Truncate user agent for display
                    user_agent_display = (user_agent[:50] + "...") if user_agent and len(user_agent) > 50 else (user_agent or "")
                    self.logs_table.setItem(row, 4, QTableWidgetItem(user_agent_display))
                    
                    # Add details button or additional info
                    details = f"Log ID: {log_id}"
                    self.logs_table.setItem(row, 5, QTableWidgetItem(details))
                
                # Auto-resize columns
                self.logs_table.resizeColumnsToContents()
                
        except Exception as e:
            logging.error(f"Error loading activity logs: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load activity logs: {str(e)}")
    
    def export_logs(self):
        try:
            import csv
            from datetime import datetime
            import os
            
            # Create reports directory if it doesn't exist
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd")
            filename = f"reports/activity_logs_{from_date}_to_{to_date}_{timestamp}.csv"
            
            # Export data
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Barsiele Sunrise Academy - Activity Logs"])
                writer.writerow(["P.O Box 117 LONDIANI"])
                writer.writerow(["Together we Rise"])
                writer.writerow([])
                writer.writerow([f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([f"Date Range: {from_date} to {to_date}"])
                writer.writerow([])
                
                # Write table headers
                headers = []
                for col in range(self.logs_table.columnCount()):
                    headers.append(self.logs_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.logs_table.rowCount()):
                    row_data = []
                    for col in range(self.logs_table.columnCount()):
                        item = self.logs_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export Complete", f"Activity logs exported to: {filename}")
            
            # Open the reports folder
            import subprocess
            subprocess.Popen(f'explorer /select,"{os.path.abspath(filename)}"')
            
        except Exception as e:
            logging.error(f"Error exporting activity logs: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export logs: {str(e)}")
    
    def clear_old_logs(self):
        reply = QMessageBox.question(self, "Clear Old Logs", 
                                   "This will delete all logs older than 90 days.\n\nAre you sure you want to continue?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with DBManager() as db:
                    # Calculate date 90 days ago
                    cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                    
                    # Count logs to be deleted
                    count_result = db.fetch_one("SELECT COUNT(*) FROM audit_logs WHERE DATE(timestamp) < ?", (cutoff_date,))
                    count = count_result[0] if count_result else 0
                    
                    if count > 0:
                        # Delete old logs
                        db.execute("DELETE FROM audit_logs WHERE DATE(timestamp) < ?", (cutoff_date,))
                        
                        # Log this action
                        db.execute("INSERT INTO audit_logs (user_id, action) VALUES (?, ?)",
                                  (1, f"Cleared {count} old log entries (older than {cutoff_date})"))
                        
                        QMessageBox.information(self, "Logs Cleared", f"Successfully deleted {count} old log entries.")
                        self.load_logs()  # Refresh the display
                    else:
                        QMessageBox.information(self, "No Old Logs", "No logs older than 90 days found.")
                
            except Exception as e:
                logging.error(f"Error clearing old logs: {e}")
                QMessageBox.critical(self, "Error", f"Failed to clear old logs: {str(e)}")


def log_user_action(user_id, action, ip_address=None, user_agent=None):
    """Helper function to log user actions with IP and user agent"""
    try:
        with DBManager() as db:
            db.execute("INSERT INTO audit_logs (user_id, action, ip_address, user_agent) VALUES (?, ?, ?, ?)", 
                      (user_id, action, ip_address, user_agent))
    except Exception as e:
        logging.error(f"Error logging user action: {e}")


def log_login_attempt(username, success, ip_address=None, user_agent=None):
    """Helper function to log login attempts"""
    try:
        with DBManager() as db:
            # Get user ID if login was successful
            user_id = None
            if success:
                user_result = db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
                user_id = user_result[0] if user_result else None
            
            action = f"Login {'successful' if success else 'failed'} for user: {username}"
            db.execute("INSERT INTO audit_logs (user_id, action, ip_address, user_agent) VALUES (?, ?, ?, ?)", 
                      (user_id, action, ip_address, user_agent))
    except Exception as e:
        logging.error(f"Error logging login attempt: {e}")
