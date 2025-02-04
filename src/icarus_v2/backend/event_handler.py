from PySide6.QtCore import QThread
import traceback
from icarus_v2.backend.event import Event

class EventHandler(QThread):


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
