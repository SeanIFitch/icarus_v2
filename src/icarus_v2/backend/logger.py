import lzma
import pickle
import os
from datetime import datetime
from PySide6.QtCore import QStandardPaths
from icarus_v2.backend.configuration_manager import ConfigurationManager


MAX_PRESSURE_INTERVAL = 5


# Logs files to logs/temp or logs/experiment depending on bit 4.
# Files are deleted if no events are logged.
class Logger:
    def __init__(self, is_raw=False) -> None:
        self.file = None
        self.filename = None
        self.current_path = None
        self.event_count = None
        self.last_pressure_update = None
        self.is_raw = is_raw

    def new_log_file(self, temporary=True):
        self.close()

        self.current_path = temporary
        base_dir = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'logs')
        if temporary:
            log_path = os.path.join(base_dir, 'temp')
        else:
            log_path = os.path.join(base_dir, "experiment")

        if not os.path.exists(log_path):
            os.makedirs(log_path)

        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        name = f"{'raw_' if self.is_raw else ''}log_{current_datetime}.xz"
        self.filename = os.path.join(log_path, name)
        self.file = lzma.open(self.filename, "ab")  # Opening file in append binary mode with LZMA compression
        self.event_count = 0
        self.last_pressure_update = None

    def log_event(self, event):
        if self.is_raw:
            raise RuntimeError("Error: Adding a processed event to a raw log.")

        if event.event_type == event.PRESSURE:
            if self.last_pressure_update is None or event.event_time - self.last_pressure_update < MAX_PRESSURE_INTERVAL:
                return

        if event.event_type == event.PRESSURE or event.event_type == event.DEPRESSURIZE:
            self.last_pressure_update = event.event_time

        event_dict = {
            'event_type': event.event_type,
            'data': event.data,
            'event_time': event.event_time,
            'event_index': event.event_index,
            'step_time': event.step_time
        }   
        self.log_raw(event_dict)

    def log_error(self, event):
        return

        #Should take in an instance of either sentry_error or sentry_warning
        if self.is_raw:
            raise RuntimeError("Error: Adding a processed error to a raw log.")

        event_dict = {
            'class_type' : type(event),     #This serves as a flag so that when the log is read it will know if it is a warning or error
            'error_type' : event.error_type,
            'event_time': event.time,
            'data': event.info
        }   

        self.log_raw(event_dict)

    def log_raw(self, data):
        self.event_count += 1
        pickle.dump(data, self.file, protocol=pickle.HIGHEST_PROTOCOL)

    def flush(self):
        self.file.close()
        self.file = lzma.open(self.filename, "ab")

    def close(self):
        if self.file is None:
            return

        if not self.is_raw:
            config_manager = ConfigurationManager()
            settings = {"plotting_coefficients": config_manager.get_settings("plotting_coefficients")}
            pickle.dump(settings, self.file, protocol=pickle.HIGHEST_PROTOCOL)

        self.file.close()
        self.file = None

        if self.event_count == 0:
            try:
                os.remove(self.filename)
            except FileNotFoundError:
                pass

        self.filename = None
