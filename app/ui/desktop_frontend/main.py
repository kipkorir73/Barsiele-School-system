# PyQt5 placeholder UI module (very minimal)
from PyQt5 import QtWidgets
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('School Fee Management - Desktop')
        self.resize(1000, 600)
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('Welcome to School Fee Management - Desktop (UI placeholder)')
        layout.addWidget(label)
        central.setLayout(layout)
        self.setCentralWidget(central)
