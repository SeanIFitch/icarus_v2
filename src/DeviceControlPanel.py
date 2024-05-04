from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QRadioButton,
    QVBoxLayout,
    QLabel,
    QWidget,
    QSizePolicy,
    QSpacerItem,
    QGridLayout
)
from ToggleButton import ToggleButton
from TogglePictureButton import TogglePictureButton
from time import sleep


# Control panel for manual and console operation
class DeviceControlPanel(QGroupBox):
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
        self.shutdown_button = TogglePictureButton("icons/shutdown.svg", "Shutdown", "Restart")
        self.pump_button = ToggleButton("Pump on", "Pump off")
        self.pressurize_button = ToggleButton("Pressurize open", "Pressurize close")
        self.depressurize_button = ToggleButton("Depressurize open", "Depressurize close")
        self.pulse_button = ToggleButton("Start pulsing", "Stop pulsing")
        self.shutdown_button.setFixedSize(150,150)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.pump_button.setSizePolicy(policy)
        self.pressurize_button.setSizePolicy(policy)
        self.depressurize_button.setSizePolicy(policy)
        self.pulse_button.setSizePolicy(policy)

        # Spacer for when buttons are hidden
        #self.spacer = QSpacerItem(0, 0, QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Set layouts
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.pump_button)
        button_layout.addWidget(self.pressurize_button)
        button_layout.addWidget(self.depressurize_button)
        button_layout.addWidget(self.pulse_button)
        self.button_widget = QWidget()
        self.button_widget.setLayout(button_layout)

        layout = QGridLayout(self)
        layout.addWidget(self.shutdown_button, 0, 0, 1, 2, alignment=Qt.AlignHCenter)
        layout.addWidget(QLabel("Change Mode:"), 1, 0, 1, 2)
        layout.addWidget(self.console_button, 2, 0)
        layout.addWidget(self.manual_button, 2, 1)
        layout.addWidget(self.button_widget, 3, 0, 1, 2)
        #layout.addItem(self.spacer, 3, 0)

        self.setMinimumWidth(287) # Width of depressurize button.Without this the panel shrinks when buttons are hidden
        self.setStyleSheet("font-size: 21pt;")


    def change_to_console(self):
        sender = self.sender()
        # Only follow through if enabling mode not disabling
        if sender.isChecked():
            # Remove all buttons from the layout
            self.button_widget.hide()

            # Set pulser off, pump on, valves closed
            self.pulse_button.setChecked(False)
            self.pump_button.setChecked(True)
            self.pressurize_button.setChecked(True)
            self.depressurize_button.setChecked(True)


    def change_to_manual(self):
        sender = self.sender()
        # Only follow through if enabling mode not disabling
        if sender.isChecked():
            self.button_widget.show()


    # Connect buttons to the pulse generator
    def set_pulse_generator(self, pulse_generator):
        self.pulse_generator = pulse_generator

        self.shutdown_button.set_check_function(self.on_shutdown)
        self.shutdown_button.set_uncheck_function(self.on_restart)
        self.pump_button.set_uncheck_function(self.pulse_generator.set_pump_high)
        self.pump_button.set_check_function(self.pulse_generator.set_pump_low)
        self.pressurize_button.set_check_function(self.pulse_generator.set_pressurize_low)
        self.pressurize_button.set_uncheck_function(self.pulse_generator.set_pressurize_high)
        self.depressurize_button.set_check_function(self.pulse_generator.set_depressurize_low)
        self.depressurize_button.set_uncheck_function(self.pulse_generator.set_depressurize_high)
        self.pulse_button.set_check_function(self.on_start_pulsing)
        self.pulse_button.set_uncheck_function(self.on_quit_pulsing)


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
        self.pressurize_button.setChecked(True)
        self.depressurize_button.setChecked(True)

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
        self.pressurize_button.setChecked(False)
        self.depressurize_button.setChecked(False)
        # Prevents 2 depressurize events in the same chunk
        # One chunk is update_rate^-1 = 30^-1 = 0.0333 seconds
        sleep(0.05)

        self.pulse_generator.start()


    def reset(self):
        # Enable buttons
        self.on_restart()

        # Reset buttons to initial states without triggering their slots
        self.shutdown_button.set_checked(False)
        self.pump_button.set_checked(False)
        self.pressurize_button.set_checked(False)
        self.depressurize_button.set_checked(False)
        self.pulse_button.set_checked(False)

        # Change to manual mode
        self.button_widget.show()
        self.console_button.blockSignals(True)
        self.console_button.setChecked(False)
        self.console_button.blockSignals(False)
        self.manual_button.blockSignals(True)
        self.manual_button.setChecked(True)
        self.manual_button.blockSignals(False)


    # Make sure no buttons are clicked until pulsing is fully done
    def on_quit_pulsing(self):
        self.pulse_generator.quit()
        self.pulse_generator.wait()
        self.pressurize_button.setEnabled(True)
        self.depressurize_button.setEnabled(True)
