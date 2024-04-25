from time import time
import numpy as np
from Channel import Channel, get_channel


# Represents an event
# All methods which extract information for plotting are in this class
class Event():
    PRESSURIZE = 0
    DEPRESSURIZE = 1
    PERIOD = 2
    PRESSURE = 3
    PUMP = 4

    def __init__(self, event_type, data, event_index, event_time=None) -> None:
        if type(event_type) == int and event_type <=4 and event_type >=0:
            self.event_type = event_type
        else:
            raise RuntimeError(event_type + "event not supported.")

        self.data = data # np.ndarray (?,8) np.int16

        if event_time == None:
            self.event_time = time() # float
        else:
            self.event_time = event_time

        # Required for some math
        self.event_index = event_index # index where the actual event occured uint8


    # used to call all info functions
    def get_event_info(self, info_type):
        if info_type == "origin pressure":
            return self.get_initial_origin()
        elif info_type == "sample pressure":
            return self.get_initial_sample()
        elif info_type == "depress origin slope":
            return self.get_origin_slope()
        elif info_type == "depress sample slope":
            return self.get_sample_slope()
        elif info_type == "press origin slope":
            return self.get_origin_slope()
        elif info_type == "press sample slope":
            return self.get_sample_slope()
        elif info_type == "depress origin switch":
            return self.get_origin_switch_time()
        elif info_type == "depress sample switch":
            return self.get_sample_switch_time()
        elif info_type == "press origin switch":
            return self.get_origin_switch_time()
        elif info_type == "press sample switch":
            return self.get_sample_switch_time()


    # Average of entire event
    def get_sample_pressure(self):
        if self.event_type != self.PRESSURE:
            raise RuntimeError("Cannot call get_sample_pressure() on event type " + self.event_type) 

        sample_pressure = np.average(get_channel(self.data, Channel.HI_PRE_SAMPLE))
        return sample_pressure


    # Average of entire event
    def get_target_pressure(self):
        if self.event_type != self.PRESSURE:
            raise RuntimeError("Cannot call get_target_pressure() on event type " + self.event_type) 

        target_pressure = np.average(get_channel(self.data, Channel.TARGET))
        return target_pressure


    # Returns time valve was open in terms of indeces, so divide result by device sample rate for time
    def get_valve_open_time(self):
        if self.event_type == self.PRESSURIZE:
            valve = Channel.PRE_VALVE
        elif self.event_type == self.DEPRESSURIZE:
            valve = Channel.DEPRE_VALVE
        else:
            raise RuntimeError("Cannot call get_valve_open_time() on event type " + self.event_type)

        # find duration of event
        duration = np.argmax(get_channel(self.data, valve)[self.event_index:])
        # Case where the end of the event is not in the reported data
        if get_channel(self.data, valve)[self.event_index + duration] == False:
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
        delay = np.argmin(get_channel(self.data, Channel.PRE_VALVE)[self.event_index:])
        return delay


    # Returns pressure before event starts
    def get_initial_sample(self):
        if self.event_type != self.DEPRESSURIZE:
            raise RuntimeError("Cannot call get_initial_sample() on event type " + self.event_type)

        sample_pressure = np.average(get_channel(self.data, Channel.HI_PRE_SAMPLE)[:self.event_index])
        return sample_pressure


    # Returns pressure before event starts
    def get_initial_origin(self):
        if self.event_type != self.DEPRESSURIZE:
            raise RuntimeError("Cannot call get_initial_origin() on event type " + self.event_type)

        sample_pressure = np.average(get_channel(self.data, Channel.HI_PRE_ORIG)[:self.event_index])
        return sample_pressure


    # Returns difference of index of half max and event_index
    def get_origin_switch_time(self):
        if self.event_type != self.DEPRESSURIZE and self.event_type != self.PRESSURIZE:
            raise RuntimeError("Cannot call get_origin_slope() on event type " + self.event_type)

        data = get_channel(self.data, Channel.HI_PRE_ORIG)
        minimum = np.min(data)
        data_range = np.max(data) - minimum
        half_max = minimum + (data_range / 2)
        half_max_index = np.argmin(np.abs(data - half_max))

        return half_max_index - self.event_index


    # Returns difference of index of half max and event_index
    def get_sample_switch_time(self):
        if self.event_type != self.DEPRESSURIZE and self.event_type != self.PRESSURIZE:
            raise RuntimeError("Cannot call get_origin_slope() on event type " + self.event_type)

        data = get_channel(self.data, Channel.HI_PRE_SAMPLE)
        minimum = np.min(data)
        data_range = np.max(data) - minimum
        half_max = minimum + (data_range / 2)
        half_max_index = np.argmin(np.abs(data - half_max))

        return half_max_index - self.event_index


    def get_origin_slope(self):
        if self.event_type != self.DEPRESSURIZE and self.event_type != self.PRESSURIZE:
            raise RuntimeError("Cannot call get_origin_slope() on event type " + self.event_type)

        return np.random.randint(-5, 5)

    def get_sample_slope(self):
        if self.event_type != self.DEPRESSURIZE and self.event_type != self.PRESSURIZE:
            raise RuntimeError("Cannot call get_sample_slope() on event type " + self.event_type)

        return np.random.randint(-5, 5)