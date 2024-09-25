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
    QSizePolicy,
    QWidget,
    QStackedWidget,
    QToolBar
)
from PySide6.QtGui import QDoubleValidator, QIntValidator, QAction
from icarus_v2.gui.error_dialog import open_error_dialog
from icarus_v2.backend.event import Channel, get_channel
import numpy as np
from PySide6.QtCore import Qt
from time import sleep


class SettingsDialog(QDialog):
    def __init__(self, config_manager, connected, pressure_signal, sentry, parent=None):
        super().__init__(parent=parent)

        self.config_manager = config_manager
        self.pressure_signal = pressure_signal
        self.sentry = sentry

        # Create the toolbar
        toolbar = QToolBar(parent)
        action1 = QAction("General", self)
        action2 = QAction("Advanced", self)
        action1.triggered.connect(self.show_general)
        action2.triggered.connect(self.show_advanced)
        toolbar.addAction(action1)
        toolbar.addAction(action2)

        self.general_widget = self.get_default_widget(connected)
        self.advanced_widget = self.get_advanced_widget(connected)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.general_widget)
        self.stack.addWidget(self.advanced_widget)

        # Button to apply changes
        buttons = QDialogButtonBox.Apply
        button_box = QDialogButtonBox(buttons)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

        # Dialog configuration
        self.setWindowTitle("Settings")
        self.setStyleSheet("font-size: 17pt;")
        self.setMinimumWidth(610)

        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.stack)
        main_layout.addWidget(button_box)

        # Default selection
        button_box.button(QDialogButtonBox.Apply).setFocus()

    def get_default_widget(self, connected):
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

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(view_group)
        layout.addWidget(timings_group)
        layout.addWidget(hardware_group)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        return widget

    def get_advanced_widget(self, connected):
        # Allow only positive floating-point numbers
        positive_float = QDoubleValidator()
        positive_int = QIntValidator()
        positive_float.setBottom(0)
        positive_int.setBottom(1)
        # Width of edit boxes
        edit_width = 190

        self.depress_edit = QLineEdit()
        self.press_edit = QLineEdit()
        self.pump_rate_edit = QLineEdit()
        self.example_edit = QLineEdit()
        self.diff_count_error = QLineEdit()
        self.max_pump_edit = QLineEdit()
        self.pump_window_edit = QLineEdit()
        self.enable_sentry_button = QPushButton("Enable")
        self.enable_sentry_button.setEnabled(connected)

        self.depress_edit.setFixedWidth(edit_width)
        self.press_edit.setFixedWidth(edit_width)
        self.pump_rate_edit.setFixedWidth(edit_width)
        self.example_edit.setFixedWidth(edit_width)
        self.diff_count_error.setFixedWidth(edit_width)
        self.pump_window_edit.setFixedWidth(edit_width)
        self.max_pump_edit.setFixedWidth(edit_width)

        self.depress_edit.setValidator(positive_float)
        self.press_edit.setValidator(positive_float)
        self.pump_rate_edit.setValidator(positive_float)
        self.example_edit.setValidator(positive_int)
        self.diff_count_error.setValidator(positive_int)
        self.pump_window_edit.setValidator(positive_float)
        self.max_pump_edit.setValidator(positive_int)

        self.sentry_settings = self.config_manager.get_settings('sentry_settings')

        self.depress_edit.setText(str(self.sentry_settings['max_pressure_before_depress_decrease'] * 100))
        self.press_edit.setText(str(self.sentry_settings['max_pressure_before_depress_increase'] * 100))
        self.pump_rate_edit.setText(str(self.sentry_settings['max_pump_rate_increase'] * 100))
        self.example_edit.setText(str(self.sentry_settings['example_events']))
        self.diff_count_error.setText(str(self.sentry_settings['decrease_count_to_error']))
        self.max_pump_edit.setText(str(self.sentry_settings['max_pumps_in_window']))
        self.pump_window_edit.setText(str(self.sentry_settings['pump_window']))

        self.depress_edit.textChanged.connect(self.set_sentry_depress)
        self.press_edit.textChanged.connect(self.set_sentry_press)
        self.pump_rate_edit.textChanged.connect(self.set_sentry_pump_rate)
        self.example_edit.textChanged.connect(self.set_sentry_example)
        self.diff_count_error.textChanged.connect(self.set_sentry_diff_count)
        self.max_pump_edit.textChanged.connect(self.set_sentry_max_pumps)
        self.pump_window_edit.textChanged.connect(self.set_sentry_pump_window)
        self.enable_sentry_button.clicked.connect(self.enable_sentry)

        error_layout = QGridLayout()
        error_layout.addWidget(QLabel("Pressure Difference to Error Count:"), 0, 0)
        error_layout.addWidget(QLabel("Max Pump Count in Window:"), 1, 0)
        error_layout.addWidget(QLabel("Pump Window (s):"), 2, 0)
        error_layout.addWidget(self.diff_count_error, 0, 1)
        error_layout.addWidget(self.max_pump_edit, 1, 1)
        error_layout.addWidget(self.pump_window_edit, 2, 1)
        error_group = QGroupBox("Errors")
        error_group.setLayout(error_layout)

        warning_layout = QGridLayout()
        warning_layout.addWidget(QLabel("Max Pressure Decrease (%):"), 0, 0)
        warning_layout.addWidget(QLabel("Max Pressure Increase (%):"), 1, 0)
        warning_layout.addWidget(QLabel("Max Pump Rate Increase (%):"), 2, 0)
        warning_layout.addWidget(self.depress_edit, 0, 1)
        warning_layout.addWidget(self.press_edit, 1, 1)
        warning_layout.addWidget(self.pump_rate_edit, 2, 1)
        warning_group = QGroupBox("Warnings")
        warning_group.setLayout(warning_layout)

        misc_layout = QGridLayout()
        misc_layout.addWidget(QLabel("Example Event Count:"), 0, 0)
        misc_layout.addWidget(QLabel("Enable Sentry (until device disconnected):"), 1, 0)
        misc_layout.addWidget(self.example_edit, 0, 1)
        misc_layout.addWidget(self.enable_sentry_button, 1, 1)
        misc_group = QGroupBox("Sentry")
        misc_group.setLayout(misc_layout)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(error_group)
        layout.addWidget(warning_group)
        layout.addWidget(misc_group)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        return widget

    def show_general(self):
        self.stack.setCurrentIndex(0)

    def show_advanced(self):
        self.stack.setCurrentIndex(1)

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
        elif self.sentry_settings['example_events'] <= 1:
            error = "Example events should be greater than 1."
        elif self.sentry_settings['decrease_count_to_error'] <= 0:
            error = "Difference to error count should be greater than 0."

        if error is not None:
            self.dialog = open_error_dialog(error, QDialogButtonBox.Ok, self)
            # Do not apply changes or close window
            return

        self.config_manager.save_settings("timing_settings", self.timing_settings)
        self.config_manager.save_settings("counter_settings", self.counter_settings)
        self.config_manager.save_settings("sentry_settings", self.sentry_settings)
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
        sleep(0.4)  # Time for a pressure event * 2
        self.config_manager.save_settings('plotting_coefficients', self.coefficients)

    def set_hide_valve(self, state):
        self.config_manager.save_settings('hide_valve_sensors', bool(state))

    def set_connected(self, connected):
        self.recalibrate_button.setEnabled(connected)
        self.enable_sentry_button.setEnabled(connected)

    def set_pressure_signal(self, pressure_signal):
        self.pressure_signal = pressure_signal

    def set_sentry(self, sentry):
        self.sentry = sentry

    def set_sentry_depress(self, depress):
        try:
            depress = float(depress) / 100
        except:
            return
        self.sentry_settings['max_pressure_before_depress_decrease'] = depress

    def set_sentry_press(self, press):
        try:
            press = float(press) / 100
        except:
            return
        self.sentry_settings['max_pressure_before_depress_increase'] = press

    def set_sentry_pump_rate(self, pump_rate):
        try:
            pump_rate = float(pump_rate) / 100
        except:
            return
        self.sentry_settings['max_pump_rate_increase'] = pump_rate

    def set_sentry_example(self, example):
        try:
            example = int(example)
        except:
            return
        self.sentry_settings['example_events'] = example

    def set_sentry_diff_count(self, diff_count):
        try:
            diff_count = int(diff_count)
        except:
            return
        self.sentry_settings['decrease_count_to_error'] = diff_count

    def set_sentry_pump_window(self, pump_window):
        try:
            pump_window = float(pump_window)
        except:
            return
        self.sentry_settings['pump_window'] = pump_window

    def set_sentry_max_pumps(self, max_pumps):
        try:
            max_pumps = int(max_pumps)
        except:
            return
        self.sentry_settings['max_pumps_in_window'] = max_pumps

    def enable_sentry(self):
        self.sentry.handle_experiment(False)
