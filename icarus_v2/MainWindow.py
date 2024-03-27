import sys
# GUI imports
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QGridLayout, QWidget, QPushButton, QLabel, QLineEdit
from PySide6.QtGui import QDoubleValidator
from EventPlot import EventPlot
from ErrorDialog import ErrorDialog
from ToggleButton import ToggleButton
# Data collection & Device imports
from Di4108USB import Di4108USB
from BufferLoader import BufferLoader
from PulseGenerator import PulseGenerator
# Event handler imports
from PressurizeHandler import PressurizeHandler
from DepressurizeHandler import DepressurizeHandler
from PeriodHandler import PeriodHandler


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

        # Initialize thread variables
        self.loader = None
        self.pressurize_handler = None
        self.depressurize_handler = None
        self.period_handler = None


    # Initializes all widgets and sets layout
    def initUI(self):
        # Window settings
        self.setWindowTitle("Icarus NMR")
        self.setMinimumSize(QSize(400, 300))

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

        # Device controls
        self.shutdown_button = QPushButton(text="Shutdown")
        self.pump_button = ToggleButton("Pump on", "Pump off")
        self.pressurize_button = ToggleButton("Pressurize open", "Pressurize close")
        self.depressurize_button = ToggleButton("Depressurize open", "Depressurize close")
        self.pulse_button = ToggleButton("Start pulsing", "Stop pulsing")

        # Timing controls
        pressurize_label = QLabel("Pressurize Width (ms):")
        depressurize_label = QLabel("Depressurize Width (ms):")
        period_label = QLabel("Period (s):")
        delay_label = QLabel("Delay (s):")
        self.pressurize_edit = QLineEdit()
        self.depressurize_edit = QLineEdit()
        self.period_edit = QLineEdit()
        self.delay_edit = QLineEdit()
        # View settings
        self.pressurize_edit.setFixedWidth(40)
        self.depressurize_edit.setFixedWidth(40)
        self.period_edit.setFixedWidth(40)
        self.delay_edit.setFixedWidth(40)
        self.pressurize_edit.setAlignment(Qt.AlignRight)
        self.depressurize_edit.setAlignment(Qt.AlignRight)
        self.period_edit.setAlignment(Qt.AlignRight)
        self.delay_edit.setAlignment(Qt.AlignRight)
        # Allow only floating-point numbers
        self.pressurize_edit.setValidator(QDoubleValidator())
        self.depressurize_edit.setValidator(QDoubleValidator())
        self.period_edit.setValidator(QDoubleValidator())
        self.delay_edit.setValidator(QDoubleValidator())

        # Counters
        self.pump_count = 0
        self.pressurize_count = 0
        self.depressurize_count = 0
        pump_count_label = QLabel("Pump Count:")
        pressurize_count_label = QLabel("Pressurize Count")
        depressurize_count_label = QLabel("Depressurize Count")
        stroke_display_label = QLabel("Pump Strokes/hr")
        self.pump_counter = QLabel("0")
        self.pressurize_counter = QLabel("0")
        self.depressurize_counter = QLabel("0")
        self.stroke_display = QLabel("0")


        # Set all layouts

        # Set layout for device control panel
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.shutdown_button)
        control_layout.addWidget(self.pump_button)
        control_layout.addWidget(self.pressurize_button)
        control_layout.addWidget(self.depressurize_button)
        control_layout.addWidget(self.pulse_button)

        # Set layout for timing control panel
        timing_layout = QGridLayout()
        timing_layout.addWidget(pressurize_label, 0, 0)
        timing_layout.addWidget(depressurize_label, 1, 0)
        timing_layout.addWidget(period_label, 2, 0)
        timing_layout.addWidget(delay_label, 3, 0)
        timing_layout.addWidget(self.pressurize_edit, 0, 1)
        timing_layout.addWidget(self.depressurize_edit, 1, 1)
        timing_layout.addWidget(self.period_edit, 2, 1)
        timing_layout.addWidget(self.delay_edit, 3, 1)

        # Set layout for counter panel
        counter_layout = QGridLayout()
        counter_layout.addWidget(pump_count_label, 0, 0)
        counter_layout.addWidget(pressurize_count_label, 1, 0)
        counter_layout.addWidget(depressurize_count_label, 2, 0)
        counter_layout.addWidget(stroke_display_label, 3, 0)
        counter_layout.addWidget(self.pump_counter, 0, 1)
        counter_layout.addWidget(self.pressurize_counter, 1, 1)
        counter_layout.addWidget(self.depressurize_counter, 2, 1)
        counter_layout.addWidget(self.stroke_display, 3, 1)

        # Set main layout
        main_layout = QGridLayout()
        main_layout.addWidget(self.pressurize_plot, 0, 0)
        main_layout.addWidget(self.depressurize_plot, 1, 0)
        main_layout.addWidget(self.period_plot, 2, 0)
        main_layout.addLayout(timing_layout, 3, 0)
        main_layout.addLayout(control_layout, 1, 1)
        main_layout.addLayout(counter_layout, 3, 1)

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
                if not self.show_error_dialog(str(e)):
                    sys.exit(0)

        # Loads data from device into buffer
        self.loader = BufferLoader(device)

        # Controls device DIO
        self.pulse_generator = PulseGenerator(device)

        # Connect widgets to handlers
        self.setup_pressurize_plot()
        self.setup_depressurize_plot()
        self.setup_period_plot()
        self.setup_controls()

        # Start threads
        self.loader.start()
        self.pressurize_handler.start()
        self.depressurize_handler.start()
        self.period_handler.start()


    # Initialize pressurize event handler and connect it to the plot
    def setup_pressurize_plot(self):
        sample_rate = self.loader.get_sample_rate()
        self.pressurize_plot.set_sample_rate(sample_rate)
        reader = self.loader.new_reader()
        self.pressurize_handler = PressurizeHandler(reader, sample_rate, self.pressure_event_display_range)
        self.pressurize_handler.event_data.connect(self.pressurize_plot.update_data)
        self.pressurize_handler.event_count.connect(self.increment_pressurize_count)


    # Initialize depressurize event handler and connect it to the plot
    def setup_depressurize_plot(self):
        sample_rate = self.loader.get_sample_rate()
        self.depressurize_plot.set_sample_rate(sample_rate)
        reader = self.loader.new_reader()
        self.depressurize_handler = DepressurizeHandler(reader, sample_rate, self.pressure_event_display_range)
        self.depressurize_handler.event_data.connect(self.depressurize_plot.update_data)
        self.depressurize_handler.event_count.connect(self.increment_depressurize_count)


    # Initialize period event handler and connect it to the plot
    def setup_period_plot(self):
        sample_rate = self.loader.get_sample_rate()
        self.period_plot.set_sample_rate(sample_rate)
        reader = self.loader.new_reader()
        self.period_handler = PeriodHandler(reader, sample_rate, self.pressure_event_display_range)
        self.period_handler.event_data.connect(self.period_plot.update_data)


    # Connects controls to appropriate functions
    def setup_controls(self):
        # Device controls
        self.shutdown_button.clicked.connect(lambda x: x)
        self.pump_button.set_check_function(self.pulse_generator.set_pump_low)
        self.pump_button.set_uncheck_function(self.pulse_generator.set_pump_high)
        self.pressurize_button.set_check_function(self.pulse_generator.set_pressurize_low)
        self.pressurize_button.set_uncheck_function(self.pulse_generator.set_pressurize_high)
        self.depressurize_button.set_check_function(self.pulse_generator.set_depressurize_low)
        self.depressurize_button.set_uncheck_function(self.pulse_generator.set_depressurize_high)
        self.pulse_button.set_check_function(self.pulse_generator.start)
        self.pulse_button.set_uncheck_function(self.pulse_generator.quit)

        # Timing controls
        self.pressurize_edit.setText(str(self.pulse_generator.pressurize_width))
        self.depressurize_edit.setText(str(self.pulse_generator.depressurize_width))
        self.period_edit.setText(str(self.pulse_generator.period_width))
        self.delay_edit.setText(str(self.pulse_generator.delay_width))
        self.pressurize_edit.textChanged.connect(self.pulse_generator.set_pressurize_width)
        self.depressurize_edit.textChanged.connect(self.pulse_generator.set_depressurize_width)
        self.period_edit.textChanged.connect(self.pulse_generator.set_period_width)
        self.delay_edit.textChanged.connect(self.pulse_generator.set_delay_width)


    def increment_pump_count(self):
        self.pump_count += 1
        self.pump_counter.setText(str(self.pump_count))


    def increment_pressurize_count(self):
        self.pressurize_count += 1
        self.pressurize_counter.setText(str(self.pressurize_count))


    def increment_depressurize_count(self):
        self.depressurize_count += 1
        self.depressurize_counter.setText(str(self.depressurize_count))


    # Opens error dialog
    def show_error_dialog(self, error_message):
        dialog = ErrorDialog(error_message, parent=self)
        return dialog.exec()


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

        if self.pulse_generator is not None:
            self.pulse_generator.quit()
            self.pulse_generator.wait()

        if self.loader is not None:
            self.loader.quit()
            self.loader.wait()


# Testing purposes
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    window.start_acquisition()
    app.exec()
