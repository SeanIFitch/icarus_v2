from EventHandler import EventHandler
from PySide6.QtCore import Signal
import numpy as np


# Sends pressure data constantly. Events always occur.
class PressureHandler(EventHandler):
    sample_pressure = Signal(float)
    target_pressure = Signal(float)


    def __init__(self, reader, sample_rate, update_rate) -> None:
        super().__init__(reader, sample_rate, update_rate)


    # Responsible for emitting to all pertinent signals.
    def emit_data(self, event_data):
        target_pressure = np.average(event_data['target'])
        sample_pressure = np.average(event_data['hi_pre_orig'])

        self.target_pressure.emit(target_pressure)
        self.sample_pressure.emit(sample_pressure)


    # Loops to transmit data if an event occurs
    # Overridden because events always occur for this handler and all data is used
    def run(self):
        self.running = True
        while(self.running):
            data_to_get = int(self.sample_rate / self.update_rate)
            data, buffer_index = self.reader.read(size=data_to_get, timeout=2)

            # Transmit data to plot
            self.emit_data(data)
