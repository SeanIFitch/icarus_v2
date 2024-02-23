from PySide6.QtCore import QThread, Signal
import random
import numpy as np

class DataHandler(QThread):
    event_occurred = Signal(np.ndarray)

    def __init__(self, buffer_reader, sample_rate, event_report_range) -> None:
        super().__init__()
        self.buffer_reader = buffer_reader
        self.sample_rate = sample_rate
        self.running = False
        self.event_report_range = event_report_range # tuple of number of ms before and after an event to report

    # Placeholder. Returns whether 
    def detect_event(self, data):
        if random.random() > 0.95:
            event = True
            index = random.randint(0,len(data) - 1)
        else:
            event = False
            index = -1

        return event, index


    # Loops to transmit data if an event occurs
    def run(self):
        self.running = True
        while(self.running):
            data, buffer_index = self.buffer_reader.read(timeout=2)
            event, chunk_index = self.detect_event(data)

            # If an event occurs, transmit data to plot
            if event:
                chunk_size = len(data)
                event_data = self.event_data(buffer_index, chunk_index, chunk_size)
                self.event_occurred.emit(event_data)


    # Return a range of data around the event
    # buffer_index is the index of the buffer where the event occured
    # chunk_index is the index of that array where the event occured
    # chunk_size is the size of a chunk in the buffer
    def event_data(self, buffer_index, chunk_index, chunk_size):
        # Amount of data in ms to report around the event
        before, after = self.event_report_range

        # Calculate chunk number of chunks before and after to get
        sample_rate_kHz = float(self.sample_rate) / 1000
        points_before = int(before * sample_rate_kHz)
        points_after = int(after * sample_rate_kHz)
        chunks_before = int(np.ceil(max(0.0, float(points_before - chunk_index)) / chunk_size))
        chunks_after = int(np.ceil(max(0.0, float(points_after - (chunk_size - chunk_index - 1))) / chunk_size))

        # Get data
        data_list = self.buffer_reader.retrieve_range(buffer_index - chunks_before, buffer_index + chunks_after, timeout=2)
        # Select proper points
        data = np.concatenate(data_list)
        origin = chunk_size * chunks_before + chunk_index
        return data[origin - points_before:origin + points_after]


    def quit(self):
        self.running = False
