from PySide6.QtCore import QThread, Signal
from SPMCRingBuffer import SPMCRingBuffer, SPMCRingBufferReader
import numpy as np


# This class is responsible for creating a buffer, reading from the device, processing the data, and putting it into the buffer.
class BufferLoader(QThread):

    def __init__(self, device, buffer_seconds=120) -> None:
        super().__init__()
        self.device = device

        num_channels = self.device.channels_to_read
        buffer_capacity = int(buffer_seconds * self.device.sample_rate)
        self.buffer = SPMCRingBuffer((buffer_capacity, num_channels), np.int16)


    def run(self):
        self.device.start_scan()

        while self.device.acquiring:
            data = self.device.read_data()
            processed_data = self.process_data(data)
            self.buffer.enqueue(processed_data)

        self.device.end_scan()


    def process_data(self, data):
        data_shape = (self.device.points_to_read, self.device.channels_to_read)

        int_array = np.frombuffer(data, dtype=np.int16)
        reshaped_array = np.reshape(int_array, data_shape)
        reshaped_array[:,-1] = reshaped_array[:,-1] >> 8    # Digital is only in the 1st byte

        return reshaped_array


    def new_reader(self):
        return SPMCRingBufferReader(self.buffer)


    def get_sample_rate(self):
        return self.device.sample_rate


    def quit(self):
        self.device.stop()
        self.device.close_device()
