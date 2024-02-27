from EventHandler import EventHandler
import numpy as np
import random


# Detects a pressurize or depressurize event and transmits data to plot
class PressureHandler(EventHandler):
    def __init__(self, digital_reader, analog_viewer, sample_rate, event_report_range) -> None:
        super().__init__(digital_reader, sample_rate)
        self.event_report_range = event_report_range # tuple of range of ms around an event to report
        self.analog_viewer = analog_viewer


    # Placeholder. 
    # Data: one chunk from the reader
    # Returns whether an event occurs and the index of the event
    def detect_event(self, data):
        if random.random() > 0.95:
            event = True
            index = random.randint(0,len(data) - 1)
        else:
            event = False
            index = -1

        return event, index


    # Returns data to graph
    def handle_event(self, event_coordinate, chunk_size):
        return self.event_data(event_coordinate, chunk_size, self.analog_viewer)


    # Return a range of data around the event
    # Event coordinate is a tuple of the index in the buffer and in the chunk where the event occured
    # chunk_size is the size of a chunk in the buffer
    def event_data(self, event_coordinate, chunk_size, viewer):
        before, after = self.event_report_range # Amount of data in ms to report around the event
        before *= -1
        buffer_i, chunk_i = event_coordinate

        # Calculate number of chunks to get around event
        sample_rate_kHz = float(self.sample_rate) / 1000
        points_before = int(before * sample_rate_kHz)
        points_after = int(after * sample_rate_kHz)
        chunks_before = int(np.ceil(max(0.0, float(points_before - chunk_i)) / chunk_size))
        chunks_after = int(np.ceil(max(0.0, float(points_after - (chunk_size - chunk_i))) / chunk_size))

        # Get data
        start = buffer_i - chunks_before
        end = buffer_i + chunks_after + 1
        data_list = viewer.retrieve_range(start, end, timeout=2)
        # Select proper points
        data = np.concatenate(data_list)
        origin = (chunk_size * chunks_before) + chunk_i

        return data[origin - points_before:origin + points_after]
