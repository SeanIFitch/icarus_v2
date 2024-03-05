from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PressurizeEventPlot import PressurizeEventPlot
from DepressurizeEventPlot import DepressurizeEventPlot
from PressureHandler import PressureHandler
from BufferLoader import BufferLoader
from ErrorDialog import ErrorDialog
import sys

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        # Initialize variables
        self.loader = None
        self.pressure_event_display_range = (-10,140) # How much data to view around pressurize events
        self.pressurize_handler = None
        self.pressurize_plot = None
        self.depressurize_handler = None
        self.depressurize_plot = None

        # Window settings
        self.setWindowTitle("Icarus NMR")
        self.setMinimumSize(QSize(400, 300))

        # Pressure event plots
        self.pressurize_plot = PressurizeEventPlot(display_range=self.pressure_event_display_range)
        self.depressurize_plot = DepressurizeEventPlot(display_range=self.pressure_event_display_range)

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.pressurize_plot)
        layout.addWidget(self.depressurize_plot)

        # Add layout to dummy widget and apply to main window
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


    def start_acquisition(self):
        # Continually try to connect to usb device
        while True:
            try:
                self.loader = BufferLoader()
                break  # Break out of the loop if acquisition is successful
            except Exception as e:
                if not self.show_error_dialog(str(e)):
                    sys.exit(0)

        # Connect widgets to handlers
        self.setup_pressurize_plot()
        self.setup_depressurize_plot()

        # Start threads
        self.loader.start()
        self.pressurize_handler.start()
        self.depressurize_handler.start()


    # Initialize pressurize event handler and connect it to the plot
    def setup_pressurize_plot(self):
        sample_rate = self.loader.get_sample_rate()
        self.pressurize_plot.set_sample_rate(sample_rate)
        dig_reader = self.loader.new_digital_reader()
        ana_reader = self.loader.new_analog_reader()
        self.pressurize_handler = PressureHandler(dig_reader, ana_reader, sample_rate, self.pressure_event_display_range)
        self.pressurize_handler.event_occurred.connect(self.pressurize_plot.update_data)


    # Initialize depressurize event handler and connect it to the plot
    def setup_depressurize_plot(self):
        sample_rate = self.loader.get_sample_rate()
        self.depressurize_plot.set_sample_rate(sample_rate)
        dig_reader = self.loader.new_digital_reader()
        ana_reader = self.loader.new_analog_reader()
        self.depressurize_handler = PressureHandler(dig_reader, ana_reader, sample_rate, self.pressure_event_display_range)
        self.depressurize_handler.event_occurred.connect(self.depressurize_plot.update_data)


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
