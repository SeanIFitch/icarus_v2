from time import time
import numpy as np
from enum import Enum


class Channel(Enum):
    TARGET = 0          # Analog CH0: target pressure 
    DEPRE_LOW = 1       # Analog CH1: depressurization valve lower sensor
    DEPRE_UP = 2        # Analog CH2: depressurization valve upper sensor
    PRE_LOW = 3         # Analog CH3: pressurization valve lower sensor
    PRE_UP = 4          # Analog CH4: pressurization valve upper sensor
    HI_PRE_ORIG = 5     # Analog CH5: high pressure transducer at the origin
    HI_PRE_SAMPLE = 6   # Analog CH6: high pressure transducer at the sample
    PUMP = 7            # Digital CH0: high pressure pump (Active low / pumping on False)
    DEPRE_VALVE = 8     # Digital CH1: depressurize valve (Active low / open on False)
    PRE_VALVE = 9       # Digital CH2: pressurize valve (Active low / open on False)
    LOG = 10            # Digital CH4: log (Active low / logging on False)


# Returns a view of the selected channel
# Can be used on data that has not been wrapped in an event
def get_channel(data, channel):
    if isinstance(data, Event):
        data = data.data
    if channel.value <= 6:
        return data[:,channel.value]
    else:
        digital = 7
        bit = 1 << (channel.value - 7)
        channel_data = data[:,digital] & bit
        return channel_data.astype(np.bool_)


# Represents an event
# All methods which extract information for plotting are in this class
class Event():
    PRESSURIZE = 0
    DEPRESSURIZE = 1
    PERIOD = 2
    PRESSURE = 3
    PUMP = 4

    def __init__(self, event_type, data, event_index = None, event_time=None, data_end_time = None) -> None:
        if type(event_type) == int and event_type <=4 and event_type >=0:
            self.event_type = event_type
        else:
            raise RuntimeError(event_type + "event not supported.")

        if event_time == None:
            self.event_time = time() # float
        # Case where this is a priorly generated event being deserialized
        else:
            self.event_time = event_time

        # Required for some math
        self.event_index = event_index # index where the actual event occured uint8
        if data_end_time is None and event_index is not None:
            self.data_end_time = (len(data) - self.event_index) / 4 # time in ms from event_index to end. Assumes srate = 4000
        else:
            self.data_end_time = data_end_time

        # Period events can be long. Therefore only take 600 data points to log and plot. (same as pressurize and depressurize plots)
        # No statistical analysis of period events is necessary, so this loss of data is fine.
        if self.event_type == self.PERIOD and data_end_time is None:
            self.data = self.compress_data(data, 600)
        else:
            self.data = data # np.ndarray (?,8) np.int16


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


    # Decrease size of data. Takes every nth data point, making sure not to lose valve events.
    def compress_data(self, data, num_points):
        if len(data) <= num_points:
            return data
        else:
            step = len(data) / num_points
            indices = np.round(np.arange(0, num_points) * step).astype(int)
            compressed_data = np.copy(data[indices])

            # Recover lost valve events so they are plotted
            depressurize_indeces = np.argmin(get_channel(data, Channel.DEPRE_VALVE))
            pressurize_indeces = np.argmin(get_channel(data, Channel.PRE_VALVE))
            compressed_depressurize_indeces = np.unique((depressurize_indeces / step).astype(int))
            compressed_pressurize_indeces = np.unique((pressurize_indeces / step).astype(int))
            # Set to false with bitwise operation
            depre_mask = np.int16(0b1111111111111011)
            pre_mask = np.int16(0b1111111111110111)
            compressed_data[compressed_depressurize_indeces,7] = compressed_data[compressed_depressurize_indeces,7] & depre_mask
            compressed_data[compressed_pressurize_indeces,7] = compressed_data[compressed_pressurize_indeces,7] & pre_mask
            return compressed_data


    # Average of entire event
    def get_sample_pressure(self):
        if self.event_type != self.PRESSURE:
            raise RuntimeError("Cannot call get_sample_pressure() on event type " + self.event_type) 

        sample_pressure = np.average(get_channel(self, Channel.HI_PRE_SAMPLE))
        return sample_pressure


    # Average of entire event
    def get_target_pressure(self):
        if self.event_type != self.PRESSURE:
            raise RuntimeError("Cannot call get_target_pressure() on event type " + self.event_type) 

        target_pressure = np.average(get_channel(self, Channel.TARGET))
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
        duration = np.argmax(get_channel(self, valve)[self.event_index:])
        # Case where the end of the event is not in the reported data
        if get_channel(self, valve)[self.event_index + duration] == False:
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
        delay = np.argmin(get_channel(self, Channel.PRE_VALVE)[self.event_index:])
        return delay


    # Returns pressure before event starts
    def get_initial_sample(self):
        if self.event_type != self.DEPRESSURIZE:
            raise RuntimeError("Cannot call get_initial_sample() on event type " + self.event_type)

        sample_pressure = np.average(get_channel(self, Channel.HI_PRE_SAMPLE)[:self.event_index])
        return sample_pressure


    # Returns pressure before event starts
    def get_initial_origin(self):
        if self.event_type != self.DEPRESSURIZE:
            raise RuntimeError("Cannot call get_initial_origin() on event type " + self.event_type)

        sample_pressure = np.average(get_channel(self, Channel.HI_PRE_ORIG)[:self.event_index])
        return sample_pressure


    # Returns difference of index of half max and event_index
    def get_origin_switch_time(self):
        if self.event_type != self.DEPRESSURIZE and self.event_type != self.PRESSURIZE:
            raise RuntimeError("Cannot call get_origin_slope() on event type " + self.event_type)

        data = get_channel(self, Channel.HI_PRE_ORIG)
        minimum = np.min(data)
        data_range = np.max(data) - minimum
        half_max = minimum + (data_range / 2)
        half_max_index = np.argmin(np.abs(data - half_max))

        return half_max_index - self.event_index


    # Returns difference of index of half max and event_index
    def get_sample_switch_time(self):
        if self.event_type != self.DEPRESSURIZE and self.event_type != self.PRESSURIZE:
            raise RuntimeError("Cannot call get_origin_slope() on event type " + self.event_type)

        data = get_channel(self, Channel.HI_PRE_SAMPLE)
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

        data = get_channel(self, Channel.HI_PRE_SAMPLE)


        return np.random.randint(-5, 5)