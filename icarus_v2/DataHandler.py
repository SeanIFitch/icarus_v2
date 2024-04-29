# General utility imports
from Logger import Logger
from PySide6.QtCore import Signal, QThread
from time import sleep
from threading import Lock
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
    acquiring_signal = Signal(bool)
    display_error = Signal(str)


    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.pulse_generator = PulseGenerator(self.config_manager)
        self.connecting = False
        self.device = None
        self.logger = None

        # Loads data from device into buffer
        self.loader = BufferLoader()
        self.loader.device_disconnected.connect(self.device_disconnected)

        # Event handlers
        sample_rate = 4000
        event_update_hz = 30
        pressure_update_hz = 3
        event_display_bounds = (-10,140)
        self.pressurize_handler = PressurizeHandler(self.loader, self.pressurize_event_signal, sample_rate, event_update_hz, event_display_bounds)
        self.depressurize_handler = DepressurizeHandler(self.loader, self.depressurize_event_signal, sample_rate, event_update_hz, event_display_bounds)
        self.period_handler = PeriodHandler(self.loader, self.period_event_signal, sample_rate, event_update_hz, event_display_bounds)
        self.pressure_handler = PressureHandler(self.loader, self.pressure_event_signal, sample_rate, pressure_update_hz)

        # Start threads


        # Prevents another thread from quitting this while it is initializing the device.
        # Without this, the cleanup code would run and then the QThreads would be initialized.
        self.quit_lock = Lock()

        self.acquiring_signal.emit(False)


    # Connect to a device
    def run(self):
        print("Run")
        self.connecting = True
        self.quit_lock.acquire(timeout=1)
        while self.connecting:
            try:
                self.device = Di4108USB()
                self.connecting = False
            except:
                self.quit_lock.release()
                sleep(0.1)
                self.quit_lock.acquire(timeout=1)

        if self.device is not None:
            self.loader.set_device(self.device)
            self.pulse_generator.set_device(self.device)

            self.pressurize_handler.start()
            self.depressurize_handler.start()
            self.period_handler.start()
            self.pressure_handler.start()
            self.loader.start()

            self.acquiring_signal.emit(True)

        self.quit_lock.release()

        # Start event loop so that signals sent to this thread may be processed
        self.exec()

        '''# Logger
        self.logger = Logger()
        self.pressurize_event_signal.connect(self.logger.log_event)
        self.depressurize_event_signal.connect(self.logger.log_event)
        self.period_event_signal.connect(self.logger.log_event)'''


    def device_disconnected(self):
        self.quit()

        # Try to reconnect to device
        self.start()


    def quit(self):
        self.connecting = False
        self.quit_lock.acquire(timeout=10)

        if self.logger is not None:
            self.logger.close()

        self.acquiring_signal.emit(False)
        # Cleanup QThreads
        self.pressurize_handler.quit()
        self.depressurize_handler.quit()
        self.period_handler.quit()
        self.pressure_handler.quit()
        self.pulse_generator.quit()
        self.loader.quit()

        self.pressurize_handler.wait()
        self.depressurize_handler.wait()
        self.period_handler.wait()
        self.pressure_handler.wait()
        self.pulse_generator.wait()
        self.loader.wait()

        super().quit()
        self.wait()
        self.quit_lock.release()
