from icarus_v2.backend.event_handler import EventHandler
import numpy as np
from icarus_v2.backend.event import Event, Channel, get_channel


# Detects a period event and transmits data to plot
class PeriodHandler(EventHandler):
    def __init__(self, loader, signal, sample_rate, update_rate, event_report_range) -> None:
        super().__init__(loader, signal, sample_rate, update_rate)
        self.event_report_range = event_report_range # tuple of range of ms around an event to report e.g. (-10,140)
        self.last_depressurize_bit = None # variable to keep track of edges of data chunks in case an event lines up with the start of a chunk
        self.last_depressurize_event = None # variable to keep track of index of last depressurize event
        self.event_type = Event.PERIOD


    # Data: one chunk from the reader
    # Returns whether a depressurize event occurs and the index of the event
    # This logic is the same as for DepressurizeHandler
    def detect_event(self, data):
        depre_valve = get_channel(data, Channel.DEPRE_VALVE)
        # valve array with prior value inserted and last value popped
        valve_offset = np.insert(depre_valve, 0, self.last_depressurize_bit)[:-1]

        # Find indeces where there is a low bit preceeded by a high bit
        # np.where returns a tuple, so take the first element
        low_indeces = np.where(valve_offset & ~depre_valve)[0]

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
                raise RuntimeError("Depressurize event dropped on period handler. Two events occured in same data chunk.")

        self.last_depressurize_bit = depre_valve[-1]
        return event, index


    # Returns data to graph. 
    # Always returns from the last event since a period must wait for the second event to get the duration.
    def handle_event(self, event_index):
        # No prior depressurize events
        if self.last_depressurize_event is None:
            data = None
            current_event_idx = None

        else:
            # Update event_report_range based on period length and amount of data displayed before a period
            before, current_after = self.event_report_range
            sample_rate_kHz = float(self.sample_rate) / 1000
            period_duration = float(event_index - self.last_depressurize_event) / sample_rate_kHz # in milliseconds
            after = period_duration - before
            self.event_report_range = (before, after)

            # Get data from last event based on new event_report_range
            data = self.get_event_data(self.last_depressurize_event)
            current_event_idx = int( - before * sample_rate_kHz)

        # Record event index
        self.last_depressurize_event = event_index
        # Return data to plot
        return data, current_event_idx
