from icarus_v2.backend.event_handler import EventHandler
import numpy as np
from icarus_v2.backend.event import Event, Channel, get_channel


# Detects a pressurize event and transmits data to plot
class PressurizeHandler(EventHandler):
    def __init__(self, loader, signal, sample_rate, update_rate, event_report_range) -> None:
        super().__init__(loader, signal, sample_rate, update_rate)
        self.event_report_range = event_report_range # tuple of range of ms around an event to report e.g. (-10,140)
        self.last_pressurize_bit = None # variable to keep track of edges of data chunks in case an event lines up with the start of a chunk
        self.event_type = Event.PRESSURIZE


    # Data: one chunk from the reader
    # Returns whether an event occurs and the index of the event
    def detect_event(self, data):
        pre_valve = get_channel(data, Channel.PRE_VALVE)
        # valve array with prior value inserted and last value popped
        valve_offset = np.insert(pre_valve, 0, self.last_pressurize_bit)[:-1]

        # Find indeces where there is a low bit preceeded by a high bit
        # np.where returns a tuple, so take the first element
        low_indeces = np.where(valve_offset & ~pre_valve)[0]

        # All values are high. No event.
        if len(low_indeces) == 0:
            event = False
            index = -1

        # Event occured
        else:
            event = True
            index = low_indeces[0]

            # Raise warning if 2 low pulses detected in same chunk. Under default settings this will never happen unless 2 pulses are made within 16ms of each other
            if len(low_indeces) > 1:
                raise RuntimeWarning("Pressurize event dropped. Two events occured in same data chunk.")

        self.last_pressurize_bit = pre_valve[-1]
        return event, index


    # Returns data to graph
    def handle_event(self, event_index):
        data = self.get_event_data(event_index)

        before, after = self.event_report_range
        sample_rate_kHz = float(self.sample_rate) / 1000
        event_index = int( - before * sample_rate_kHz)

        return data, event_index
