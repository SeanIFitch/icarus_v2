import lzma
import pickle
import os
from datetime import datetime


# Logs files to logs/temp or logs/experiment depending on bit 4.
# Files are deleted if no events are logged.
class Logger:
    def __init__(self) -> None:
        self.file = None
        self.filename = None
        self.current_path = None


    def new_log_file(self, temporary = True):
        self.close()

        self.current_path = temporary

        path = "logs/temp" if temporary else "logs/experiment"
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.makedirs(path)

        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = f"{path}/log_{current_datetime}.xz"
        self.file = lzma.open(self.filename, "ab")  # Opening file in append binary mode with LZMA compression
        self.event_count = 0


    def log_event(self, event):
        self.event_count += 1
        event_dict = {
            'event_type': event.event_type,
            'data': event.data,
            'event_time': event.event_time,
            'event_index': event.event_index,
            'step_time': event.step_time
        }   
        pickle.dump(event_dict, self.file, protocol=pickle.HIGHEST_PROTOCOL)


    def flush(self):
        self.file.close()
        self.file = lzma.open(self.filename, "ab")


    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
            if self.event_count == 0:
                os.remove(self.filename)
            self.filename = None
