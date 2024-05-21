from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QCheckBox,
    QSpacerItem,
    QSizePolicy
)
from PySide6.QtGui import QDoubleValidator, QIntValidator
from ErrorDialog import open_error_dialog
from Event import Channel, get_channel
import numpy as np
from PySide6.QtCore import Qt
from time import sleep


class SettingsDialog(QDialog):
    def __init__(self, config_manager, connected, pressure_signal, parent=None):
        super().__init__()

        self.config_manager = config_manager
        self.pressure_signal = pressure_signal

        # Allow only positive floating-point numbers
        positive_float = QDoubleValidator()
        positive_int = QIntValidator()
        positive_float.setBottom(0)
        positive_int.setBottom(0)
        # Width of edit boxes
        edit_width = 190

        # View section
        self.hide_valve_checkbox = QCheckBox()
        hide_valve = self.config_manager.get_settings('hide_valve_sensors')
        self.hide_valve_checkbox.setCheckState(Qt.Checked if hide_valve else Qt.Unchecked)
        self.hide_valve_checkbox.stateChanged.connect(self.set_hide_valve)
        self.hide_valve_checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 23px;
                height: 23px;
            }
            """)
        view_layout = QGridLayout()
        view_layout.addWidget(QLabel("Hide Valve Sensors:"), 0, 0)
        view_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Preferred), 0, 1)
        view_layout.addWidget(self.hide_valve_checkbox, 0, 2)
        view_group = QGroupBox("View")
        view_group.setLayout(view_layout)

        # Pulse timings section
        self.pressurize_width_edit = QLineEdit()
        self.depressurize_width_edit = QLineEdit()
        self.period_width_edit = QLineEdit()
        self.delay_width_edit = QLineEdit()
        self.pressurize_width_edit.setFixedWidth(edit_width)
        self.depressurize_width_edit.setFixedWidth(edit_width)
        self.period_width_edit.setFixedWidth(edit_width)
        self.delay_width_edit.setFixedWidth(edit_width)
        self.pressurize_width_edit.setValidator(positive_float)
        self.depressurize_width_edit.setValidator(positive_float)
        self.period_width_edit.setValidator(positive_float)
        self.delay_width_edit.setValidator(positive_float)
        self.coefficients = self.config_manager.get_settings('plotting_coefficients')
        self.timing_settings = self.config_manager.get_settings('timing_settings')
        self.pressurize_width_edit.setText(str(self.timing_settings['pressurize_width']))
        self.depressurize_width_edit.setText(str(self.timing_settings['depressurize_width']))
        self.period_width_edit.setText(str(self.timing_settings['period_width']))
        self.delay_width_edit.setText(str(self.timing_settings['delay_width']))
        self.pressurize_width_edit.textChanged.connect(self.set_pressurize_width)
        self.depressurize_width_edit.textChanged.connect(self.set_depressurize_width)
        self.period_width_edit.textChanged.connect(self.set_period_width)
        self.delay_width_edit.textChanged.connect(self.set_delay_width)

        timings_layout = QGridLayout()
        timings_layout.addWidget(QLabel("Pressurize Width (ms):"), 0, 0)
        timings_layout.addWidget(QLabel("Depressurize Width (ms):"), 1, 0)
        timings_layout.addWidget(QLabel("Period (s):"), 2, 0)
        timings_layout.addWidget(QLabel("Delay (s):"), 3, 0)
        timings_layout.addWidget(self.pressurize_width_edit, 0, 1)
        timings_layout.addWidget(self.depressurize_width_edit, 1, 1)
        timings_layout.addWidget(self.period_width_edit, 2, 1)
        timings_layout.addWidget(self.delay_width_edit, 3, 1)
        timings_group = QGroupBox("Pulse Timings")
        timings_group.setLayout(timings_layout)

        # Hardware section
        self.pump_count_edit = QLineEdit()
        self.pressurize_count_edit = QLineEdit()
        self.depressurize_count_edit = QLineEdit()
        self.recalibrate_button = QPushButton("Recalibrate")
        self.recalibrate_button.setEnabled(connected)
        self.pump_count_edit.setFixedWidth(edit_width)
        self.pressurize_count_edit.setFixedWidth(edit_width)
        self.depressurize_count_edit.setFixedWidth(edit_width)
        self.pump_count_edit.setValidator(positive_int)
        self.pressurize_count_edit.setValidator(positive_int)
        self.depressurize_count_edit.setValidator(positive_int)
        self.counter_settings = self.config_manager.get_settings('counter_settings')
        self.pump_count_edit.setText(str(self.counter_settings['pump_count']))
        self.pressurize_count_edit.setText(str(self.counter_settings['pressurize_count']))
        self.depressurize_count_edit.setText(str(self.counter_settings['depressurize_count']))
        self.pump_count_edit.textChanged.connect(self.set_pump_count)
        self.pressurize_count_edit.textChanged.connect(self.set_pressurize_count)
        self.depressurize_count_edit.textChanged.connect(self.set_depressurize_count)
        self.recalibrate_button.clicked.connect(self.get_recalibration)

        hardware_layout = QGridLayout()
        hardware_layout.addWidget(QLabel("Pump Count:"), 0, 0)
        hardware_layout.addWidget(QLabel("Pressurize Count:"), 1, 0)
        hardware_layout.addWidget(QLabel("Depressurize Count"), 2, 0)
        hardware_layout.addWidget(QLabel("Recalibrate Sensors:"), 3, 0)
        hardware_layout.addWidget(self.pump_count_edit, 0, 1)
        hardware_layout.addWidget(self.pressurize_count_edit, 1, 1)
        hardware_layout.addWidget(self.depressurize_count_edit, 2, 1)
        hardware_layout.addWidget(self.recalibrate_button, 3, 1)
        hardware_group = QGroupBox("Hardware")
        hardware_group.setLayout(hardware_layout)

        # Button to apply changes
        buttons = QDialogButtonBox.Apply
        button_box = QDialogButtonBox(buttons)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

        # Dialog configuration
        self.setWindowTitle("Settings")
        self.setWindowModality(Qt.ApplicationModal)
        self.setStyleSheet("font-size: 17pt;")

        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(view_group)
        main_layout.addWidget(timings_group)
        main_layout.addWidget(hardware_group)
        main_layout.addWidget(button_box)

        # Default selection
        button_box.button(QDialogButtonBox.Apply).setFocus()


    # Apply changes to config_manager and close the dialog
    # Also does some minor error checking for timing settings
    def apply(self) -> None:
        error = None
        if self.timing_settings['pressurize_width'] < 8:
            error = "Pressurize width should be greater than 8ms."
        elif self.timing_settings['depressurize_width'] < 8:
            error = "Depressurize width should be greater than 8ms."
        elif self.timing_settings['period_width'] < 3:
            error = "Period width should be greater than 3s."
        elif self.timing_settings['delay_width'] < 0.05:
            error = "Delay width should be greater than 0.05s."
        elif self.timing_settings['pressurize_width'] / 1000 >= self.timing_settings['period_width']:
            error = "Pressurize width should be less than Period width."
        elif self.timing_settings['depressurize_width'] / 1000 >= self.timing_settings['period_width']:
            error = "Depressurize width should be less than Period width."
        elif self.timing_settings['delay_width'] >= self.timing_settings['period_width']:
            error = "Delay width should be less than Period width."

        if error is not None:
            open_error_dialog(error, QDialogButtonBox.Ok, self)
            # Do not apply changes or close window
            return

        self.config_manager.save_settings("timing_settings", self.timing_settings)
        self.config_manager.save_settings("counter_settings", self.counter_settings)
        self.close()


    def set_pressurize_width(self, pressurize_width):
        try:
            pressurize_width = float(pressurize_width)
        except:
            return
        self.timing_settings['pressurize_width'] = pressurize_width

    def set_depressurize_width(self, depressurize_width):
        try:
            depressurize_width = float(depressurize_width)
        except:
            return
        self.timing_settings['depressurize_width'] = depressurize_width

    def set_period_width(self, period_width):
        try:
            period_width = float(period_width)
        except:
            return
        self.timing_settings['period_width'] = period_width

    def set_delay_width(self, delay_width):
        try:
            delay_width = float(delay_width)
        except:
            return
        self.timing_settings['delay_width'] = delay_width

    def set_pressurize_count(self, pressurize_count):
        try:
            pressurize_count = int(pressurize_count)
        except:
            return
        self.counter_settings['pressurize_count'] = pressurize_count

    def set_depressurize_count(self, depressurize_count):
        try:
            depressurize_count = int(depressurize_count)
        except:
            return
        self.counter_settings['depressurize_count'] = depressurize_count

    def set_pump_count(self, pump_count):
        try:
            pump_count = int(pump_count)
        except:
            return
        self.counter_settings['pump_count'] = pump_count

    # Make target and sample match origin
    def get_recalibration(self):
        def recalibrate(event):
            origin_avg = np.mean(get_channel(event, Channel.HI_PRE_ORIG))
            sample_avg = np.mean(get_channel(event, Channel.HI_PRE_SAMPLE))
            target_avg = np.mean(get_channel(event, Channel.TARGET))

            origin_pressure = origin_avg * self.coefficients[Channel.HI_PRE_ORIG]
            sample_coefficient = origin_pressure / sample_avg
            target_coefficient = origin_pressure / target_avg

            self.coefficients[Channel.HI_PRE_SAMPLE] = sample_coefficient
            self.coefficients[Channel.TARGET] = target_coefficient

        # Send pressure readings exactly once
        self.pressure_signal.connect(recalibrate, type=Qt.SingleShotConnection)
        sleep(0.4) # Time for a pressure event * 2
        self.config_manager.save_settings('plotting_coefficients', self.coefficients)

    def set_hide_valve(self, state):
        self.config_manager.save_settings('hide_valve_sensors', bool(state))

    def set_connected(self, connected):
        self.recalibrate_button.setEnabled(connected)

    def set_pressure_signal(self, pressure_signal):
        self.pressure_signal = pressure_signal
