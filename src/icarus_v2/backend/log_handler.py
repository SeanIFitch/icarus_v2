from icarus_v2.backend.event_handler import EventHandler
import numpy as np
from icarus_v2.backend.event import Channel, get_channel


# Detects log bit change event and transmits to logger
class LogHandler(EventHandler):
    def __init__(self, loader, signal, sample_rate, update_rate) -> None:
        super().__init__(loader, signal, sample_rate, update_rate)
        self.last_log_bit = None # variable to keep track of edges of data chunks in case an event lines up with the start of a chunk


    # Overridden because this should be able to handle multiple events in one chunk whereas the base class cannot
    def run(self):
        self.running = True
        while(self.running):
            data_to_get = int(self.sample_rate / self.update_rate)
            try:
                data, buffer_index = self.reader.read(size=data_to_get, timeout=1)
            except TimeoutError:
                self.running = False
                self.last_log_bit = None
                break

            # use XOR with offset array to find indeces where there is a state change
            log_data = get_channel(data, Channel.LOG)

            # Start of data stream always starts a log file
            if self.last_log_bit is None:
                self.signal.emit(log_data[0])
                self.last_log_bit = log_data[0]

            log_offset = np.insert(log_data, 0, self.last_log_bit)[:-1]

            # Find indeces where there is a state change
            # np.where returns a tuple, so take the first element
            changes = np.where(log_offset ^ log_data)[0]

            for index in changes:
                self.signal.emit(log_data[index])

            self.last_log_bit = log_data[-1]


    # Setting last_log_bit ensures that a new log file is started when device is reconnected
    def quit(self):
        self.running = False
        self.last_log_bit = None
