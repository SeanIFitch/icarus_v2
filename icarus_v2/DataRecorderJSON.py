import json
from datetime import datetime
import os
import numpy as np

class DataRecorder:
    def __init__(self, log_dir="logs/"):
        self.log_dir = log_dir
        self.log_file = None
        self.create_log_dir()

    def create_log_dir(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def create_log_file(self):
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_name = f"{current_time}_log.json"
        self.log_file = self.log_dir + log_file_name

    def log_event(self, event):
        if not self.log_file:
            self.create_log_file()

        event_data = {
            "event_type": event.event_type,
            "event_time": datetime.fromtimestamp(event.event_time).strftime("%Y-%m-%d %H:%M:%S"),
            "event_index": event.event_index
        }

        # Convert device readings to dictionary
        device_readings_dict = {}
        for field in event.data.dtype.names:
            if event.data[field].dtype == np.bool_:
                device_readings_dict[field] = bool(event.data[field][event.event_index])
            else:
                device_readings_dict[field] = float(event.data[field][event.event_index])
        event_data["device_readings"] = device_readings_dict

        with open(self.log_file, 'a') as f:
            json.dump(event_data, f)
            f.write('\n')
