from PySide6.QtCore import QThread, Signal
import traceback

class EventHandler(QThread):
    event_data = Signal(object)
    event_count = Signal(bool)

    def __init__(self, reader, sample_rate) -> None:
        super().__init__()
        self.reader = reader
        self.sample_rate = sample_rate
        self.running = False


    # Loops to transmit data if an event occurs
    def run(self):
        self.running = True
        while(self.running):
            data, buffer_index = self.reader.read(size=64, timeout=2)
            try:
                event, chunk_index = self.detect_event(data)
            except RuntimeWarning:
                traceback.print_exc()
                event, chunk_index = False, -1
            event_index = buffer_index + chunk_index

            # If an event occurs, transmit data to plot
            if event:
                event_data = self.handle_event(event_index)
                if event_data is not None:
                    self.event_data.emit(event_data)
                    self.event_count.emit(True)


    # Placeholder. 
    # Data: one chunk from the reader
    # Returns whether an event occurs and the index of the event
    def detect_event(self, data):
        return False, -1


    # Placeholder.
    # Event coordinate is a tuple of the index in the buffer and in the chunk where the event occured
    def handle_event(self, event_index):
        return None


    # Return a range of data around the event occuring at event_index
    # Event coordinate is a tuple of the index in the buffer and in the chunk where the event occured
    def get_event_data(self, event_index):
        before, after = self.event_report_range # Amount of data in ms to report around the event

        # Calculate start and end of data to get
        sample_rate_kHz = float(self.sample_rate) / 1000
        start = event_index + int(before * sample_rate_kHz)
        end = event_index + int(after * sample_rate_kHz)

        # Get data
        data = self.reader.retrieve_range(start, end, timeout=2)

        return data


    def quit(self):
        self.running = False
