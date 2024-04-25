from enum import Enum
import numpy as np


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
def get_channel(data, channel):
    if channel.value <= 6:
        return data[:,channel.value]
    else:
        digital = 7
        bit = 1 << (channel.value - 7)
        channel_data = data[:,digital] & bit
        return channel_data.astype(np.bool_)
