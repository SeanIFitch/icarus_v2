from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QLabel,
)
from ToggleButton import ToggleButton
from TimingSettingsDialog import TimingSettingsDialog
from time import sleep


# Control panel for manual and console operation
class ControlPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pulse_generator = None

        # Initialize modes
        self.console_button = QRadioButton("Console")
        self.console_button.setChecked(False)
        self.console_button.toggled.connect(self.change_to_console)
        self.manual_button = QRadioButton("Manual")
        self.manual_button.setChecked(True)
        self.manual_button.toggled.connect(self.change_to_manual)

        # Initialize buttons
        self.shutdown_button = ToggleButton("Shutdown", "Restart")
        self.pump_button = ToggleButton("Pump on", "Pump off")
        self.pressurize_button = ToggleButton("Pressurize close", "Pressurize open")
        self.depressurize_button = ToggleButton("Depressurize close", "Depressurize open")
        self.pulse_button = ToggleButton("Start pulsing", "Stop pulsing")
        self.timing_settings_button = QPushButton("Pulse Settings")

        # Set button layout
        self.button_layout = QVBoxLayout()

        # Set layout
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.console_button)
        mode_layout.addWidget(self.manual_button)
        layout = QVBoxLayout()
        layout.addWidget(self.shutdown_button)
        layout.addWidget(QLabel("Change Mode:"))
        layout.addLayout(mode_layout)
        layout.addLayout(self.button_layout)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

        self.button_layout.addWidget(self.pump_button)
        self.button_layout.addWidget(self.pressurize_button)
        self.button_layout.addWidget(self.depressurize_button)
        self.button_layout.addWidget(self.pulse_button)
        self.button_layout.addWidget(self.timing_settings_button)


    def change_to_console(self):
        sender = self.sender()
        # Only follow through if enabling mode not disabling
        if sender.isChecked():
            # Remove all buttons from the layout
            for i in reversed(range(self.button_layout.count())):
                widget = self.button_layout.itemAt(i).widget()
                if widget is not None:
                    widget.setParent(None)

            # Set pump on, valves closed
            self.pump_button.setChecked(True)
            self.pressurize_button.setChecked(True)
            self.depressurize_button.setChecked(True)


    def change_to_manual(self):
        sender = self.sender()
        # Only follow through if enabling mode not disabling
        if sender.isChecked():
            self.button_layout.addWidget(self.pump_button)
            self.button_layout.addWidget(self.pressurize_button)
            self.button_layout.addWidget(self.depressurize_button)
            self.button_layout.addWidget(self.pulse_button)
            self.button_layout.addWidget(self.timing_settings_button)


    # Connect buttons to the pulse generator
    def set_pulse_generator(self, pulse_generator):
        self.pulse_generator = pulse_generator

        self.shutdown_button.set_check_function(self.on_shutdown)
        self.shutdown_button.set_uncheck_function(self.on_restart)
        self.pump_button.set_check_function(self.pulse_generator.set_pump_high)
        self.pump_button.set_uncheck_function(self.pulse_generator.set_pump_low)
        self.pressurize_button.set_check_function(self.pulse_generator.set_pressurize_high)
        self.pressurize_button.set_uncheck_function(self.pulse_generator.set_pressurize_low)
        self.depressurize_button.set_check_function(self.pulse_generator.set_depressurize_high)
        self.depressurize_button.set_uncheck_function(self.pulse_generator.set_depressurize_low)
        self.pulse_button.set_check_function(self.on_start_pulsing)
        self.pulse_button.set_uncheck_function(self.on_quit_pulsing)
        self.timing_settings_button.clicked.connect(self.open_timing_dialog)


    def on_shutdown(self):
        # Turn pump off
        self.pump_button.setEnabled(False)
        self.pump_button.setChecked(False)
        # Stop pulsing
        self.pulse_button.setEnabled(False)
        self.pulse_button.setChecked(False)
        # Open valves
        self.pressurize_button.setEnabled(False)
        self.depressurize_button.setEnabled(False)
        self.pressurize_button.setChecked(False)
        self.depressurize_button.setChecked(False)

        # Revert to manual mode
        self.console_button.setChecked(False)
        self.manual_button.setChecked(True)


    # Enable buttons
    def on_restart(self):
        self.pump_button.setEnabled(True)
        self.pressurize_button.setEnabled(True)
        self.depressurize_button.setEnabled(True)
        self.pulse_button.setEnabled(True)


    def on_start_pulsing(self):
        # Prevent other buttons from doing anything while pulsing
        self.pressurize_button.setEnabled(False)
        self.depressurize_button.setEnabled(False)

        # Close valves
        self.pressurize_button.setChecked(True)
        self.depressurize_button.setChecked(True)
        # Prevents 2 depressurize events in the same chunk
        # One chunk is update_rate^-1 = 30^-1 = 0.0333 seconds
        sleep(0.05)

        self.pulse_generator.start()


    # Make sure no buttons are clicked until pulsing is fully done
    def on_quit_pulsing(self):
        self.pulse_generator.quit()
        self.pulse_generator.wait()
        self.pressurize_button.setEnabled(True)
        self.depressurize_button.setEnabled(True)


    def open_timing_dialog(self):
        dialog = TimingSettingsDialog(self.pulse_generator, parent=self)
        return dialog.exec()
