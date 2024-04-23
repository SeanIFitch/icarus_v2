# GUI imports
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QMainWindow,
    QGridLayout,
    QWidget,
    QPushButton
)
from EventPlot import EventPlot
from PressurePlot import PressurePlot
from SlopePlot import SlopePlot
from SwitchTimePlot import SwitchTimePlot
from ControlPanel import ControlPanel
from CounterDisplay import CounterDisplay
from TimingDisplay import TimingDisplay
from PressureDisplay import PressureDisplay

from EventLoader import EventLoader


class MainWindow(QMainWindow):

    # Initializes all widgets and sets layout
    def __init__(self):
        super(MainWindow, self).__init__()

        self.data_handler = None

        # Window settings
        self.setWindowTitle("Icarus NMR")
        self.setMinimumSize(QSize(800, 500))

        # Initialize all widgets

        # Pressure event plots
        self.pressure_event_display_range = (-10,140) # How much data to view around pressurize events
        display_offset = 10
        pressurize_channels = ['target', 'pre_low', 'pre_up', 'hi_pre_sample', 'depre_valve', 'pre_valve']
        depressurize_channels = ['target', 'depre_low', 'depre_up', 'hi_pre_sample', 'depre_valve', 'pre_valve']
        period_channels = ['target', 'hi_pre_orig', 'hi_pre_sample', 'pump', 'depre_valve', 'pre_valve']
        self.pressurize_plot = EventPlot(pressurize_channels, display_offset, "Pressurize")
        self.depressurize_plot = EventPlot(depressurize_channels, display_offset, "Depressurize")
        self.period_plot = EventPlot(period_channels, display_offset, "Period", x_unit="s")

        # History plots
        self.pressure_plot = PressurePlot()
        self.slope_plot = SlopePlot()
        self.switch_time_plot = SwitchTimePlot()

        self.history_reset = QPushButton("Reset History")
        self.last_event_button = QPushButton("Last Event")
        self.next_event_button = QPushButton("Next Event")
        button_layout = QGridLayout()
        button_layout.addWidget(self.history_reset, 0, 0, 0, 1)
        button_layout.addWidget(self.last_event_button, 1, 0)
        button_layout.addWidget(self.next_event_button, 1, 1)


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
        main_layout.addWidget(self.pressure_plot, 0, 1)
        main_layout.addWidget(self.slope_plot, 1, 1)
        main_layout.addWidget(self.switch_time_plot, 2, 1)
        main_layout.addLayout(button_layout, 3, 1)
        main_layout.addWidget(self.pressure_display, 0, 2)
        main_layout.addWidget(self.control_panel, 1, 2, 2, 2) # span 2 slots
        main_layout.addWidget(self.counter_display, 3, 2)

        # Add layout to dummy widget and apply to main window
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)


    # Connects widgets to backend
    def set_device(self, data_handler):
        self.data_handler = data_handler
        sample_rate = data_handler.get_sample_rate()

        # Loader
        self.loader = EventLoader()
        self.loader.read_events("logs/example.xz")
        self.last_event_button.clicked.connect(self.loader.emit_last_event)
        self.next_event_button.clicked.connect(self.loader.emit_next_event)

        # Pressurize plot
        self.pressurize_plot.set_sample_rate(sample_rate)
        data_handler.pressurize_handler.event_signal.connect(self.pressurize_plot.update_data)
        self.loader.pressurize_event_signal.connect(self.pressurize_plot.update_data)

        # Depressurize plot
        self.depressurize_plot.set_sample_rate(sample_rate)
        data_handler.depressurize_handler.event_signal.connect(self.depressurize_plot.update_data)
        self.loader.depressurize_event_signal.connect(self.depressurize_plot.update_data)

        # Period plot
        self.period_plot.set_sample_rate(sample_rate)
        data_handler.period_handler.event_signal.connect(self.period_plot.update_data)

        # Pressure plot
        data_handler.pressurize_handler.event_signal.connect(self.pressure_plot.update_data)

        # Slope plot
        self.slope_plot.set_sample_rate(sample_rate)
        data_handler.pressurize_handler.event_signal.connect(self.slope_plot.update_pressurize_data)
        data_handler.depressurize_handler.event_signal.connect(self.slope_plot.update_depressurize_data)

        # Switch time plot
        self.switch_time_plot.set_sample_rate(sample_rate)
        data_handler.pressurize_handler.event_signal.connect(self.switch_time_plot.update_pressurize_data)
        data_handler.depressurize_handler.event_signal.connect(self.switch_time_plot.update_depressurize_data)

        # Timings display
        data_handler.pressurize_handler.event_signal.connect(self.timing_display.update_widths)
        data_handler.depressurize_handler.event_signal.connect(self.timing_display.update_widths)
        data_handler.period_handler.event_signal.connect(self.timing_display.update_widths)

        # Reset button
        self.history_reset.clicked.connect(self.pressure_plot.reset_lines)
        self.history_reset.clicked.connect(self.slope_plot.reset_lines)
        self.history_reset.clicked.connect(self.switch_time_plot.reset_lines)

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
