from PySide6.QtCore import QThread, Signal
from SPMCRingBuffer import SPMCRingBuffer, SPMCRingBufferReader
import numpy as np
from RawDataLogger import RawDataLogger


# Structure to hold data from one time slot. 
# Analog CH7, Digital CH3, CH5, CH6 are unused.
device_readings = np.dtype([
    ('target', float),          # Analog CH0: target pressure 
    ('depre_low', float),       # Analog CH1: depressurization valve lower sensor
    ('depre_up', float),        # Analog CH2: depressurization valve upper sensor
    ('pre_low', float),         # Analog CH3: pressurization valve lower sensor
    ('pre_up', float),          # Analog CH4: pressurization valve upper sensor
    ('hi_pre_orig', float),     # Analog CH5: high pressure transducer at the origin
    ('hi_pre_sample', float),   # Analog CH6: high pressure transducer at the sample
    ('pump', np.bool_),         # Digital CH0: high pressure pump (Active high / pumping on True)
    ('depre_valve', np.bool_),  # Digital CH1: depressurize valve (Active low / open on False)
    ('pre_valve', np.bool_),    # Digital CH2: pressurize valve (Active low / open on False)
    ('log', np.bool_)           # Digital CH4: log (Active low / logging on False)
])


# This class is responsible for creating a buffer, reading from the device, processing the data, and putting it into the buffer.
class BufferLoader(QThread):
    # Constants for pressure conversion
    # TODO: get actual values for these. there should be a method for setting and storing offsets.
    PRESSURE_COEFFS = np.asarray([1.0]*7)
    PRESSURE_SENSOR_OFFSET = np.asarray([0.0]*7)

    raw_data_signal = Signal(object)

    def __init__(self, device, buffer_seconds=120) -> None:
        super().__init__()
        self.device = device

        buffer_capacity = int(buffer_seconds * self.device.sample_rate)
        self.buffer = SPMCRingBuffer(buffer_capacity, device_readings)


    def run(self):
        logger = RawDataLogger()
        self.raw_data_signal.connect(logger.log_event)

        self.device.start_scan()

        while self.device.acquiring:
            data = self.device.read_data()

            self.raw_data_signal.emit(data)

            processed_data = self.process_data(data)
            self.buffer.enqueue(processed_data)

        self.device.end_scan()


    def process_data(self, data):
        analog_shape = (self.device.points_to_read, self.device.channels_to_read)
        digital_shape = (self.device.points_to_read, self.device.channels_to_read * 2)

        analog = np.frombuffer(data, dtype=np.int16)
        analog = np.reshape(analog, analog_shape)[:, :-1]
        digital = np.asarray(data).astype(np.uint8)
        digital = np.reshape(digital, digital_shape)[:,-1]

        pressures = (analog * self.PRESSURE_COEFFS) - self.PRESSURE_SENSOR_OFFSET
        binary_array = np.unpackbits(digital, axis=-1).reshape(digital.shape + (8,))
        # Exclude 0th bit and reverse order so ch0 is at index 0
        bool_array = np.flip(binary_array[:,1:], axis=1).astype(np.bool_)

        # Convert to proper data structure
        processed_data = np.rec.fromarrays([pressures[:,0], pressures[:,1],
            pressures[:,2], pressures[:,3], pressures[:,4], pressures[:,5],
            pressures[:,6], bool_array[:,0], bool_array[:,1], bool_array[:,2],
            bool_array[:,4]], dtype=device_readings)

        return processed_data


    def new_reader(self):
        return SPMCRingBufferReader(self.buffer)


    def get_sample_rate(self):
        return self.device.sample_rate


    def quit(self):
        self.device.stop()
        self.device.close_device()

