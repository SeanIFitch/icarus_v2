from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow
from PressureEventPlot import PressureEventPlot
from DataHandler import DataHandler
from BufferLoader import BufferLoader


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        # Initialize variables
        self.pressure_event_display_range = (-10,140)
        self.loader = None
        self.sample_rate = None
        self.pressurize_handler = None

        # Window settings
        self.setWindowTitle("Icarus NMR")
        self.setMinimumSize(QSize(400, 300))

        # Pressurize plot
        self.pressurize_plot = PressureEventPlot(title="Pressurize", display_range=self.pressure_event_display_range)
        self.setCentralWidget(self.pressurize_plot)

        self.start_acquisition()


    def start_acquisition(self):
        self.loader = BufferLoader()
        self.sample_rate = self.loader.get_sample_rate()

        # Set up pressurize handler and connect to pressurize plot
        self.pressurize_plot.set_sample_rate(self.sample_rate)
        dig1 = self.loader.new_digital_reader()
        self.pressurize_handler = DataHandler(dig1, self.sample_rate, self.pressure_event_display_range)
        self.pressurize_handler.event_occurred.connect(self.pressurize_plot.update_data)

        # Start threads
        self.loader.start()
        self.pressurize_handler.start()


    def closeEvent(self, event):
        # Cleanup QThreads
        if self.pressurize_handler is not None:
            self.pressurize_handler.quit()
            self.pressurize_handler.wait()

        if self.loader is not None:
            self.loader.quit()
            self.loader.wait()

        super().closeEvent(event)



# Testing purposes
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
