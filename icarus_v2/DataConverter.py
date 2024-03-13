import numpy as np

# ANALOG
# CH0: target pressure 
# CH1: depressurization valve lower sensor
# CH2: depressurization valve upper sensor
# CH3: pressurization valve lower sensor
# CH4: pressurization valve upper sensor
# CH5: high pressure transducer at the origin
# CH6: high pressure transducer at the sample
# CH7: spare

# DIGITAL
# CH0: high pressure pump
# CH1: depressurize valve
# CH2: pressurize valve
# CH3: spare
# CH4: log
# CH5: spare
# CH6: spare

#convert integer values on the sensor to psi
TARGET_COEFF = (1/1.33)*(1/150)*79600.0*200*2.0**-15 #target pressure
LOW_PRESSURE_COEFF = (1/50)*200*2.0**-15 #depressurization valve lower sensor
HIGH_PRESSURE_COEFF = 2*50000*2.0**-15 #high pressure transducer at the origin

ANALOG_COEFFS = np.asarray([TARGET_COEFF, LOW_PRESSURE_COEFF, LOW_PRESSURE_COEFF, 
                            LOW_PRESSURE_COEFF, LOW_PRESSURE_COEFF, HIGH_PRESSURE_COEFF, 
                            HIGH_PRESSURE_COEFF, None])

USER_UNITS = {'kbar': 6.894756709891046e-05, 'atm': 1/14.696, 'psi': 1}

#readings for pressure sensors at atmospheric pressure
PRESSURE_SENSOR_OFFSET = np.asarray([69.5595, 65.562, 68.881375, 84.2195, 86.96075, 17.248, 17.322, None])


# data: 2d np array of analog data
# Returns: 2d np array of floats
def convert_to_pressure(data):
    channels = data.shape[1]
    offset = data[:,:channels] - PRESSURE_SENSOR_OFFSET[:channels]
    final = offset * ANALOG_COEFFS[:channels]
    return final


# data: 1d np array of digital data
# returns: 2d uint8 array
def digital_to_array(data):
    digital = data.astype(np.uint8)
    binary_array = np.unpackbits(digital, axis=-1)
    # Reshape the binary array to a 2D array
    binary_2d_array = binary_array.reshape(digital.shape + (8,))
    # Exclude 0th bit and reverse order so ch0 is at index 0
    reversed_array = np.flip(binary_2d_array[:,1:], axis=1)
    return reversed_array


# Testing purposes
def main():
    data = np.full((64, 8), 4, dtype=np.int16)
    print(convert_to_pressure(data))

if __name__ == "__main__":
    main()
