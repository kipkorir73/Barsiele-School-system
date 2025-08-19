from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QLabel
from PyQt6.QtCore import Qt
from ...core.config import DEFAULT_RATES
from ...core.db_manager import DBManager
import logging

logging.basicConfig(filename='app/logs/settings.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget { background-color: #ecf0f1; }
            QFormLayout { margin: 10px; }
            QLabel { color: #2c3e50; }
            QLineEdit { border: 2px solid #3498db; border-radius: 5px; padding: 5px; background-color: white; }
            QPushButton { background-color: #f1c40f; color: white; border-radius: 5px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #f39c12; }
        """)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.maize_rate = QLineEdit(str(DEFAULT_RATES['maize']))
        self.millet_rate = QLineEdit(str(DEFAULT_RATES['millet']))
        self.beans_rate = QLineEdit(str(DEFAULT_RATES['beans']))
        
        form_layout.addRow("Maize Rate (KSh/kg):", self.maize_rate)
        form_layout.addRow("Millet Rate (KSh/kg):", self.millet_rate)
        form_layout.addRow("Beans Rate (KSh/kg):", self.beans_rate)
        
        save_btn = QPushButton("Save Rates")
        save_btn.clicked.connect(self.save_rates)
        form_layout.addRow(save_btn)
        
        layout.addLayout(form_layout)
        self.setLayout(layout)

    def save_rates(self):
        try:
            new_rates = {
                'maize': float(self.maize_rate.text()),
                'millet': float(self.millet_rate.text()),
                'beans': float(self.beans_rate.text())
            }
            with open('.env', 'a') as f:
                f.write(f"\nRATE_MAIZE={new_rates['maize']}\n")
                f.write(f"RATE_MILLET={new_rates['millet']}\n")
                f.write(f"RATE_BEANS={new_rates['beans']}\n")
            QMessageBox.information(self, "Success", "Rates updated successfully!")
            logging.info(f"Updated contribution rates: {new_rates}")
        except ValueError as e:
            QMessageBox.critical(self, "Error", "Please enter valid numbers for rates")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save rates: {str(e)}")