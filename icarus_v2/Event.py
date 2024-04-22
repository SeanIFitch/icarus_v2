from time import time
import numpy as np

# Represents an event
class Event():
    def __init__(self, event_type, data, event_index) -> None:
        assert (event_type == "pressurize" 
            or event_type == "depressurize" 
            or event_type == "period" 
            or event_type == "pressure" 
            or event_type == "pump"
        )

        self.event_type = event_type
        self.data = data
        self.event_time = time()

        # Required for some math
        self.event_index = event_index # index where the actual event occured


    def get_sample_pressure(self):
        if self.event_type != 'pressure':
            raise RuntimeError("Cannot call get_sample_pressure() on event type " + self.event_type) 

        sample_pressure = np.average(self.data['hi_pre_orig'])
        return sample_pressure


    def get_target_pressure(self):
        if self.event_type != 'pressure':
            raise RuntimeError("Cannot call get_target_pressure() on event type " + self.event_type) 

        target_pressure = np.average(self.data['target'])
        return target_pressure


    # Returns time valve was open in terms of indeces, so divide result by device sample rate for time
    def get_valve_open_time(self):
        if self.event_type == 'pressurize':
            valve = 'pre_valve'
        elif self.event_type == 'depressurize':
            valve = 'depre_valve'
        else:
            raise RuntimeError("Cannot call get_valve_open_time() on event type " + self.event_type)

        # find duration of event
        duration = np.argmax(self.data[valve][self.event_index:])
        # Case where the end of the event is not in the reported data
        if self.data[valve][self.event_index + duration] == False:
            duration = len(self.data) - self.event_index
        return duration


    # Returns period duration in terms of indeces, so divide result by device sample rate for time
    def get_period_width(self):
        assert self.event_type == 'period'

        # There is a buffer of equivalent size on either end of the data
        width = len(self.data) - 2 * self.event_index
        return width


    # Returns delay duration in terms of indeces, so divide result by device sample rate for time
    def get_delay_width(self):
        assert self.event_type == 'period'

        # Find length of delay
        delay = np.argmin(self.data['pre_valve'][self.event_index:])
        return delay
