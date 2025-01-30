# GUI imports
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QGroupBox,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget
)
from icarus_v2.gui.event_plot import EventPlot
from icarus_v2.gui.history_plot import HistoryPlot
from icarus_v2.gui.device_control_panel import DeviceControlPanel
from icarus_v2.gui.log_control_panel import LogControlPanel
from icarus_v2.gui.counter_display import CounterDisplay
from icarus_v2.gui.pressure_display import PressureDisplay
from icarus_v2.gui.tool_bar import ToolBar
from icarus_v2.gui.error_dialog import open_error_dialog
from icarus_v2.backend.log_reader import LogReader
from icarus_v2.backend.event import Event
from icarus_v2.qdarktheme.load_style import load_stylesheet
from icarus_v2.gui.settings_dialog import SettingsDialog


# Can be either in log reading or device mode.
class MainWindow(QMainWindow):

    # Initializes all widgets and sets layout
    def __init__(self, config_manager):
        super(MainWindow, self).__init__()
        self.mode = None

        self.config_manager = config_manager
        self.data_handler = None

        # Window settings
        self.setWindowTitle("Icarus NMR")
        self.setMinimumSize(QSize(1000, 760))
        self.setStyleSheet("font-size: 17pt;")
        self.setAttribute(Qt.WA_AcceptTouchEvents, False)
        self.settings_dialog = SettingsDialog(self.config_manager, connected=False, pressure_signal=None, sentry=None)
        self.settings_dialog.theme_changed.connect(self.update_plots)

        # Initialize all widgets
        self.pressure_event_display_range = (-10, 140)  # How much data to view around pressurize events
        self.pressurize_plot = EventPlot(Event.PRESSURIZE, self.config_manager, parent=self)
        self.depressurize_plot = EventPlot(Event.DEPRESSURIZE, self.config_manager, parent=self)
        self.period_plot = EventPlot(Event.PERIOD, self.config_manager, parent=self)
        self.history_plot = HistoryPlot(config_manager)
        self.device_control_panel = DeviceControlPanel()
        self.device_control_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.counter_display = CounterDisplay(config_manager)
        self.pressure_display = PressureDisplay(config_manager)

        self.log_control_panel = LogControlPanel(self.config_manager)
        self.log_control_panel.pressurize_event_signal.connect(self.pressurize_plot.update_data)
        self.log_control_panel.pressurize_event_signal.connect(self.history_plot.render_pressurize_time)
        self.log_control_panel.depressurize_event_signal.connect(self.depressurize_plot.update_data)
        self.log_control_panel.depressurize_event_signal.connect(self.history_plot.render_depressurize_time)
        self.log_control_panel.period_event_signal.connect(self.period_plot.update_data)
        self.log_control_panel.event_list_signal.connect(self.history_plot.load_event_list)
        self.log_control_panel.reset_history_signal.connect(self.reset_history)
        self.log_control_panel.sample_sensor_connected.connect(self.set_sample_sensor_connected)
        self.log_control_panel.log_coefficients_signal.connect(self.pressurize_plot.set_log_coefficients)
        self.log_control_panel.log_coefficients_signal.connect(self.depressurize_plot.set_log_coefficients)
        self.log_control_panel.log_coefficients_signal.connect(self.period_plot.set_log_coefficients)
        self.log_control_panel.log_coefficients_signal.connect(self.history_plot.set_log_coefficients)
        self.log_control_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ToolBar
        self.toolbar = ToolBar(config_manager, self)
        self.addToolBar(self.toolbar)
        self.toolbar.set_mode_signal.connect(self.set_mode)
        self.toolbar.history_reset_action.triggered.connect(self.reset_history)

        # Control and value layout
        # Show bounding box even when no controls are displayed
        self.bounding_box = QGroupBox()
        spacer = QSpacerItem(0, 0, QSizePolicy.Preferred, QSizePolicy.Expanding)
        box_layout = QVBoxLayout()
        box_layout.addItem(spacer)
        self.bounding_box.setLayout(box_layout)
        self.bounding_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bounding_box.setMinimumWidth(287)  # Width of DeviceControlPanel

        # Control layout
        control_layout = QGridLayout()
        control_layout.addWidget(self.pressure_display, 0, 0)

        #Stacked Widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.device_control_panel)
        self.stacked_widget.addWidget(self.log_control_panel)
        self.stacked_widget.addWidget(self.bounding_box)
        self.stacked_widget.setCurrentWidget(self.bounding_box)
        self.stacked_widget.setFixedWidth(329)
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.stacked_widget)

        control_layout.addWidget(self.counter_display, 2, 0)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setColumnStretch(0, 1)

        # Event plot layout
        event_layout = QVBoxLayout()
        event_layout.addWidget(self.pressurize_plot)
        event_layout.addWidget(self.depressurize_plot)
        event_layout.addWidget(self.period_plot)

        # Set layout
        self.main_layout = QHBoxLayout()
        self.main_layout.addLayout(event_layout)
        self.main_layout.addWidget(self.history_plot)
        self.main_layout.addLayout(control_layout)

        # Add layout to dummy widget and apply to main window
        widget = QWidget()
        widget.setLayout(self.main_layout)
        self.setCentralWidget(widget)

        self.connected = False
        self.set_mode("device")

    # Connects widgets to backend
    def set_device(self, data_handler):
        self.data_handler = data_handler
        self.device_control_panel.set_pulse_generator(data_handler.pulse_generator)
        self.log_control_panel.log_reader.set_logger(data_handler.logger)
        self.toolbar.set_pressure_signal(data_handler.pressure_event_signal)
        self.toolbar.set_sentry(data_handler.sentry)

        # Connections that are never disconnected
        data_handler.pressure_event_signal.connect(self.pressure_display.update_pressure)
        data_handler.pressurize_event_signal.connect(self.counter_display.increment_count)
        data_handler.depressurize_event_signal.connect(self.counter_display.increment_count)
        data_handler.pump_event_signal.connect(self.counter_display.increment_count)
        data_handler.acquiring_signal.connect(lambda x: self.set_connected(x))
        data_handler.toolbar_warning.connect(self.toolbar.display_warning)
        # Ideally this is unnecessary as the signal should be directly sent to the pulse_generator. This is a workaround
        data_handler.shutdown_signal.connect(self.device_control_panel.on_shutdown)

        def error_dialog(err):
            self.dialog = open_error_dialog(err)
        data_handler.display_error.connect(error_dialog)

        # Connect plot signals
        self.set_mode(self.mode)

    # Set device signal connections, clear history, set control panel
    def set_mode(self, mode):
        self.mode = mode
        if mode == "log":
            
            self.stacked_widget.setCurrentWidget(self.log_control_panel)

            # Disconnect device signals from gui elements (excludes pressure display and counter display)
            if self.data_handler is not None:
                self.data_handler.pressurize_event_signal.disconnect(self.pressurize_plot.update_data)
                self.data_handler.depressurize_event_signal.disconnect(self.depressurize_plot.update_data)
                self.data_handler.period_event_signal.disconnect(self.period_plot.update_data)
                self.data_handler.pressurize_event_signal.disconnect(self.history_plot.add_event)
                self.data_handler.depressurize_event_signal.disconnect(self.history_plot.add_event)
                self.data_handler.log_signal.disconnect(self.reset_history)
                self.data_handler.sample_sensor_connected.disconnect(self.set_sample_sensor_connected)

            # Clear plots
            self.reset_history()

        elif mode == "device":
            if self.connected:
                self.stacked_widget.setCurrentWidget(self.device_control_panel)
            else:
                self.stacked_widget.setCurrentWidget(self.bounding_box)

            # Connect device event signals to GUI elements
            if self.data_handler is not None:
                self.data_handler.pressurize_event_signal.connect(self.pressurize_plot.update_data)
                self.data_handler.depressurize_event_signal.connect(self.depressurize_plot.update_data)
                self.data_handler.period_event_signal.connect(self.period_plot.update_data)
                self.data_handler.pressurize_event_signal.connect(self.history_plot.add_event)
                self.data_handler.depressurize_event_signal.connect(self.history_plot.add_event)
                self.data_handler.log_signal.connect(self.reset_history)
                self.data_handler.sample_sensor_connected.connect(self.set_sample_sensor_connected)

            # Clear plots
            self.reset_history()

            # restore history
            if self.connected:
                current_log_file = self.data_handler.logger.filename
                self.data_handler.logger.flush()
                reader = LogReader()
                reader.read_events(current_log_file)
                self.history_plot.load_event_list(reader.events)
                press = None
                depress = None
                per = None
                for event in reader.events[::-1]:
                    if press is None and event.event_type == Event.PRESSURIZE:
                        press = event
                    elif depress is None and event.event_type == Event.DEPRESSURIZE:
                        depress = event
                    elif per is None and event.event_type == Event.PERIOD:
                        per = event
                    if press is not None and depress is not None and per is not None:
                        break
                self.pressurize_plot.update_data(press)
                self.depressurize_plot.update_data(depress)
                self.period_plot.update_data(per)

    # Set control panel, clear pressure
    def set_connected(self, connected):
        self.connected = connected
        self.toolbar.set_connected(connected)
        self.log_control_panel.set_logging(connected)
        if connected:
            self.device_control_panel.reset()
            if self.mode == "device":
                self.stacked_widget.setCurrentWidget(self.device_control_panel)
        else:
            self.pressure_display.reset()
            if self.mode == "device":
                self.stacked_widget.setCurrentWidget(self.bounding_box)

    def set_sample_sensor_connected(self, connected):
        self.history_plot.set_sample_sensor(connected)
        self.pressurize_plot.set_sample_sensor(connected)
        self.depressurize_plot.set_sample_sensor(connected)
        self.period_plot.set_sample_sensor(connected)

    def reset_history(self):
        self.set_sample_sensor_connected(True)

        self.history_plot.reset_history()
        self.pressurize_plot.reset_history()
        self.depressurize_plot.reset_history()
        self.period_plot.reset_history()

    def update_plots(self):
        self.pressurize_plot.update_theme('pressure')
        self.depressurize_plot.update_theme('depressure')
        self.period_plot.update_theme('period')

        self.history_plot.update_theme()

    # Runs on quitting the application
    def closeEvent(self, event):
        super().closeEvent(event)

        if self.data_handler is not None:
            self.data_handler.quit()
