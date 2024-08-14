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

    def __str__(self):
        if self.value == 0:
            return "Target Pressure"
        elif self.value == 1:
            return "Depressurization Valve Lower Sensor"
        elif self.value == 2:
            return "Depressurization Valve Upper Sensor"
        elif self.value == 3:
            return "Pressurization Valve Lower Sensor"
        elif self.value == 4:
            return "Pressurization Valve Upper Sensor"
        elif self.value == 5:
            return "Origin High Pressure Sensor"
        elif self.value == 6:
            return "Sample High Pressure Sensor"
        elif self.value == 7:
            return "Pump DIO"
        elif self.value == 8:
            return "Depressurization Valve DIO"
        elif self.value == 9:
            return "Pressurization Valve DIO"
        elif self.value == 10:
            return "Log DIO"


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
        if data[:,digital].dtype != np.int16:
            data = data.astype(np.int16)
        channel_data = data[:,digital] & bit
        return channel_data.astype(np.bool_)


# Used for ramp detection
def gaussian_filter(data, kernel_size, sigma=1):
    """Applies a 1D Gaussian filter to the data."""
    if kernel_size % 2 == 0 or kernel_size <= 0:
        raise ValueError("kernel_size must be a positive odd integer")

    kernel_range = np.arange(-kernel_size // 2 + 1, kernel_size // 2 + 1)
    kernel = np.exp(-kernel_range**2 / (2 * sigma**2))
    kernel /= kernel.sum()
    padded_data = np.pad(data, pad_width=kernel_size//2, mode='edge')
    return np.convolve(padded_data, kernel, mode='valid')



# Represents an event
# All methods which extract information for plotting are in this class
class Event():
    PRESSURIZE = 0
    DEPRESSURIZE = 1
    PERIOD = 2
    PRESSURE = 3
    PUMP = 4

    def __init__(self, event_type, data, event_index = None, event_time=None, step_time = None) -> None:
        if type(event_type) == int and event_type <=4 and event_type >=0:
            self.event_type = event_type
        else:
            raise RuntimeError(event_type + "event not supported.")

        if event_time == None:
            self.event_time = time()
            if data is not None:
                self.event_time -= data.shape[1] / 4000 # Assumes srate = 4000. 
            if event_index is not None:
                self.event_time += event_index / 4000
        # Case where this is a priorly generated event being deserialized
        else:
            self.event_time = event_time

        # Required for some math
        self.event_index = event_index # index where the actual event occured uint8
        if step_time is None and event_index is not None:
            self.step_time = 1 / 4 # Assumes srate = 4000. step_time is in ms.
        else:
            self.step_time = step_time

        # Period events can be long. Therefore only take 600 data points to log and plot. (same as pressurize and depressurize plots)
        # No statistical analysis of period events is necessary, so this loss of data is fine.
        # If initialized with a step time, this means the data has already been compressed.
        if self.event_type == self.PERIOD or self.event_type == self.PUMP and step_time is None:
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
            self.step_time = self.step_time * step
            indices = np.round(np.arange(0, num_points) * step).astype(int)

            compressed_data = data[indices]

            # Change where event occured
            self.event_index = np.round(self.event_index / step).astype(int)

            # Recover lost valve events so they are plotted
            depressurize_indeces = np.argmin(get_channel(data, Channel.DEPRE_VALVE))
            pressurize_indeces = np.argmin(get_channel(data, Channel.PRE_VALVE))
            compressed_depressurize_indeces = np.unique((depressurize_indeces / step).astype(int))
            compressed_pressurize_indeces = np.unique((pressurize_indeces / step).astype(int))
            # Set to false with bitwise operation
            depre_mask = np.uint16(0b1111111111111011)
            pre_mask = np.uint16(0b1111111111110111)
            compressed_data[compressed_depressurize_indeces,7] = compressed_data[compressed_depressurize_indeces,7] & depre_mask
            compressed_data[compressed_pressurize_indeces,7] = compressed_data[compressed_pressurize_indeces,7] & pre_mask
            return compressed_data


    # Average of entire event
    def get_origin_pressure(self):
        if self.event_type != self.PRESSURE:
            raise RuntimeError("Cannot call get_origin_pressure() on event type " + self.event_type) 

        sample_pressure = np.average(get_channel(self, Channel.HI_PRE_ORIG))
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

        origin_pressure = np.average(get_channel(self, Channel.HI_PRE_ORIG)[:self.event_index])
        return origin_pressure


    # Returns pressure before event starts
    def get_initial_target(self):
        if self.event_type != self.PUMP:
            raise RuntimeError("Cannot call get_initial_target() on event type " + self.event_type)

        target_pressure = np.average(get_channel(self, Channel.TARGET)[:self.event_index])
        return target_pressure


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
        return self.get_slope(Channel.HI_PRE_ORIG)


    def get_sample_slope(self):
        return self.get_slope(Channel.HI_PRE_SAMPLE)


    # Returns max slope of pressurization or depressurization
    def get_slope(self, channel):
        if self.event_type != self.DEPRESSURIZE and self.event_type != self.PRESSURIZE:
            raise RuntimeError(f"Cannot call get_slope() on event type {self.event_type}")

        y = get_channel(self, channel)

        # Calculate the first derivative of the data
        dy = np.diff(y)
        dy_smoothed = gaussian_filter(dy, 5, 5)

        if self.event_type == self.PRESSURIZE:
            slope = max(dy_smoothed)
        elif self.event_type == self.DEPRESSURIZE:
            slope = min(dy_smoothed)

        return slope
