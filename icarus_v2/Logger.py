import lzma
import pickle
from datetime import datetime


class Logger:
    def __init__(self, path="logs"):
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{path}/log_{current_datetime}.xz"
        self.file = lzma.open(filename, "ab")  # Opening file in append binary mode with LZMA compression


    def log_event(self, event):
        event_dict = {
            'event_type': event.event_type,
            'data': event.data,
            'event_time': event.event_time,
            'event_index': event.event_index,
            'step_time': event.step_time
        }
        pickle.dump(event_dict, self.file, protocol=pickle.HIGHEST_PROTOCOL)


    def log_raw_data(self, data):
        pickle.dump(data, self.file, protocol=pickle.HIGHEST_PROTOCOL)


    def close(self):
        self.file.close()
