from PySide6.QtCore import QThread, Signal
import numpy as np

class EventHandler(QThread):
    event_occurred = Signal(np.ndarray)

    def __init__(self, buffer_reader, sample_rate) -> None:
        super().__init__()
        self.buffer_reader = buffer_reader
        self.sample_rate = sample_rate
        self.running = False


    # Loops to transmit data if an event occurs
    def run(self):
        self.running = True
        while(self.running):
            data, buffer_index = self.buffer_reader.read(timeout=2)
            event, chunk_index = self.detect_event(data)

            # If an event occurs, transmit data to plot
            if event:
                chunk_size = len(data)
                event_data = self.handle_event((buffer_index, chunk_index), chunk_size)
                self.event_occurred.emit(event_data)


    # Placeholder. 
    # Data: one chunk from the reader
    # Returns whether an event occurs and the index of the event
    def detect_event(self, data):
        return False, -1


    # Placeholder.
    # Event coordinate is a tuple of the index in the buffer and in the chunk where the event occured
    # chunk_size is the size of a chunk in the buffer
    def handle_event(self, event_coordinate, chunk_size):
        return None


    def quit(self):
        self.running = False
