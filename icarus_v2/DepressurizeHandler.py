from EventHandler import EventHandler
from PySide6.QtCore import Signal
import numpy as np


# Detects a depressurize event and transmits data to plot
class DepressurizeHandler(EventHandler):
    event_data = Signal(np.ndarray)
    event_count_increment = Signal(bool)
    event_width = Signal(float)


    def __init__(self, reader, sample_rate, update_rate, event_report_range) -> None:
        super().__init__(reader, sample_rate, update_rate)
        self.event_report_range = event_report_range # tuple of range of ms around an event to report e.g. (-10,140)
        self.last_depressurize_bit = None # variable to keep track of edges of data chunks in case an event lines up with the start of a chunk


    # Data: one chunk from the reader
    # Returns whether an event occurs and the index of the event
    def detect_event(self, data):
        depre_valve = data['depre_valve']
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

            # Raise warning if 2 low pulses detected in same chunk. Under default settings this will never happen unless 2 pulses are made within 33ms of each other
            if len(low_indeces) > 1:
                raise RuntimeError("Depressurize event dropped. Two events occured in same data chunk.")

        self.last_depressurize_bit = depre_valve[-1]
        return event, index


    # Returns data to graph
    def handle_event(self, event_index):
        data = self.get_event_data(event_index)
        return data


    # Responsible for emitting to all pertinent signals.
    def emit_data(self, event_data):
        self.event_data.emit(event_data)
        self.event_count_increment.emit(True)

        # find duration of event
        ms_before, ms_after = self.event_report_range
        sample_rate_kHz = float(self.sample_rate) / 1000
        event_index =  - int(ms_before * sample_rate_kHz)
        event_duration = np.argmax(event_data['depre_valve'][event_index:])
        duration_ms = float(event_duration) / sample_rate_kHz
        # Case where the end of the event is not in the reported data
        if event_data['depre_valve'][event_index + event_duration] == False:
            duration_ms = ms_after
        self.event_width.emit(duration_ms)
