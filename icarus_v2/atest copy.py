from PySide6.QtCore import Signal, QThread
from time import sleep
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from ConfigurationManager import ConfigurationManager
from PulseGenerator import PulseGenerator
from ControlPanel import ControlPanel



class mainwindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()

        c = ControlPanel()
        p = PulseGenerator(None, config_manager)
        c.set_pulse_generator(p)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(c)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)



app = QApplication([])

config_manager = ConfigurationManager("settings.json")
window = mainwindow(config_manager)
window.show()

app.exec()
