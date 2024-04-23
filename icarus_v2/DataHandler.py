# General utility imports
from EventLogger import EventLogger
import json
from PySide6.QtCore import Signal
# Data collection & Device imports
from Di4108USB import Di4108USB
from BufferLoader import BufferLoader
from PulseGenerator import PulseGenerator
from Counter import Counter
# Event handler imports
from PressurizeHandler import PressurizeHandler
from DepressurizeHandler import DepressurizeHandler
from PeriodHandler import PeriodHandler
from PressureHandler import PressureHandler

# Define the DataHandler class
class DataHandler:
    display_error = Signal(str)

    def __init__(self, settings_filename):
        # Load application settings
        self.settings_filename = settings_filename
        with open(self.settings_filename, "r") as file:
            self.settings = json.load(file)

        # Try to connect to usb device
        try:
            device = Di4108USB()
        except Exception as e:
            # Open error dialog
            self.display_error.emit(e)
            return False

        # Loads data from device into buffer
        self.loader = BufferLoader(device)

        # Controls device DIO
        self.pulse_generator = PulseGenerator(device, self.settings["timing_settings"])

        # Event handlers
        sample_rate = self.get_sample_rate()
        event_update_hz = 30
        pressure_update_hz = 2
        event_display_bounds = (-10,140)
        self.pressurize_handler = PressurizeHandler(self.loader, sample_rate, event_update_hz, event_display_bounds)
        self.depressurize_handler = DepressurizeHandler(self.loader, sample_rate, event_update_hz, event_display_bounds)
        self.period_handler = PeriodHandler(self.loader, sample_rate, event_update_hz, event_display_bounds)
        self.pressure_handler = PressureHandler(self.loader, sample_rate, pressure_update_hz)

        # Logger
        self.logger = EventLogger()
        self.pressurize_handler.event_signal.connect(self.logger.log_event)
        self.depressurize_handler.event_signal.connect(self.logger.log_event)

        # Keeps track of event counts
        self.counter = Counter(self.settings["counter_settings"])
        self.counter.save_settings.connect(self.save_settings)
        self.pressurize_handler.event_signal.connect(self.counter.increment_count)
        self.depressurize_handler.event_signal.connect(self.counter.increment_count)

        # Start threads
        self.loader.start()
        self.pressurize_handler.start()
        self.depressurize_handler.start()
        self.period_handler.start()
        self.pressure_handler.start()


    def get_sample_rate(self):
        return self.loader.get_sample_rate()


    # Save timing and counter settings to settings file
    def save_settings(self):
        settings = {
            "counter_settings": self.counter.counts,
            "timing_settings": self.pulse_generator.settings
        }

        with open(self.settings_filename, "w") as write_file:
            json.dump(settings, write_file, indent=4)


    # Run on quitting data collection
    def quit(self):
        self.save_settings()

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
