import lzma
import pickle
import os
from datetime import datetime
from PySide6.QtCore import QStandardPaths


# Logs files to logs/temp or logs/experiment depending on bit 4.
# Files are deleted if no events are logged.
class Logger:
    def __init__(self, config_manager=None) -> None:
        self.config_manager = config_manager
        self.file = None
        self.filename = None
        self.current_path = None
        self.event_count = None

    def new_log_file(self, temporary=True, raw=False):
        self.close()

        self.current_path = temporary
        base_dir = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation), 'logs')
        if raw:
            log_path = os.path.join(base_dir, "example")
        elif temporary:
            log_path = os.path.join(base_dir, 'temp')
        else:
            log_path = os.path.join(base_dir, "experiment")

        if not os.path.exists(log_path):
            os.makedirs(log_path)

        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = f"{log_path}/log_{current_datetime}.xz"
        self.file = lzma.open(self.filename, "ab")  # Opening file in append binary mode with LZMA compression
        self.event_count = 0

    def log_event(self, event):
        event_dict = {
            'event_type': event.event_type,
            'data': event.data,
            'event_time': event.event_time,
            'event_index': event.event_index,
            'step_time': event.step_time
        }   
        self.log_raw(event_dict)

    def log_raw(self, data):
        self.event_count += 1
        pickle.dump(data, self.file, protocol=pickle.HIGHEST_PROTOCOL)

    def flush(self):
        self.file.close()
        self.file = lzma.open(self.filename, "ab")

    def close(self):
        if self.file is not None:
            if self.config_manager is not None:
                settings = {"plotting_coefficients": self.config_manager.get_settings("plotting_coefficients")}
                pickle.dump(settings, self.file, protocol=pickle.HIGHEST_PROTOCOL)
            self.file.close()
            self.file = None
            if self.event_count == 0:
                try:
                    os.remove(self.filename)
                except FileNotFoundError:
                    pass

            self.filename = None
