import numpy as np
from enum import Enum
from dataclasses import dataclass, field


SAMPLE_RATE = 4000
EVENT_DATA_POINTS = 600


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

    def __str__(self) -> str:
        match self.value:
            case 0:
                return "Target Pressure"
            case 1:
                return "Depressurization Valve Lower Sensor"
            case 2:
                return "Depressurization Valve Upper Sensor"
            case 3:
                return "Pressurization Valve Lower Sensor"
            case 4:
                return "Pressurization Valve Upper Sensor"
            case 5:
                return "Origin High Pressure Sensor"
            case 6:
                return "Sample High Pressure Sensor"
            case 7:
                return "Pump DIO"
            case 8:
                return "Depressurization Valve DIO"
            case 9:
                return "Pressurization Valve DIO"
            case 10:
                return "Log DIO"
            case _:
                raise ValueError(f"Unknown value: {self.value}")


# Enum for history statistics
# TODO: remove this class
class HistStat(Enum):
    O_PRESS = "Origin Pressure"
    S_PRESS = "Sample Pressure"
    DO_SLOPE = "Origin Depressurization Slope"
    DS_SLOPE = "Sample Depressurization Slope"
    PO_SLOPE = "Origin Pressurization Slope"
    PS_SLOPE = "Sample Pressurization Slope"
    DO_SWITCH = "Origin Depressurization Switch Time"
    DS_SWITCH = "Sample Depressurization Switch Time"
    PO_SWITCH = "Origin Pressurization Switch Time"
    PS_SWITCH = "Sample Pressurization Switch Time"

    def __str__(self) -> str:
        return self.value


# Returns a view of the selected channel
# Can be used on data that has not been wrapped in an event
def get_channel(data: "DataEvent" | np.ndarray, channel: Channel) -> np.ndarray:
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
def gaussian_filter(data: np.ndarray, kernel_size: int, sigma: int=1) -> np.ndarray:
    """Applies a 1D Gaussian filter to the data."""
    if kernel_size % 2 == 0 or kernel_size <= 0:
        raise ValueError("kernel_size must be a positive odd integer")

    kernel_range = np.arange(-kernel_size // 2 + 1, kernel_size // 2 + 1)
    kernel = np.exp(-kernel_range**2 / (2 * sigma**2))
    kernel /= kernel.sum()
    padded_data = np.pad(data, pad_width=kernel_size//2, mode='edge')
    return np.convolve(padded_data, kernel, mode='valid')


@dataclass
class Event:
    timestamp: float


@dataclass
class DataEvent(Event):
    """
    Subclass of event for events which must keep the underlying data
    """
    data: np.ndarray
    event_index: int
    data_step_ms: float = 1000 / SAMPLE_RATE


@dataclass
class ValveEvent(DataEvent):
    @property
    def origin_switch_time(self) -> float:
        data = get_channel(self, Channel.HI_PRE_ORIG)
        return self.get_switch_time(data)

    @property
    def sample_switch_time(self) -> float:
        data = get_channel(self, Channel.HI_PRE_SAMPLE)
        return self.get_switch_time(data)

    @property
    def origin_slope(self) -> float:
        data = get_channel(self, Channel.HI_PRE_ORIG)
        return self.get_slope(data)

    @property
    def sample_slope(self) -> float:
        data = get_channel(self, Channel.HI_PRE_SAMPLE)
        return self.get_slope(data)

    # Returns difference of index of half max and event_index
    def get_switch_time(self, data: np.ndarray) -> float:
        minimum = np.min(data)
        data_range = np.max(data) - minimum
        half_max = minimum + (data_range / 2)
        half_max_index = np.argmin(np.abs(data - half_max))

        return half_max_index - self.event_index

    # Returns max slope of pressurization or depressurization
    @staticmethod
    def get_slope(data: np.ndarray) -> float:
        # Calculate the first derivative of the data
        dy = np.diff(data)
        dy_smoothed = gaussian_filter(dy, 5, 5)
        max_index = np.argmax(np.abs(dy_smoothed))[0]

        return dy_smoothed[max_index]


@dataclass
class Pressurize(ValveEvent):
    pass


@dataclass
class Depressurize(ValveEvent):
    sample: np.floating = field(init=False)
    origin: np.floating = field(init=False)
    target: np.floating = field(init=False)

    def __post_init__(self) -> None:
        self.sample = np.mean(get_channel(self, Channel.HI_PRE_SAMPLE)[:self.event_index])
        self.origin = np.mean(get_channel(self, Channel.HI_PRE_ORIG)[:self.event_index])
        self.target = np.mean(get_channel(self, Channel.TARGET)[:self.event_index])


@dataclass
class Period(DataEvent):
    def __post_init__(self) -> None:
        self._compress_data(EVENT_DATA_POINTS)

    # Decrease size of data. Takes every nth data point, making sure not to lose valve events.
    def _compress_data(self, num_points: int) -> None:
        if len(self.data) <= num_points:
            return
        else:
            step = len(self.data) / num_points
            self.data_step_ms = 1000 / SAMPLE_RATE * step
            indices = np.round(np.arange(0, num_points) * step).astype(int)

            compressed_data = self.data[indices]

            # Change where event occurred
            self.event_index = np.round(self.event_index / step).astype(int)

            # Recover lost valve events so they are plotted
            depressurize_indices = np.where(get_channel(self, Channel.DEPRE_VALVE) == np.min(get_channel(self, Channel.DEPRE_VALVE)))[0]
            pressurize_indices = np.where(get_channel(self, Channel.PRE_VALVE) == np.min(get_channel(self, Channel.PRE_VALVE)))[0]
            compressed_depressurize_indices = np.unique((depressurize_indices / step).astype(int))
            compressed_pressurize_indices = np.unique((pressurize_indices / step).astype(int))
            # Set to false with bitwise operation
            depre_mask = np.uint16(0b1111111111111101)
            pre_mask = np.uint16(0b1111111111111011)
            compressed_data[compressed_depressurize_indices,7] = compressed_data[compressed_depressurize_indices,7] & depre_mask
            compressed_data[compressed_pressurize_indices,7] = compressed_data[compressed_pressurize_indices,7] & pre_mask

            self.data = compressed_data


@dataclass
class Pressure(Event):
    origin: float
    sample: float
    target: float

    @classmethod
    def from_data(cls, data: np.ndarray) -> "Pressure":
         origin = np.average(get_channel(data, Channel.HI_PRE_ORIG))
         sample = np.average(get_channel(data, Channel.HI_PRE_SAMPLE))
         target = np.average(get_channel(data, Channel.TARGET))
         return cls(origin, sample, target)


@dataclass
class Pump(Event):
    pass


@dataclass
class DIO(Event):
    pressurize: bool
    depressurize: bool
    pump: bool
    log: bool


@dataclass
class SampleSensor(Event):
    connected: bool
