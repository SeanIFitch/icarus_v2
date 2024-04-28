# GUI imports
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QMainWindow,
    QGridLayout,
    QWidget,
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
from LogReader import LogReader


# Can be either in log reading or device mode.
class MainWindow(QMainWindow):

    # Initializes all widgets and sets layout
    def __init__(self, config_manager):
        super(MainWindow, self).__init__()

        self.config_manager = config_manager
        self.log_reader = LogReader()
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
        self.log_control_panel = LogControlPanel()
        self.counter_display = CounterDisplay(config_manager)
        self.pressure_display = PressureDisplay()

        # ToolBar
        self.toolbar = ToolBar(config_manager, self.log_reader, self.history_plot)
        self.addToolBar(Qt.BottomToolBarArea, self.toolbar)
        self.toolbar.set_mode_signal.connect(self.set_mode)

        # Set main layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.pressurize_plot, 0, 0)
        self.layout.addWidget(self.depressurize_plot, 1, 0)
        self.layout.addWidget(self.period_plot, 2, 0)
        self.layout.addWidget(self.history_plot, 0, 1, 3, 1)
        self.layout.addWidget(self.pressure_display, 0, 2)
        self.layout.addWidget(self.device_control_panel, 1, 2)
        self.layout.addWidget(self.log_control_panel, 1, 2)
        self.layout.addWidget(self.counter_display, 2, 2)

        # Add layout to dummy widget and apply to main window
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        # Default to device mode
        self.mode = "device"
        self.log_control_panel.hide()



    # Connects widgets to backend
    def set_device(self, data_handler):
        self.data_handler = data_handler
        self.device_control_panel.set_pulse_generator(data_handler.pulse_generator)

        # Connections that are never disconnected
        self.data_handler.pressure_event_signal.connect(self.pressure_display.update_pressure)
        self.data_handler.pressurize_event_signal.connect(self.counter_display.increment_count)
        self.data_handler.depressurize_event_signal.connect(self.counter_display.increment_count)

        # Remainder of connections
        if self.mode == "device":
            self.set_mode("device")


    def set_mode(self, mode):
        if mode == "log":
            if self.mode != 'log':
                self.mode = "log"
                self.device_control_panel.hide()
                self.log_control_panel.show()

            # Disconnect device signals from gui elements (excludes pressure display and counter display)
            self.data_handler.pressurize_event_signal.disconnect(self.pressurize_plot.update_data)
            self.data_handler.depressurize_event_signal.disconnect(self.depressurize_plot.update_data)
            self.data_handler.period_event_signal.disconnect(self.period_plot.update_data)
            self.data_handler.pressurize_event_signal.disconnect(self.history_plot.add_event)
            self.data_handler.depressurize_event_signal.disconnect(self.history_plot.add_event)

            # Connect loader signals to event plots
            #self.loader.pressurize_event_signal.connect(self.pressurize_plot.update_data)
            #self.loader.depressurize_event_signal.connect(self.depressurize_plot.update_data)
            #self.loader.period_event_signal.connect(self.period_plot.update_data)

            # Clear plots
            self.history_plot.reset_history()
            # Load history
            self.history_plot.load_event_list(self.log_reader.events)

        elif mode == "device":
            if self.mode != 'device':
                self.mode = "device"
                self.log_control_panel.hide()
                self.device_control_panel.show()

            # Connect device event signals to GUI elements
            self.data_handler.pressurize_event_signal.connect(self.pressurize_plot.update_data)
            self.data_handler.depressurize_event_signal.connect(self.depressurize_plot.update_data)
            self.data_handler.period_event_signal.connect(self.period_plot.update_data)
            self.data_handler.pressurize_event_signal.connect(self.history_plot.add_event)
            self.data_handler.depressurize_event_signal.connect(self.history_plot.add_event)

            # Clear plots
            self.history_plot.reset_history()

        else:
            raise RuntimeError(f"Unknown mode: {mode}")


    # Runs on quitting the application
    def closeEvent(self, event):
        super().closeEvent(event)

        if self.data_handler is not None:
            self.data_handler.quit()
