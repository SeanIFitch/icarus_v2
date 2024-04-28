from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QLabel,
)
from ToggleButton import ToggleButton
from time import sleep


# Control panel for manual and console operation
class LogControlPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)



    # Enable buttons
    def on_restart(self):
        self.pump_button.setEnabled(True)
        self.pressurize_button.setEnabled(True)
        self.depressurize_button.setEnabled(True)
        self.pulse_button.setEnabled(True)
