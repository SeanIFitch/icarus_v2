from PySide6.QtCore import QThread
import traceback
from icarus_v2.backend.event import Event

class EventHandler(QThread):
    def __init__(self, loader, signal, sample_rate, update_rate) -> None:
        super().__init__()
        self.reader = loader.new_reader()
        self.signal = signal
        self.sample_rate = sample_rate
        self.update_rate = update_rate
        self.running = False


    # Loops to transmit data if an event occurs
    def run(self):
        self.running = True
        while self.running:
            data_to_get = int(self.sample_rate / self.update_rate)
            try:
                data, buffer_index = self.reader.read(size=data_to_get, timeout=1)
            except TimeoutError:
                self.running = False
                break
            try:
                event, chunk_index = self.detect_event(data)
            except RuntimeWarning:
                # Case where 2 events occur in same chunk
                traceback.print_exc()
                event, chunk_index = False, -1

            # buffer_index is the index that the chunk started in in the buffer
            # chunk index is the index that the event started in in that chunk
            event_index = buffer_index + chunk_index

            # If an event occurs, transmit data to plot
            if event:
                event_data, event_start = self.handle_event(event_index)
                if event_data is not None:
                    new_event = Event(self.event_type, event_data, event_start)
                    self.signal.emit(new_event)


    # Placeholder. 
    # Data: one chunk from the reader
    # Returns whether an event occurs and the index of the event
    def detect_event(self, data):
        return False, -1


    # Placeholder.
    # event_index: absolute index of event in buffer
    # Returns appropriate data and index of the event in the new data
    def handle_event(self, event_index):
        return None, -1


    # Return a range of data around the event occuring at event_index
    # Event coordinate is a tuple of the index in the buffer and in the chunk where the event occured
    def get_event_data(self, event_index):
        before, after = self.event_report_range # Amount of data in ms to report around the event

        # Calculate start and end of data to get
        sample_rate_kHz = float(self.sample_rate) / 1000
        start = event_index + int(before * sample_rate_kHz)
        end = event_index + int(after * sample_rate_kHz)

        # Case where more data was requested than is stored in the buffer
        # Safety factor of 0.9 to avoid race conditions
        if end - start > 0.9 * self.reader.buffer.capacity:
            start = int(end - 0.9 * self.reader.buffer.capacity)

        # Get data
        try:
            data = self.reader.retrieve_range(start, end, timeout=2)
        except TimeoutError:
            return None

        return data


    def quit(self):
        self.running = False
