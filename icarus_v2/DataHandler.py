# General utility imports
from Logger import Logger
from PySide6.QtCore import Signal, QThread
from time import sleep
# Data collection & Device imports
from Di4108USB import Di4108USB
from BufferLoader import BufferLoader
from PulseGenerator import PulseGenerator
from Event import Event
# Event handler imports
from PressurizeHandler import PressurizeHandler
from DepressurizeHandler import DepressurizeHandler
from PeriodHandler import PeriodHandler
from PressureHandler import PressureHandler


# Define the DataHandler class
class DataHandler(QThread):
    pressurize_event_signal = Signal(Event)
    depressurize_event_signal = Signal(Event)
    period_event_signal = Signal(Event)
    pressure_event_signal = Signal(Event)
    update_counts_signal = Signal(dict)
    acquisition_started_signal = Signal(bool)
    display_error = Signal(str)


    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.pulse_generator = PulseGenerator(self.config_manager)
        self.connecting = False
        self.device = None
        self.logger = None
        self.loader = None
        self.pressurize_handler = None
        self.depressurize_handler = None
        self.period_handler = None
        self.pressure_handler = None


    # Connect to a device
    def run(self):
        self.connecting = True
        while self.connecting:
            try:
                self.device = Di4108USB()
                self.connecting = False
            except:
                sleep(0.1)
        if self.device is not None:
            self.start_data_collection()
            # Start event loop so that signals sent to this thread may be processed
            self.exec()


    def start_data_collection(self):
        # Loads data from device into buffer
        self.loader = BufferLoader(self.device)

        # Controls device DIO
        self.pulse_generator.set_device(self.device)

        # Event handlers
        sample_rate = 4000
        event_update_hz = 30
        pressure_update_hz = 3
        event_display_bounds = (-10,140)
        self.pressurize_handler = PressurizeHandler(self.loader, self.pressurize_event_signal, sample_rate, event_update_hz, event_display_bounds)
        self.depressurize_handler = DepressurizeHandler(self.loader, self.depressurize_event_signal, sample_rate, event_update_hz, event_display_bounds)
        self.period_handler = PeriodHandler(self.loader, self.period_event_signal, sample_rate, event_update_hz, event_display_bounds)
        self.pressure_handler = PressureHandler(self.loader, self.pressure_event_signal, sample_rate, pressure_update_hz)

        # Logger
        '''self.logger = Logger()
        self.pressurize_event_signal.connect(self.logger.log_event)
        self.depressurize_event_signal.connect(self.logger.log_event)
        self.period_event_signal.connect(self.logger.log_event)'''

        # Start threads
        self.loader.start()
        self.pressurize_handler.start()
        self.depressurize_handler.start()
        self.period_handler.start()
        self.pressure_handler.start()

        self.acquisition_started_signal.emit(True)


    def quit(self):
        self.connecting = False

        if self.logger is not None:
            self.logger.close()

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
            self.pressure_handler.quit()
            self.pressure_handler.wait()

        if self.pulse_generator is not None:
            self.pulse_generator.quit()
            self.pulse_generator.wait()

        if self.loader is not None:
            self.loader.quit()
            self.loader.wait()

        super().quit()
