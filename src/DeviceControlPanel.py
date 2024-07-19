from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)
from ToggleButton import ToggleButton
from ImageButton import ImageButton
from time import sleep
import os
from path_utils import get_base_directory
import qdarktheme


# Control panel for manual and console operation
class DeviceControlPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pulse_generator = None

        # Initialize buttons
        base_dir = get_base_directory()
        shutdown_path = os.path.join(base_dir, "images/shutdown.svg")
        self.shutdown_button = ImageButton(shutdown_path, "Shutdown")

        bg = qdarktheme.load_palette().window().color().name()
        self.mode_button = ToggleButton("Manual", "Console", bg, bg)
        self.mode_button.set_check_function(self.change_to_console)
        self.mode_button.set_uncheck_function(self.change_to_manual)

        self.pump_button = ToggleButton("Pump", check_color="#56bd5d", uncheck_color="#f45555")
        self.pressurize_button = ToggleButton("Pressurize", check_color="#56bd5d", uncheck_color="#f45555")
        self.depressurize_button = ToggleButton("Depressurize", check_color="#56bd5d", uncheck_color="#f45555")
        self.pulse_button = ToggleButton("Pulsing", check_color="#56bd5d", uncheck_color="#f45555")

        self.shutdown_button.setFixedSize(150, 150)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.mode_button.setSizePolicy(policy)
        self.pump_button.setSizePolicy(policy)
        self.pressurize_button.setSizePolicy(policy)
        self.depressurize_button.setSizePolicy(policy)
        self.pulse_button.setSizePolicy(policy)
        self.spacer_item = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.shutdown_button, alignment=Qt.AlignHCenter | Qt.AlignTop)
        self.layout.addWidget(self.mode_button)
        self.layout.addWidget(self.pump_button)
        self.layout.addWidget(self.pressurize_button)
        self.layout.addWidget(self.depressurize_button)
        self.layout.addWidget(self.pulse_button)

        self.setMinimumWidth(288)  # Width of depressurize button.Without this the panel shrinks when buttons are hidden
        self.setStyleSheet("font-size: 21pt;")

    def change_to_console(self):
        # Ensure the mode button doesn't expand or move
        size = self.mode_button.size().height()
        self.mode_button.setMinimumHeight(size)
        self.mode_button.setMaximumHeight(size)

        for button in [self.pump_button, self.pressurize_button, self.depressurize_button, self.pulse_button]:
            button.setVisible(False)
            button.setEnabled(False)

        self.layout.addItem(self.spacer_item)

        # Set pulser off, pump on, valves closed
        self.pulse_button.setChecked(False)
        self.pump_button.setChecked(True)
        self.pressurize_button.setChecked(False)
        self.depressurize_button.setChecked(False)

    def change_to_manual(self):
        for button in [self.pump_button, self.pressurize_button, self.depressurize_button, self.pulse_button]:
            button.setVisible(True)
            button.setEnabled(True)

        self.layout.removeItem(self.spacer_item)

        # Remove size constraint on mode button
        self.mode_button.setMaximumHeight(16777215)
        self.mode_button.setMinimumHeight(0)

    # Connect buttons to the pulse generator
    def set_pulse_generator(self, pulse_generator):
        self.pulse_generator = pulse_generator

        self.shutdown_button.clicked.connect(self.on_shutdown)
        self.pump_button.set_check_function(self.pulse_generator.set_pump_low)
        self.pump_button.set_uncheck_function(self.pulse_generator.set_pump_high)
        self.pressurize_button.set_check_function(self.pulse_generator.set_pressurize_low)
        self.pressurize_button.set_uncheck_function(self.pulse_generator.set_pressurize_high)
        self.depressurize_button.set_check_function(self.pulse_generator.set_depressurize_low)
        self.depressurize_button.set_uncheck_function(self.pulse_generator.set_depressurize_high)
        self.pulse_button.set_check_function(self.on_start_pulsing)
        self.pulse_button.set_uncheck_function(self.on_quit_pulsing)

    def on_shutdown(self):
        # Turn pump off
        self.pump_button.setChecked(False)
        # Stop pulsing
        self.pulse_button.setChecked(False)
        # Open valves
        self.pressurize_button.setChecked(True)
        self.depressurize_button.setChecked(True)

        # Revert to manual mode
        self.mode_button.setChecked(False)

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
        # Reset buttons to initial states without triggering their slots
        self.pump_button.set_checked(False)
        self.pressurize_button.set_checked(False)
        self.depressurize_button.set_checked(False)
        self.pulse_button.set_checked(False)

        # Change to manual mode
        self.mode_button.setChecked(False)

    # Make sure no buttons are clicked until pulsing is fully done
    def on_quit_pulsing(self):
        self.pulse_generator.quit()
        self.pulse_generator.wait()
        self.pressurize_button.setEnabled(True)
        self.depressurize_button.setEnabled(True)
