import sys
# GUI imports
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGridLayout,
    QWidget,
    QDialogButtonBox,
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
from ErrorDialog import open_error_dialog
# Data collection & Device imports
from Di4108USB import Di4108USB
from BufferLoader import BufferLoader
from PulseGenerator import PulseGenerator
# Event handler imports
from PressurizeHandler import PressurizeHandler
from DepressurizeHandler import DepressurizeHandler
from PeriodHandler import PeriodHandler
from PressureHandler import PressureHandler


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

        # Initialize thread variables
        self.loader = None
        self.pressurize_handler = None
        self.depressurize_handler = None
        self.period_handler = None
        self.pressure_handler = None


    # Initializes all widgets and sets layout
    def initUI(self):
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

        # Device control panel
        self.control_panel = ControlPanel()

        # Info displays
        self.counter_panel = CounterDisplay()
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
        main_layout.addWidget(self.history_reset, 3, 1)
        main_layout.addWidget(self.pressure_display, 0, 2)
        main_layout.addWidget(self.control_panel, 1, 2)
        main_layout.addWidget(self.counter_panel, 3, 2)

        # Add layout to dummy widget and apply to main window
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)


    # Connects to the USB device, connects all widgets to handlers, starts acquiring data
    def start_acquisition(self):
        # Continually try to connect to usb device
        while True:
            try:
                device = Di4108USB()
                break  # Break out of the loop if acquisition is successful
            except Exception as e:
                # Open error dialog
                if not open_error_dialog(e, QDialogButtonBox.Retry | QDialogButtonBox.Cancel, self):
                    # Quit if cancel is selected
                    sys.exit(0)

        # Loads data from device into buffer
        self.loader = BufferLoader(device)

        # Controls device DIO
        self.pulse_generator = PulseGenerator(device)

        # Connect widgets to backend
        self.setup_widgets()
        self.init_event_handlers()

        # Start threads
        self.loader.start()
        self.pressurize_handler.start()
        self.depressurize_handler.start()
        self.period_handler.start()
        self.pressure_handler.start()


    # Widget setup after backend is initialized
    def setup_widgets(self):
        sample_rate = self.loader.get_sample_rate()

        # plots
        self.pressurize_plot.set_sample_rate(sample_rate)
        self.depressurize_plot.set_sample_rate(sample_rate)
        self.period_plot.set_sample_rate(sample_rate)
        self.switch_time_plot.set_sample_rate(sample_rate)
        self.slope_plot.set_sample_rate(sample_rate)

        self.history_reset.clicked.connect(self.pressure_plot.reset_lines)
        self.history_reset.clicked.connect(self.slope_plot.reset_lines)
        self.history_reset.clicked.connect(self.switch_time_plot.reset_lines)

        # Control panel
        self.control_panel.set_pulse_generator(self.pulse_generator)


    # Initialize event handlers and connect to widgets
    def init_event_handlers(self):
        sample_rate = self.loader.get_sample_rate()
        event_update_rate = 30

        # Pressurize handler
        reader = self.loader.new_reader()
        self.pressurize_handler = PressurizeHandler(reader, sample_rate, event_update_rate, self.pressure_event_display_range)
        self.pressurize_handler.event_data.connect(self.pressurize_plot.update_data)
        self.pressurize_handler.event_data.connect(self.pressure_plot.update_data)
        self.pressurize_handler.event_data.connect(self.switch_time_plot.update_pressurize_data)
        self.pressurize_handler.event_data.connect(self.slope_plot.update_pressurize_data)
        self.pressurize_handler.event_count_increment.connect(self.counter_panel.increment_pressurize_count)
        self.pressurize_handler.event_width.connect(self.timing_display.update_pressurize_width)

        # Depressurize handler
        reader = self.loader.new_reader()
        self.depressurize_handler = DepressurizeHandler(reader, sample_rate, event_update_rate, self.pressure_event_display_range)
        self.depressurize_handler.event_data.connect(self.depressurize_plot.update_data)
        self.depressurize_handler.event_data.connect(self.switch_time_plot.update_depressurize_data)
        self.depressurize_handler.event_data.connect(self.slope_plot.update_depressurize_data)
        self.depressurize_handler.event_count_increment.connect(self.counter_panel.increment_depressurize_count)
        self.depressurize_handler.event_width.connect(self.timing_display.update_depressurize_width)

        # Period handler
        reader = self.loader.new_reader()
        self.period_handler = PeriodHandler(reader, sample_rate, event_update_rate, self.pressure_event_display_range)
        self.period_handler.event_data.connect(self.period_plot.update_data)
        self.period_handler.event_width.connect(self.timing_display.update_period_width)
        self.period_handler.delay_width.connect(self.timing_display.update_delay_width)

        # Pressure handler
        pressure_update_rate = 2
        reader = self.loader.new_reader()
        self.pressure_handler = PressureHandler(reader, sample_rate, pressure_update_rate)
        self.pressure_handler.target_pressure.connect(self.pressure_display.update_target_pressure)
        self.pressure_handler.sample_pressure.connect(self.pressure_display.update_sample_pressure)


    # Runs on quitting the application
    def closeEvent(self, event):
        super().closeEvent(event)

        # Cleanup QThreads
        if self.pressurize_handler is not None:
            self.pressurize_handler.quit()
            self.pressurize_handler.wait()

        if self.depressurize_handler is not None:
            self.depressurize_handler.quit()
            self.depressurize_handler.wait()

        if self.period_handler is not None:
            self.period_handler.quit()
            self.period_handler.wait()

        if self.pressure_handler is not None:
            self.loader.quit()
            self.loader.wait()

        if self.pulse_generator is not None:
            self.pulse_generator.quit()
            self.pulse_generator.wait()

        if self.loader is not None:
            self.loader.quit()
            self.loader.wait()


# Run application
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    window.start_acquisition()
    app.exec()
