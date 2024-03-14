from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
import sys

from PressurizeEventPlot import PressurizeEventPlot
from DepressurizeEventPlot import DepressurizeEventPlot
from PressurizeHandler import PressurizeHandler
from DepressurizeHandler import DepressurizeHandler
from BufferLoader import BufferLoader
from ErrorDialog import ErrorDialog
from Di4108USB import Di4108USB
from PulseGenerator import PulseGenerator


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

        # Initialize thread variables
        self.loader = None
        self.pressurize_handler = None
        self.depressurize_handler = None


    # Initializes all widgets and sets layout
    def initUI(self):
        # Window settings
        self.setWindowTitle("Icarus NMR")
        self.setMinimumSize(QSize(400, 300))

        # Initialize all widgets

        # Pressure event plots
        self.pressure_event_display_range = (-10,140) # How much data to view around pressurize events
        self.pressurize_plot = PressurizeEventPlot(display_range=self.pressure_event_display_range)
        self.depressurize_plot = DepressurizeEventPlot(display_range=self.pressure_event_display_range)

        # Controls
        self.shutdown_button = QPushButton(text="Shutdown")
        self.pump_button = QPushButton(text="Pump")
        self.pressurize_button = QPushButton(text="Pressurize")
        self.depressurize_button = QPushButton(text="Depressurize")

        # Set all layouts

        # Set layout for event plots
        event_layout = QVBoxLayout()
        event_layout.addWidget(self.pressurize_plot)
        event_layout.addWidget(self.depressurize_plot)

        # Set layout for control panel
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.shutdown_button)
        control_layout.addWidget(self.pump_button)
        control_layout.addWidget(self.pressurize_button)
        control_layout.addWidget(self.depressurize_button)

        # Set main layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(event_layout)
        main_layout.addLayout(control_layout)

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
        self.setup_controls()

        # Start threads
        self.loader.start()
        self.pressurize_handler.start()
        self.depressurize_handler.start()


    # Initialize pressurize event handler and connect it to the plot
    def setup_pressurize_plot(self):
        sample_rate = self.loader.get_sample_rate()
        self.pressurize_plot.set_sample_rate(sample_rate)
        reader = self.loader.new_reader()
        self.pressurize_handler = PressurizeHandler(reader, sample_rate, self.pressure_event_display_range)
        self.pressurize_handler.event_occurred.connect(self.pressurize_plot.update_data)


    # Initialize depressurize event handler and connect it to the plot
    def setup_depressurize_plot(self):
        sample_rate = self.loader.get_sample_rate()
        self.depressurize_plot.set_sample_rate(sample_rate)
        reader = self.loader.new_reader()
        self.depressurize_handler = DepressurizeHandler(reader, sample_rate, self.pressure_event_display_range)
        self.depressurize_handler.event_occurred.connect(self.depressurize_plot.update_data)


    def setup_controls(self):
        def dummy():
            pass
        self.shutdown_button.clicked.connect(dummy)
        self.pump_button.clicked.connect(dummy)
        self.pressurize_button.clicked.connect(self.pulse_generator.pressurize)
        self.depressurize_button.clicked.connect(self.pulse_generator.depressurize)


    # Opens error dialog
    def show_error_dialog(self, error_message):
        dialog = ErrorDialog(error_message, parent=self)
        return dialog.exec()


    def closeEvent(self, event):
        # Cleanup QThreads
        if self.pressurize_handler is not None:
            self.pressurize_handler.quit()
            self.pressurize_handler.wait()

        if self.depressurize_handler is not None:
            self.depressurize_handler.quit()
            self.depressurize_handler.wait()

        if self.loader is not None:
            self.loader.quit()
            self.loader.wait()

        super().closeEvent(event)



# Testing purposes
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    window.start_acquisition()
    app.exec()
