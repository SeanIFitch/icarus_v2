from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QLabel,
    QDialogButtonBox
)
from ToggleButton import ToggleButton
from TimingSettingsDialog import TimingSettingsDialog
from ErrorDialog import open_error_dialog


# Control panel for pulsed, manual, and console operation
class ControlPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.mode = "Console"  # Default mode is console
        self.pulse_generator = None

        # Initialize modes
        mode_layout = QHBoxLayout()
        self.mode_buttons = {}
        modes = ["Console", "Manual", "Pulsed"]
        for mode in modes:
            mode_button = QRadioButton(mode)
            mode_button.setChecked(mode == self.mode)
            mode_button.toggled.connect(self.mode_changed)
            self.mode_buttons[mode] = mode_button
            mode_layout.addWidget(mode_button)

        # Initialize buttons
        self.shutdown_button = ToggleButton("Shutdown", "Restart")
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
            # Check for states in which mode should not be changed
            error = None

            # Do not switch if pulse generator is running
            if self.pulse_button.isChecked():
                error = "Disable pulsing to change mode."
            # Do not switch if valves are open
            elif self.pressurize_button.isChecked():
                error = "Close pressurize valve to change mode."
            elif self.depressurize_button.isChecked():
                error = "Close depressurize valve to change mode."

            if error is not None:
                open_error_dialog(error, QDialogButtonBox.Ok, self)

                # Revert changes without calling this function again
                # Disconnect the toggled signal temporarily
                for mode, button in self.mode_buttons.items():
                    button.toggled.disconnect(self.mode_changed)
                # set proper button to checked
                for mode, button in self.mode_buttons.items():
                    button.setChecked(mode == self.mode)
                # Reconnect
                for mode, button in self.mode_buttons.items():
                    button.toggled.connect(self.mode_changed)

            # Otherwise change mode and buttons
            else:
                self.mode = sender.text()
                self.update_buttons()


    def update_buttons(self):
        # Remove all buttons from the layout
        for i in reversed(range(self.button_layout.count())):
            widget = self.button_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        if self.mode == "Manual":
            self.button_layout.addWidget(self.shutdown_button)
            self.button_layout.addWidget(self.pump_button)
            self.button_layout.addWidget(self.pressurize_button)
            self.button_layout.addWidget(self.depressurize_button)
        elif self.mode == "Pulsed":
            self.button_layout.addWidget(self.shutdown_button)
            self.button_layout.addWidget(self.pump_button)
            self.button_layout.addWidget(self.pulse_button)
            self.button_layout.addWidget(self.timing_settings_button)
        elif self.mode == "Console":
            self.button_layout.addWidget(self.shutdown_button)
            self.button_layout.addWidget(self.pump_button)


    # Connect buttons to the pulse generator
    def set_pulse_generator(self, pulse_generator):
        self.pulse_generator = pulse_generator

        self.shutdown_button.set_check_function(self.on_shutdown)
        self.shutdown_button.set_uncheck_function(self.on_restart)
        self.pump_button.set_check_function(self.pulse_generator.set_pump_low)
        self.pump_button.set_uncheck_function(self.pulse_generator.set_pump_high)
        self.pressurize_button.set_check_function(self.pulse_generator.set_pressurize_low)
        self.pressurize_button.set_uncheck_function(self.pulse_generator.set_pressurize_high)
        self.depressurize_button.set_check_function(self.pulse_generator.set_depressurize_low)
        self.depressurize_button.set_uncheck_function(self.pulse_generator.set_depressurize_high)
        self.pulse_button.set_check_function(self.pulse_generator.start)
        self.pulse_button.set_uncheck_function(self.on_quit_pulsing)
        self.timing_settings_button.clicked.connect(self.open_timing_dialog)


    def on_shutdown(self):
        # Prevent other buttons from doing anything while shutdown
        self.pump_button.setEnabled(False)
        self.pressurize_button.setEnabled(False)
        self.depressurize_button.setEnabled(False)
        self.pulse_button.setEnabled(False)

        # Turn pump off
        self.pump_button.setChecked(False)
        # Shutdown device
        # Stop pulsing
        self.pulse_generator.quit()
        self.pulse_generator.wait()
        # Open valves
        self.pressurize_button.setChecked(True)
        self.depressurize_button.setChecked(True)


    # Enable buttons
    def on_restart(self):
        self.pump_button.setEnabled(True)
        self.pressurize_button.setEnabled(True)
        self.depressurize_button.setEnabled(True)
        self.pulse_button.setEnabled(True)

        # Revert to manual mode so that valves may be closed
        self.mode = "Manual"
        # disconnect so that mode may be changed while valves are closed
        for mode, button in self.mode_buttons.items():
            button.toggled.disconnect(self.mode_changed)
        # set proper button to checked
        for mode, button in self.mode_buttons.items():
            button.setChecked(mode == self.mode)
        # Reconnect
        for mode, button in self.mode_buttons.items():
            button.toggled.connect(self.mode_changed)
        self.update_buttons()


    # Make sure no buttons are clicked until pulsing is fully done
    def on_quit_pulsing(self):
        self.pulse_generator.quit()
        self.pulse_generator.wait()


    def open_timing_dialog(self):
        dialog = TimingSettingsDialog(self.pulse_generator, parent=self)
        return dialog.exec()
