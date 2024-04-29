import lzma
import pickle
import os
from datetime import datetime


class Logger:
    def __init__(self, path="logs"):
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{path}/log_{current_datetime}.xz"
        self.file = lzma.open(filename, "ab")  # Opening file in append binary mode with LZMA compression
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


    def close(self):
        self.file.close()
        if self.event_count == 0:
            os.remove(self.filename)
