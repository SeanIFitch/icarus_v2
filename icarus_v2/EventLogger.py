import lzma
import pickle
from datetime import datetime


class EventLogger:
    def __init__(self):
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"logs/log_{current_datetime}.xz"
        self.file = lzma.open(filename, "ab")  # Opening file in append binary mode with LZMA compression


    def log_event(self, event):
        event_dict = {
            'event_type': event.event_type,
            'data': event.data,
            'event_time': event.event_time,
            'event_index': event.event_index
        }
        # Serialize event data using pickle with a higher protocol for efficiency
        pickle.dump(event_dict, self.file, protocol=pickle.HIGHEST_PROTOCOL)


    def close(self):
        self.file.close()
