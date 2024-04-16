from EventHandler import EventHandler
from PySide6.QtCore import Signal
import numpy as np


# Sends pressure data constantly. Events always occur.
class PressureHandler(EventHandler):
    sample_pressure = Signal(float)
    target_pressure = Signal(float)


    def __init__(self, reader, sample_rate, update_rate) -> None:
        super().__init__(reader, sample_rate, update_rate)


    # Data: one chunk from the reader
    # Returns whether an event occurs and the index of the event
    def detect_event(self, data):
        self.event_report_range = (0, len(data['target']))
        return True, 0


    # Returns data to graph
    def handle_event(self, event_index):
        data = self.get_event_data(event_index)
        return data


    # Responsible for emitting to all pertinent signals.
    def emit_data(self, event_data):
        target_pressure = np.average(event_data['target'])
        sample_pressure = np.average(event_data['hi_pre_orig'])

        self.target_pressure.emit(target_pressure)
        self.sample_pressure.emit(sample_pressure)
