# General utility imports
from icarus_v2.backend.logger import Logger
from PySide6.QtCore import Signal, QThread
from time import sleep
from threading import Lock
from icarus_v2.utils.udev_setup import setup_udev_rules
from icarus_v2.utils.raw_log_reader import RawLogReader
import os
# Data collection & Device imports
from icarus_v2.backend.dataq_interface import DataqInterface
from icarus_v2.backend.buffer_loader import BufferLoader
from icarus_v2.backend.pulse_generator import PulseGenerator
from icarus_v2.backend.event import Event
# Event handler imports
from icarus_v2.backend.pressurize_handler import PressurizeHandler
from icarus_v2.backend.depressurize_handler import DepressurizeHandler
from icarus_v2.backend.period_handler import PeriodHandler
from icarus_v2.backend.pressure_handler import PressureHandler
from icarus_v2.backend.pump_handler import PumpHandler
from icarus_v2.backend.log_handler import LogHandler
from icarus_v2.backend.sentry import Sentry
from icarus_v2.backend.sample_sensor_detector import SampleSensorDetector


# Define the DataHandler class
class DataHandler(QThread):
    # Send events to gui
    pressurize_event_signal = Signal(Event)
    depressurize_event_signal = Signal(Event)
    period_event_signal = Signal(Event)
    pressure_event_signal = Signal(Event)
    pump_event_signal = Signal(Event)
    # Tell gui when device is connected
    acquiring_signal = Signal(bool)
    # display error dialog
    display_error = Signal(str)
    # Show warning or error in toolbar
    toolbar_warning = Signal(str)
    # Signal to tell device control panel to shut down
    # Ideally this is unnecessary as the signal should be directly sent to the pulse_generator
    # But currently the control panel can not check the state of the device. This is a workaround.
    shutdown_signal = Signal()
    # Start new log file
    log_signal = Signal(bool)
    # Tell GUI whether the sample sensor is connected
    sample_sensor_connected = Signal(bool)

    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.pulse_generator = PulseGenerator(self.config_manager)
        self.connecting = False
        self.connected = False
        self.device = None
        self.logger = None

        # TESTING ONLY!!!. reads a raw data file instead of connecting to a device
        self.load_raw = False
        if self.load_raw:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.raw_file = os.path.join(project_root, 'logs', 'raw', "2.1_to_1.5kBar.xz")

        # Loads data from device into buffer
        self.loader = BufferLoader()
        self.loader.device_disconnected.connect(self.device_disconnected)

        # Event handlers
        sample_rate = 4000
        event_update_hz = 30
        pressure_update_hz = 5
        event_display_bounds = (-10, 140)
        self.pressurize_handler = PressurizeHandler(
            self.loader,
            self.pressurize_event_signal,
            sample_rate,
            event_update_hz,
            event_display_bounds
        )
        self.depressurize_handler = DepressurizeHandler(
            self.loader,
            self.depressurize_event_signal,
            sample_rate,
            event_update_hz,
            event_display_bounds
        )
        self.period_handler = PeriodHandler(
            self.loader,
            self.period_event_signal,
            sample_rate,
            event_update_hz,
            event_display_bounds
        )
        self.pressure_handler = PressureHandler(
            self.loader,
            self.pressure_event_signal,
            sample_rate,
            pressure_update_hz)
        self.pump_handler = PumpHandler(self.loader, self.pump_event_signal, sample_rate)
        self.log_handler = LogHandler(self.loader, self.log_signal, sample_rate, pressure_update_hz)

        # Logger
        if not self.load_raw:
            self.logger = Logger(self.config_manager)
            self.pressurize_event_signal.connect(self.logger.log_event)
            self.depressurize_event_signal.connect(self.logger.log_event)
            self.period_event_signal.connect(self.logger.log_event)
            self.log_signal.connect(self.logger.new_log_file)

        # Sentry
        self.sentry = Sentry(config_manager)
        self.log_signal.connect(self.sentry.handle_experiment)
        self.pump_event_signal.connect(self.sentry.handle_pump)
        self.depressurize_event_signal.connect(self.sentry.handle_depressurize)
        self.sentry.warning_signal.connect(lambda x: self.toolbar_warning.emit(x))
        self.sentry.error_signal.connect(lambda x: self.toolbar_warning.emit(x))
        self.sentry.error_signal.connect(lambda x: self.display_error.emit(x))
        self.sentry.error_signal.connect(lambda x: self.shutdown_signal.emit())

        # Sample sensor detector
        self.sample_sensor_detector = SampleSensorDetector(self.config_manager, self.sample_sensor_connected)
        self.depressurize_event_signal.connect(self.sample_sensor_detector.detect)

        # Prevents another thread from quitting this while it is initializing the device.
        # Without this, the cleanup code would run and then the QThreads would be initialized.
        self.quit_lock = Lock()

        self.acquiring_signal.emit(False)

    # Connect to a device
    def run(self):
        self.connecting = True
        self.quit_lock.acquire()
        udev_installed = False

        while self.connecting:

            # TESTING ONLY
            if self.load_raw:
                self.device = RawLogReader(self.raw_file)
                self.connecting = False
                self.connected = True
                break

            try:
                self.device = DataqInterface()
                self.connecting = False
                self.connected = True
            except Exception as e:
                # Continue connecting
                if (
                        "USB device not found" in str(e) or
                        "No such device (it may have been disconnected)" in str(e) or
                        "Operation timed out" in str(e) or
                        "Input/Output Error" in str(e) or
                        "No backend available" in str(e)
                        ):
                    self.quit_lock.release()
                    sleep(0.5)
                    if not self.connecting:
                        return
                    self.quit_lock.acquire()
                elif "Insufficient permissions to access the USB device" in str(e):
                    try:
                        if not udev_installed:
                            setup_udev_rules()
                            udev_installed = True
                        sleep(1)
                    except Exception as err:
                        self.display_error.emit(str(err))
                        break
                else:
                    self.display_error.emit(str(e))
                    break

        if self.device is not None:
            self.loader.set_device(self.device)
            self.pulse_generator.set_device(self.device)

            self.pressurize_handler.start()
            self.depressurize_handler.start()
            self.period_handler.start()
            self.pressure_handler.start()
            self.pump_handler.start()
            self.log_handler.start()
            self.loader.start()

            self.acquiring_signal.emit(True)

        self.quit_lock.release()

        # Start event loop so that signals sent to this thread may be processed
        self.exec()

    def device_disconnected(self):
        self.connected = False
        self.quit()

        # Reset persistent states
        self.pressurize_handler.last_pressurize_bit = None
        self.depressurize_handler.last_depressurize_bit = None
        self.period_handler.last_depressurize_bit = None
        self.period_handler.last_depressurize_event = None
        self.log_handler.last_log_bit = None
        self.sample_sensor_detector.last_result = True
        self.pump_handler.reset()
        self.sentry.reset()

        # Try to reconnect to device
        self.start()

    def quit(self):
        self.connecting = False
        acquired = self.quit_lock.acquire(timeout=10)

        if self.logger is not None:
            self.logger.close()

        self.acquiring_signal.emit(False)
        # Cleanup QThreads
        self.pressurize_handler.quit()
        self.depressurize_handler.quit()
        self.period_handler.quit()
        self.pressure_handler.quit()
        self.pump_handler.quit()
        self.log_handler.quit()
        self.pulse_generator.quit()
        self.loader.quit()

        self.pressurize_handler.wait()
        self.depressurize_handler.wait()
        self.period_handler.wait()
        self.pressure_handler.wait()
        self.pump_handler.wait()
        self.log_handler.wait()
        self.pulse_generator.wait()
        self.loader.wait()

        if self.connected:
            self.pulse_generator.set_pressurize_low()
            self.pulse_generator.set_depressurize_low()
            sleep(1)
            self.pulse_generator.set_pressurize_high()
            self.pulse_generator.set_depressurize_high()

        super().quit()
        self.wait()
        if acquired:
            self.quit_lock.release()
