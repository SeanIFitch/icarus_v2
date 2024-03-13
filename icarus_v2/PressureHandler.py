from EventHandler import EventHandler
import numpy as np
import random


# Detects a pressurize or depressurize event and transmits data to plot
class PressureHandler(EventHandler):
    def __init__(self, reader, sample_rate, event_report_range) -> None:
        super().__init__(reader, sample_rate)
        self.event_report_range = event_report_range # tuple of range of ms around an event to report e.g. (-10,140)


    # Placeholder. 
    # Data: one chunk from the reader
    # Returns whether an event occurs and the index of the event
    def detect_event(self, data):
        if random.random() > 0.99:
            event = True
            index = random.randint(0,len(data) - 1)
        else:
            event = False
            index = -1

        return event, index


    # Returns data to graph
    def handle_event(self, event_index):
        data = self.event_data(event_index)
        return data

