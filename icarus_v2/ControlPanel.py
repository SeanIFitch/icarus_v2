from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QLabel
)
from ToggleButton import ToggleButton
from TimingDialog import TimingDialog


# Control panel for pulsed, manual, and console operation
class ControlPanel(QGroupBox):
    def __init__(self):
        super().__init__()

        self.mode = "console"  # Default mode is console

        # Initialize modes
        mode_layout = QHBoxLayout()
        self.mode_buttons = {}
        modes = ["Manual", "Pulsed", "Console"]
        for mode in modes:
            mode_button = QRadioButton(mode)
            mode_button.setChecked(mode.lower() == self.mode)
            mode_button.toggled.connect(self.mode_changed)
            self.mode_buttons[mode] = mode_button
            mode_layout.addWidget(mode_button)

        # Initialize buttons
        self.shutdown_button = QPushButton(text="Shutdown")
        self.pump_button = ToggleButton("Pump on", "Pump off")
        self.pressurize_button = ToggleButton("Pressurize open", "Pressurize close")
        self.depressurize_button = ToggleButton("Depressurize open", "Depressurize close")
        self.pulse_button = ToggleButton("Start pulsing", "Stop pulsing")
        self.timing_settings_button = QPushButton("Settings")

        # Set button layout
        self.button_layout = QVBoxLayout()
        self.update_buttons()  # Update buttons according to current mode

        # Set main layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Change Mode:"))
        layout.addLayout(mode_layout)
        layout.addLayout(self.button_layout)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)


    def mode_changed(self):
        sender = self.sender()
        if sender.isChecked():
            self.mode = sender.text().lower()
            self.update_buttons()


    def update_buttons(self):
        # Remove all buttons from the layout
        for i in reversed(range(self.button_layout.count())):
            widget = self.button_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        if self.mode == "manual":
            self.button_layout.addWidget(self.shutdown_button)
            self.button_layout.addWidget(self.pump_button)
            self.button_layout.addWidget(self.pressurize_button)
            self.button_layout.addWidget(self.depressurize_button)
        elif self.mode == "pulsed":
            self.button_layout.addWidget(self.shutdown_button)
            self.button_layout.addWidget(self.pump_button)
            self.button_layout.addWidget(self.pulse_button)
            self.button_layout.addWidget(self.timing_settings_button)
        elif self.mode == "console":
            self.button_layout.addWidget(self.shutdown_button)
            self.button_layout.addWidget(self.pump_button)


    # Connect buttons to the pulse generator
    def set_pulse_generator(self, pulse_generator):
        self.pulse_generator = pulse_generator
        # Device controls
        def dummy():
                #Shut down pump (High)
                #    solenoid stops for air pressure on high
                #Open valves (Low)
            pass
        self.shutdown_button.clicked.connect(dummy)
        self.pump_button.set_check_function(self.pulse_generator.set_pump_low)
        self.pump_button.set_uncheck_function(self.pulse_generator.set_pump_high)
        self.pressurize_button.set_check_function(self.pulse_generator.set_pressurize_low)
        self.pressurize_button.set_uncheck_function(self.pulse_generator.set_pressurize_high)
        self.depressurize_button.set_check_function(self.pulse_generator.set_depressurize_low)
        self.depressurize_button.set_uncheck_function(self.pulse_generator.set_depressurize_high)
        self.pulse_button.set_check_function(self.pulse_generator.start)
        self.pulse_button.set_uncheck_function(self.pulse_generator.quit)
        self.timing_settings_button.clicked.connect(self.open_timing_dialog)


    def open_timing_dialog(self):
        dialog = TimingDialog(self.pulse_generator, parent=self)
        return dialog.exec()
