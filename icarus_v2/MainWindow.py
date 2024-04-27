# GUI imports
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QMainWindow,
    QGridLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QToolBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction
from EventPlot import EventPlot
from HistoryPlot import HistoryPlot
from ControlPanel import ControlPanel
from CounterDisplay import CounterDisplay
from TimingDisplay import TimingDisplay
from PressureDisplay import PressureDisplay
from SettingsDialog import SettingsDialog

from Event import Event
from LogReader import LogReader


class MainWindow(QMainWindow):

    # Initializes all widgets and sets layout
    def __init__(self, config_manager):
        super(MainWindow, self).__init__()

        self.config_manager = config_manager
        self.data_handler = None

        # Window settings
        self.setWindowTitle("Icarus NMR")
        self.showMaximized()
        self.setMinimumSize(QSize(800, 600))

        # Setup the toolbar
        self.toolbar = QToolBar()
        self.addToolBar(Qt.BottomToolBarArea, self.toolbar)
        self.toolbar.setMovable(False)
        # Add a settings button
        settings_action = QAction(QIcon(), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        self.toolbar.addAction(settings_action)
        # Add a history reset button
        self.history_reset_action = QAction(QIcon(), "Reset History", self)
        self.toolbar.addAction(self.history_reset_action)

        # Initialize all widgets

        # Pressure event plots
        self.pressure_event_display_range = (-10,140) # How much data to view around pressurize events
        sample_rate = 4000
        self.pressurize_plot = EventPlot(Event.PRESSURIZE, self.config_manager)
        self.depressurize_plot = EventPlot(Event.DEPRESSURIZE, self.config_manager)
        self.period_plot = EventPlot(Event.PERIOD, self.config_manager)

        # History plots
        self.history_plot = HistoryPlot(sample_rate, config_manager)

        # Logging
        self.file_button = QPushButton("Choose File")
        self.last_event_button = QPushButton("Last Event")
        self.next_event_button = QPushButton("Next Event")
        button_layout = QGridLayout()
        button_layout.addWidget(self.last_event_button, 0, 0)
        button_layout.addWidget(self.next_event_button, 0, 1)
        button_layout.addWidget(self.file_button, 1, 0, 1, 1)

        # Device control panel
        self.control_panel = ControlPanel()

        # Info displays
        self.counter_display = CounterDisplay()
        self.timing_display = TimingDisplay()
        self.pressure_display = PressureDisplay()

        # Set main layout
        main_layout = QGridLayout()
        main_layout.addWidget(self.pressurize_plot, 0, 0)
        main_layout.addWidget(self.depressurize_plot, 1, 0)
        main_layout.addWidget(self.period_plot, 2, 0)
        main_layout.addWidget(self.timing_display, 3, 0)
        main_layout.addWidget(self.history_plot, 0, 1, 3, 1)
        main_layout.addLayout(button_layout, 3, 1)
        main_layout.addWidget(self.pressure_display, 0, 2)
        main_layout.addWidget(self.control_panel, 1, 2, 2, 2)
        main_layout.addWidget(self.counter_display, 3, 2)

        # Add layout to dummy widget and apply to main window
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)


    def on_file(self):
        file = QFileDialog.getOpenFileName(self, "Open Log", "logs", "Log Files (*.xz)")[0]
        self.loader.read_events(file)
        print(len(self.loader.events))


    def init_loader(self):
        # Loader
        self.loader = LogReader()
        self.last_event_button.clicked.connect(self.loader.emit_last_event)
        self.next_event_button.clicked.connect(self.loader.emit_next_event)
        self.file_button.clicked.connect(self.on_file)

        self.loader.pressurize_event_signal.connect(self.pressurize_plot.update_data)
        self.loader.depressurize_event_signal.connect(self.depressurize_plot.update_data)
        self.loader.period_event_signal.connect(self.period_plot.update_data)


    # Connects widgets to backend
    def set_device(self, data_handler):
        self.data_handler = data_handler

        # Event Plots
        data_handler.pressurize_handler.event_signal.connect(self.pressurize_plot.update_data)
        data_handler.depressurize_handler.event_signal.connect(self.depressurize_plot.update_data)
        data_handler.period_handler.event_signal.connect(self.period_plot.update_data)

        # History plot
        data_handler.pressurize_handler.event_signal.connect(self.history_plot.add_event)
        data_handler.depressurize_handler.event_signal.connect(self.history_plot.add_event)
        self.history_reset_action.triggered.connect(self.history_plot.reset_history)

        # Timings display
        data_handler.pressurize_handler.event_signal.connect(self.timing_display.update_widths)
        data_handler.depressurize_handler.event_signal.connect(self.timing_display.update_widths)
        data_handler.period_handler.event_signal.connect(self.timing_display.update_widths)

        # Pressure display
        data_handler.pressure_handler.event_signal.connect(self.pressure_display.update_pressure)

        # Control panel
        self.control_panel.set_pulse_generator(data_handler.pulse_generator)

        # Counter display
        data_handler.counter.update_counts.connect(self.counter_display.update_counts)
        self.counter_display.update_counts(data_handler.counter.counts)


    # Runs on quitting the application
    def closeEvent(self, event):
        super().closeEvent(event)

        if self.data_handler is not None:
            self.data_handler.quit()


    def open_settings(self):
        # Open the settings dialog
        dialog = SettingsDialog(self.config_manager)
        dialog.exec()
