from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QDialog, QMessageBox
from PyQt6.QtCore import Qt
from ...core.db_manager import DBManager
from ...core.payment_manager import get_balance
import logging

logging.basicConfig(filename='app/logs/arrears.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ArrearsDetailDialog(QDialog):
    def __init__(self, class_name=None, parent=None):
        super().__init__(parent)
        self.class_name = class_name
        self.setWindowTitle(f"Arrears Details - {class_name if class_name else 'All Classes'}")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QLabel { color: #2c3e50; font-size: 14px; font-weight: bold; }
            QTableWidget { 
                border: 2px solid #27ae60; 
                background-color: white; 
                gridline-color: #bdc3c7;
                selection-background-color: #27ae60;
            }
            QPushButton { 
                background-color: #27ae60; 
                color: white; 
                border-radius: 8px; 
                padding: 12px 20px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"Arrears Details - {class_name if class_name else 'All Classes'}")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #27ae60; margin-bottom: 10px;")
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
        
        # Summary stats
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; margin-bottom: 15px; padding: 10px; background-color: #fdf2f2; border-left: 4px solid #e74c3c;")
        layout.addWidget(self.summary_label)
        
        # Students table
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(6)
        self.students_table.setHorizontalHeaderLabels(["Admission No", "Name", "Class", "Total Fees", "Paid", "Arrears"])
        layout.addWidget(self.students_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_data)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_data()
    
    def load_data(self):
        try:
            with DBManager() as db:
                if self.class_name:
                    # Get students from specific class
                    students = db.fetch_all("""
                        SELECT s.admission_number, s.name, c.name as class_name, s.id,
                               COALESCE(f.total_fees, 0) as total_fees,
                               COALESCE(f.bus_fee, 0) as bus_fee
                        FROM students s
                        JOIN classes c ON s.class_id = c.id
                        LEFT JOIN fees f ON s.id = f.student_id
                        WHERE c.name = ?
                        ORDER BY s.name
                    """, (self.class_name,))
                else:
                    # Get all students with arrears > 0
                    students = db.fetch_all("""
                        SELECT s.admission_number, s.name, c.name as class_name, s.id,
                               COALESCE(f.total_fees, 0) as total_fees,
                               COALESCE(f.bus_fee, 0) as bus_fee
                        FROM students s
                        JOIN classes c ON s.class_id = c.id
                        LEFT JOIN fees f ON s.id = f.student_id
                        ORDER BY c.name, s.name
                    """)
                
                # Calculate arrears for each student
                students_with_arrears = []
                total_arrears = 0
                total_fees_expected = 0
                total_paid = 0
                
                for student in students:
                    admission_no, name, class_name, student_id, fees, bus_fee = student
                    
                    # Get payments for this student
                    paid_result = db.fetch_one("SELECT SUM(amount) FROM payments WHERE student_id = ?", (student_id,))
                    paid = paid_result[0] if paid_result and paid_result[0] else 0
                    
                    total_expected = fees + bus_fee
                    arrears = total_expected - paid
                    
                    # Only include students with arrears > 0 if showing all classes
                    if self.class_name or arrears > 0:
                        students_with_arrears.append((admission_no, name, class_name, total_expected, paid, arrears))
                        total_arrears += arrears
                        total_fees_expected += total_expected
                        total_paid += paid
                
                # Update summary
                if self.class_name:
                    summary_text = f"Class {self.class_name}: {len(students_with_arrears)} students | Total Expected: KSh {total_fees_expected:,.2f} | Total Paid: KSh {total_paid:,.2f} | Total Arrears: KSh {total_arrears:,.2f}"
                else:
                    summary_text = f"Students with Arrears: {len(students_with_arrears)} | Total Expected: KSh {total_fees_expected:,.2f} | Total Paid: KSh {total_paid:,.2f} | Total Arrears: KSh {total_arrears:,.2f}"
                
                self.summary_label.setText(summary_text)
                
                # Populate table
                self.students_table.setRowCount(len(students_with_arrears))
                for row, (admission_no, name, class_name, total_expected, paid, arrears) in enumerate(students_with_arrears):
                    self.students_table.setItem(row, 0, QTableWidgetItem(str(admission_no or "")))
                    self.students_table.setItem(row, 1, QTableWidgetItem(name or ""))
                    self.students_table.setItem(row, 2, QTableWidgetItem(class_name or ""))
                    self.students_table.setItem(row, 3, QTableWidgetItem(f"KSh {total_expected:,.2f}"))
                    self.students_table.setItem(row, 4, QTableWidgetItem(f"KSh {paid:,.2f}"))
                    
                    # Color code arrears
                    arrears_item = QTableWidgetItem(f"KSh {arrears:,.2f}")
                    if arrears > 1000:
                        arrears_item.setBackground(Qt.GlobalColor.red)
                        arrears_item.setForeground(Qt.GlobalColor.white)
                    elif arrears > 500:
                        arrears_item.setBackground(Qt.GlobalColor.yellow)
                    self.students_table.setItem(row, 5, arrears_item)
                
                # Auto-resize columns
                self.students_table.resizeColumnsToContents()
                
        except Exception as e:
            logging.error(f"Error loading arrears data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load arrears data: {str(e)}")
    
    def export_data(self):
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
            if self.class_name:
                filename = f"reports/{self.class_name.replace(' ', '_')}_arrears_{timestamp}.csv"
            else:
                filename = f"reports/all_arrears_{timestamp}.csv"
            
            # Export data
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Barsiele Sunrise Academy - Arrears Report"])
                writer.writerow(["P.O Box 117 LONDIANI"])
                writer.writerow(["Together we Rise"])
                writer.writerow([])
                writer.writerow([f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([f"Report for: {self.class_name if self.class_name else 'All Classes with Arrears'}"])
                writer.writerow([])
                
                # Write table headers
                headers = []
                for col in range(self.students_table.columnCount()):
                    headers.append(self.students_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.students_table.rowCount()):
                    row_data = []
                    for col in range(self.students_table.columnCount()):
                        item = self.students_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export Complete", f"Arrears report exported to: {filename}")
            
            # Open the reports folder
            import subprocess
            subprocess.Popen(f'explorer /select,"{os.path.abspath(filename)}"')
            
        except Exception as e:
            logging.error(f"Error exporting arrears data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")


class HighArrearsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("High Arrears Students")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QLabel { color: #2c3e50; font-size: 14px; font-weight: bold; }
            QTableWidget { 
                border: 2px solid #e74c3c; 
                background-color: white; 
                gridline-color: #bdc3c7;
                selection-background-color: #e74c3c;
            }
            QPushButton { 
                background-color: #e74c3c; 
                color: white; 
                border-radius: 8px; 
                padding: 12px 20px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a93226; }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("High Arrears Students (> KSh 1,000)")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c; margin-bottom: 10px;")
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
        
        # Summary stats
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; margin-bottom: 15px; padding: 10px; background-color: #fdf2f2; border-left: 4px solid #e74c3c;")
        layout.addWidget(self.summary_label)
        
        # Students table
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(7)
        self.students_table.setHorizontalHeaderLabels(["Admission No", "Name", "Class", "Guardian Contact", "Total Fees", "Paid", "Arrears"])
        layout.addWidget(self.students_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export High Arrears")
        export_btn.clicked.connect(self.export_data)
        send_sms_btn = QPushButton("Send SMS Reminders")
        send_sms_btn.clicked.connect(self.send_sms_reminders)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(send_sms_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_data()
    
    def load_data(self):
        try:
            with DBManager() as db:
                # Get all students with high arrears (> 1000)
                students = db.fetch_all("""
                    SELECT s.admission_number, s.name, c.name as class_name, s.guardian_contact, s.id,
                           COALESCE(f.total_fees, 0) as total_fees,
                           COALESCE(f.bus_fee, 0) as bus_fee
                    FROM students s
                    JOIN classes c ON s.class_id = c.id
                    LEFT JOIN fees f ON s.id = f.student_id
                    ORDER BY c.name, s.name
                """)
                
                high_arrears_students = []
                total_high_arrears = 0
                
                for student in students:
                    admission_no, name, class_name, guardian_contact, student_id, fees, bus_fee = student
                    
                    # Get payments for this student
                    paid_result = db.fetch_one("SELECT SUM(amount) FROM payments WHERE student_id = ?", (student_id,))
                    paid = paid_result[0] if paid_result and paid_result[0] else 0
                    
                    total_expected = fees + bus_fee
                    arrears = total_expected - paid
                    
                    # Only include students with arrears > 1000
                    if arrears > 1000:
                        high_arrears_students.append((admission_no, name, class_name, guardian_contact, total_expected, paid, arrears))
                        total_high_arrears += arrears
                
                # Update summary
                summary_text = f"Students with High Arrears: {len(high_arrears_students)} | Total High Arrears: KSh {total_high_arrears:,.2f}"
                self.summary_label.setText(summary_text)
                
                # Populate table
                self.students_table.setRowCount(len(high_arrears_students))
                for row, (admission_no, name, class_name, guardian_contact, total_expected, paid, arrears) in enumerate(high_arrears_students):
                    self.students_table.setItem(row, 0, QTableWidgetItem(str(admission_no or "")))
                    self.students_table.setItem(row, 1, QTableWidgetItem(name or ""))
                    self.students_table.setItem(row, 2, QTableWidgetItem(class_name or ""))
                    self.students_table.setItem(row, 3, QTableWidgetItem(guardian_contact or ""))
                    self.students_table.setItem(row, 4, QTableWidgetItem(f"KSh {total_expected:,.2f}"))
                    self.students_table.setItem(row, 5, QTableWidgetItem(f"KSh {paid:,.2f}"))
                    
                    # Color code arrears based on severity
                    arrears_item = QTableWidgetItem(f"KSh {arrears:,.2f}")
                    if arrears > 5000:
                        arrears_item.setBackground(Qt.GlobalColor.darkRed)
                        arrears_item.setForeground(Qt.GlobalColor.white)
                    elif arrears > 2000:
                        arrears_item.setBackground(Qt.GlobalColor.red)
                        arrears_item.setForeground(Qt.GlobalColor.white)
                    else:
                        arrears_item.setBackground(Qt.GlobalColor.yellow)
                    self.students_table.setItem(row, 6, arrears_item)
                
                # Auto-resize columns
                self.students_table.resizeColumnsToContents()
                
        except Exception as e:
            logging.error(f"Error loading high arrears data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load high arrears data: {str(e)}")
    
    def export_data(self):
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
            filename = f"reports/high_arrears_students_{timestamp}.csv"
            
            # Export data
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Barsiele Sunrise Academy - High Arrears Report"])
                writer.writerow(["P.O Box 117 LONDIANI"])
                writer.writerow(["Together we Rise"])
                writer.writerow([])
                writer.writerow([f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow(["Students with arrears > KSh 1,000"])
                writer.writerow([])
                
                # Write table headers
                headers = []
                for col in range(self.students_table.columnCount()):
                    headers.append(self.students_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.students_table.rowCount()):
                    row_data = []
                    for col in range(self.students_table.columnCount()):
                        item = self.students_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export Complete", f"High arrears report exported to: {filename}")
            
            # Open the reports folder
            import subprocess
            subprocess.Popen(f'explorer /select,"{os.path.abspath(filename)}"')
            
        except Exception as e:
            logging.error(f"Error exporting high arrears data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
    
    def send_sms_reminders(self):
        # Placeholder for SMS functionality
        QMessageBox.information(self, "SMS Reminders", 
                               "SMS reminder functionality will be implemented with SMS gateway integration.\n\n"
                               "For now, you can export the data and contact guardians manually.")
