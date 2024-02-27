from enum import Enum


class Coefficients(Enum):
    CHANNEL_0 = 'target pressure'
    CHANNEL_1 = 'depressurization valve lower sensor'
    CHANNEL_2 = 'depressurization valve upper sensor'
    CHANNEL_3 = 'pressurization valve lower sensor'
    CHANNEL_4 = 'pressurization valve upper sensor'
    CHANNEL_5 = 'high pressure transducer at the origin'
    CHANNEL_6 = 'high pressure transducer at the sample'
    CHANNEL_7 = 'spare'


