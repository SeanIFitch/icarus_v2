import numpy as np


#convert integer values on the sensor to psi
CH0_COEFF = (1/1.33)*(1/150)*79600.0*200*2.0**-15 #target pressure
CH1_COEFF = (1/50)*200*2.0**-15 #depressurization valve lower sensor
CH2_COEFF = (1/50)*200*2.0**-15 #depressurization valve upper sensor
CH3_COEFF = (1/50)*200*2.0**-15 #pressurization valve lower sensor
CH4_COEFF = (1/50)*200*2.0**-15 #pressurization valve upper sensor
CH5_COEFF = 2*50000*2.0**-15 #high pressure transducer at the origin
CH6_COEFF = 2*50000*2.0**-15 #high pressure transducer at the sample
CH7_COEFF = 1 #spare
DIO_COEFF = 42860.0

ANALOG_COEFFS = [CH0_COEFF, CH1_COEFF, CH2_COEFF, CH3_COEFF, CH4_COEFF, CH5_COEFF, CH6_COEFF, CH7_COEFF]

USER_UNITS = {'kbar': 6.894756709891046e-05, 'atm': 1/14.696, 'psi': 1}

#readings for pressure sensors at atmospheric pressure
PRESSURE_SENSOR_OFFSET = np.asarray([69.5595, 65.562, 68.881375, 84.2195, 86.96075, 17.248, 17.322, 0])


def ADC_to_pressure(analog_data):
    shape = analog_data.size
    return analog_data * ANALOG_COEFFS[:shape[1]]


def digital_to_array(digital_data):
    reshaped_array = digital_data.reshape(-1, 1)
    bits_array = np.unpackbits(reshaped_array, axis=1)
    bits_array_2d = bits_array.reshape(digital_data.shape[0], -1)
    final = bits_array_2d[:,1:][:,::-1] # Exclude first column and reverse order
    return final
