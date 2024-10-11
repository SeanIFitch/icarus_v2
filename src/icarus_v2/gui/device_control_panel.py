import importlib
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QGroupBox,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QPushButton,
)
from icarus_v2.gui.image_button import ImageButton
from time import sleep


# Control panel for manual and console operation
class DeviceControlPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pulse_generator = None

        # Initialize buttons
        with importlib.resources.path('icarus_v2.resources', 'shutdown.svg') as shutdown_path:
            self.shutdown_button = ImageButton(str(shutdown_path), "Shutdown")
        self.shutdown_button.clicked.connect(self.on_shutdown)

        self.mode_button = QPushButton("Manual")
        self.mode_button.setObjectName("noEnabled")
        self.mode_button.setCheckable(True)
        self.mode_button.toggled.connect(self.toggle_mode)

        self.pump_button = QPushButton("Pump")
        self.pump_button.setObjectName("toggleButton")
        self.pump_button.setCheckable(True)
        self.pump_button.toggled.connect(self.toggle_pump)

        self.pressurize_button = QPushButton("Pressurize")
        self.pressurize_button.setObjectName("toggleButton")
        self.pressurize_button.setCheckable(True)
        self.pressurize_button.toggled.connect(self.toggle_pressurize)

        self.depressurize_button = QPushButton("Depressurize")
        self.depressurize_button.setObjectName("toggleButton")
        self.depressurize_button.setCheckable(True)
        self.depressurize_button.toggled.connect(self.toggle_depressurize)

        self.pulse_button = QPushButton("Pulsing")
        self.pulse_button.setObjectName("toggleButton")
        self.pulse_button.setCheckable(True)
        self.pulse_button.toggled.connect(self.toggle_pulsing)

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

    def toggle_mode(self, checked):
        if checked:
            self.mode_button.setText("Console")
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
        else:
            self.mode_button.setText("Manual")
            for button in [self.pump_button, self.pressurize_button, self.depressurize_button, self.pulse_button]:
                button.setVisible(True)
                button.setEnabled(True)

            self.layout.removeItem(self.spacer_item)

            # Remove size constraint on mode button
            self.mode_button.setMaximumHeight(16777215)
            self.mode_button.setMinimumHeight(0)

    def toggle_pump(self, checked):
        if checked:
            self.pulse_generator.set_pump_low()
        else:
            self.pulse_generator.set_pump_high()

    def toggle_depressurize(self, checked):
        if checked:
            self.pulse_generator.set_depressurize_low()
        else:
            self.pulse_generator.set_depressurize_high()

    def toggle_pressurize(self, checked):
        if checked:
            self.pulse_generator.set_pressurize_low()
        else:
            self.pulse_generator.set_pressurize_high()

    def toggle_pulsing(self, checked):
        if checked:
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
        else:
            # make sure no buttons are clicked until pulsing is fully done
            self.pulse_generator.quit()
            self.pulse_generator.wait()
            self.pressurize_button.setEnabled(True)
            self.depressurize_button.setEnabled(True)

    # Connect buttons to the pulse generator
    def set_pulse_generator(self, pulse_generator):
        self.pulse_generator = pulse_generator

    def on_shutdown(self):
        # turn pump off
        self.pump_button.setChecked(False)
        # stop pulsing
        self.pulse_button.setChecked(False)
        # open valves
        self.pressurize_button.setChecked(True)
        self.depressurize_button.setChecked(True)

        # wait 3 seconds and then set the buttons to unchecked
        # only if currently in manual, as in console mode closing the valves returns control to console
        if not self.mode_button.isChecked():
            self.pressurize_button.setEnabled(False)
            self.depressurize_button.setEnabled(False)
            self.pump_button.setEnabled(False)
            self.pulse_button.setEnabled(False)
            QTimer.singleShot(1000, self.reset_valves)

        # revert to manual mode
        self.mode_button.setChecked(False)

    def reset_valves(self):
        self.pressurize_button.setEnabled(True)
        self.depressurize_button.setEnabled(True)
        self.pump_button.setEnabled(True)
        self.pulse_button.setEnabled(True)

        self.pressurize_button.setChecked(False)
        self.depressurize_button.setChecked(False)

    def reset(self):
        # Reset buttons to initial states without triggering their slots
        for button in [self.pump_button, self.pressurize_button, self.depressurize_button, self.pulse_button]:
            button.blockSignals(True)
            button.setChecked(False)
            button.blockSignals(False)

        # Change to manual mode
        self.mode_button.setChecked(False)
