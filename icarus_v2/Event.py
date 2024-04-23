from time import time
import numpy as np

# Represents an event
class Event():
    PRESSURIZE = 0
    DEPRESSURIZE = 1
    PERIOD = 2
    PRESSURE = 3
    PUMP = 4

    def __init__(self, event_type, data, event_index, event_time=None) -> None:
        if event_type == 'pressurize' or event_type == self.PRESSURIZE:
            self.event_type = self.PRESSURIZE
        elif event_type == 'depressurize' or event_type == self.DEPRESSURIZE:
            self.event_type = self.DEPRESSURIZE
        elif event_type == 'period' or event_type == self.PERIOD:
            self.event_type = self.PERIOD
        elif event_type == 'pressure' or event_type == self.PRESSURE:
            self.event_type = self.PRESSURE
        elif event_type == 'pump' or event_type == self.PUMP:
            self.event_type = self.PUMP
        else:
            raise RuntimeError(event_type + "event not supported.")

        self.data = data # np.ndarray(?, device_readings)
        if event_time == None:
            self.event_time = time() # float
        else:
            self.event_time = event_time

        # Required for some math
        self.event_index = event_index # index where the actual event occured uint8


    def get_event_type(self):
        if self.event_type == self.PRESSURIZE:
            return 'pressurize'
        elif self.event_type == self.DEPRESSURIZE:
            return 'depressurize'
        elif self.event_type == self.PERIOD:
            return 'period'
        elif self.event_type == self.PRESSURE:
            return 'pressure'
        elif self.event_type == self.PUMP:
            return 'pump'


    def get_sample_pressure(self):
        if self.event_type != self.PRESSURE:
            raise RuntimeError("Cannot call get_sample_pressure() on event type " + self.event_type) 

        sample_pressure = np.average(self.data['hi_pre_orig'])
        return sample_pressure


    def get_target_pressure(self):
        if self.event_type != self.PRESSURE:
            raise RuntimeError("Cannot call get_target_pressure() on event type " + self.event_type) 

        target_pressure = np.average(self.data['target'])
        return target_pressure


    # Returns time valve was open in terms of indeces, so divide result by device sample rate for time
    def get_valve_open_time(self):
        if self.event_type == self.PRESSURIZE:
            valve = 'pre_valve'
        elif self.event_type == self.DEPRESSURIZE:
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
        if self.event_type != self.PERIOD:
            raise RuntimeError("Cannot call get_period_width() on event type " + self.event_type) 

        # There is a buffer of equivalent size on either end of the data
        width = len(self.data) - 2 * self.event_index
        return width


    # Returns delay duration in terms of indeces, so divide result by device sample rate for time
    def get_delay_width(self):
        if self.event_type != self.PERIOD:
            raise RuntimeError("Cannot call get_delay_width() on event type " + self.event_type) 

        # Find length of delay
        delay = np.argmin(self.data['pre_valve'][self.event_index:])
        return delay
