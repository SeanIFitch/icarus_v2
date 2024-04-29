# GUI imports
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QMainWindow,
    QGridLayout,
    QWidget,
    QGroupBox, 
    QSizePolicy
)
from PySide6.QtCore import Qt
from EventPlot import EventPlot
from HistoryPlot import HistoryPlot
from DeviceControlPanel import DeviceControlPanel
from LogControlPanel import LogControlPanel
from CounterDisplay import CounterDisplay
from PressureDisplay import PressureDisplay
from ToolBar import ToolBar

from Event import Event


# Can be either in log reading or device mode.
class MainWindow(QMainWindow):

    # Initializes all widgets and sets layout
    def __init__(self, config_manager):
        super(MainWindow, self).__init__()

        self.config_manager = config_manager
        self.data_handler = None

        # Window settings
        self.setWindowTitle("Icarus NMR")
        self.setMinimumSize(QSize(800, 600))

        # Initialize all widgets
        self.pressure_event_display_range = (-10,140) # How much data to view around pressurize events
        self.pressurize_plot = EventPlot(Event.PRESSURIZE, self.config_manager)
        self.depressurize_plot = EventPlot(Event.DEPRESSURIZE, self.config_manager)
        self.period_plot = EventPlot(Event.PERIOD, self.config_manager)
        self.history_plot = HistoryPlot(config_manager)
        self.device_control_panel = DeviceControlPanel()
        self.counter_display = CounterDisplay(config_manager)
        self.pressure_display = PressureDisplay(config_manager)

        self.log_control_panel = LogControlPanel()
        self.log_control_panel.pressurize_event_signal.connect(self.pressurize_plot.update_data)
        self.log_control_panel.pressurize_event_signal.connect(self.history_plot.render_pressurize_time)
        self.log_control_panel.depressurize_event_signal.connect(self.depressurize_plot.update_data)
        self.log_control_panel.depressurize_event_signal.connect(self.history_plot.render_depressurize_time)
        self.log_control_panel.period_event_signal.connect(self.period_plot.update_data)
        self.log_control_panel.event_list_signal.connect(self.history_plot.load_event_list)
        self.log_control_panel.reset_history_signal.connect(self.history_plot.reset_history)
        self.log_control_panel.reset_history_signal.connect(self.pressurize_plot.reset_history)
        self.log_control_panel.reset_history_signal.connect(self.depressurize_plot.reset_history)
        self.log_control_panel.reset_history_signal.connect(self.period_plot.reset_history)

        # ToolBar
        self.toolbar = ToolBar(config_manager)
        self.addToolBar(Qt.BottomToolBarArea, self.toolbar)
        self.toolbar.set_mode_signal.connect(self.set_mode)
        self.toolbar.history_reset_action.triggered.connect(self.history_plot.reset_history)

        # Control and value layout
        # Show bounding box even when no controls are displayed
        self.bounding_box = QGroupBox()
        self.bounding_box.setFixedSize(194, 321)
        control_layout = QGridLayout()
        control_layout.addWidget(self.pressure_display, 0,0)
        control_layout.addWidget(self.device_control_panel, 2, 0)
        control_layout.addWidget(self.log_control_panel, 2, 0)
        control_layout.addWidget(self.bounding_box, 2, 0)
        control_layout.addWidget(self.counter_display, 1, 0)

        # Set main layout
        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.pressurize_plot, 0, 0)
        self.main_layout.addWidget(self.depressurize_plot, 1, 0)
        self.main_layout.addWidget(self.period_plot, 2, 0)
        self.main_layout.addWidget(self.history_plot, 0, 1, 3, 1)
        self.main_layout.addLayout(control_layout, 0, 2, 2, 2)
        # Make event plots keep same height
        self.period_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

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

        # Connections that are never disconnected
        data_handler.pressure_event_signal.connect(self.pressure_display.update_pressure)
        data_handler.pressurize_event_signal.connect(self.counter_display.increment_count)
        data_handler.depressurize_event_signal.connect(self.counter_display.increment_count)
        data_handler.acquiring_signal.connect(lambda x: self.set_connected(x))

        # Connect plot signals
        self.set_mode(self.mode)


    # Set device signal connections, clear history, set control panel
    def set_mode(self, mode):
        self.mode = mode
        if mode == "log":
            self.device_control_panel.hide()
            self.bounding_box.hide()
            self.log_control_panel.show()

            # Disconnect device signals from gui elements (excludes pressure display and counter display)
            if self.data_handler is not None:
                self.data_handler.pressurize_event_signal.disconnect(self.pressurize_plot.update_data)
                self.data_handler.depressurize_event_signal.disconnect(self.depressurize_plot.update_data)
                self.data_handler.period_event_signal.disconnect(self.period_plot.update_data)
                self.data_handler.pressurize_event_signal.disconnect(self.history_plot.add_event)
                self.data_handler.depressurize_event_signal.disconnect(self.history_plot.add_event)

            # Clear plots
            self.history_plot.reset_history()
            self.pressurize_plot.reset_history()
            self.depressurize_plot.reset_history()
            self.period_plot.reset_history()


        elif mode == "device":
            if self.connected:
                self.log_control_panel.hide()
                self.bounding_box.hide()
                self.device_control_panel.show()
            else:
                self.log_control_panel.hide()
                self.device_control_panel.hide()
                self.bounding_box.show()

            # Connect device event signals to GUI elements
            if self.data_handler is not None:
                self.data_handler.pressurize_event_signal.connect(self.pressurize_plot.update_data)
                self.data_handler.depressurize_event_signal.connect(self.depressurize_plot.update_data)
                self.data_handler.period_event_signal.connect(self.period_plot.update_data)
                self.data_handler.pressurize_event_signal.connect(self.history_plot.add_event)
                self.data_handler.depressurize_event_signal.connect(self.history_plot.add_event)

            # Clear plots
            self.history_plot.reset_history()
            self.pressurize_plot.reset_history()
            self.depressurize_plot.reset_history()
            self.period_plot.reset_history()


    # Set control panel, clear pressure
    def set_connected(self, connected):
        self.connected = connected
        if connected:
            self.device_control_panel.reset()
            if self.mode == "device":
                self.bounding_box.hide()
                self.device_control_panel.show()
        else:
            self.pressure_display.reset()
            if self.mode == "device":
                self.bounding_box.show()
                self.device_control_panel.hide()


    # Runs on quitting the application
    def closeEvent(self, event):
        super().closeEvent(event)

        if self.data_handler is not None:
            self.data_handler.quit()
