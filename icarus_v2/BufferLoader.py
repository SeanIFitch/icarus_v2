from PySide6.QtCore import QThread
from Di4108USB import Di4108USB
from DataConverter import convert_to_pressure, digital_to_array
from SPMCRingBuffer import SPMCRingBuffer, SPMCRingBufferReader
import numpy as np


class BufferLoader(QThread):
    def __init__(self, buffer_seconds=120) -> None:
        super().__init__()
        self.device = Di4108USB()

        buffer_capacity = int(buffer_seconds * self.device.sample_rate)
        analog_shape = (buffer_capacity, self.device.channels_to_read - 1) # Subtract 1 for digital
        digital_shape = (buffer_capacity, 7) # Always 7 digital channels
        self.analog_buffer = SPMCRingBuffer(analog_shape, float)
        self.digital_buffer = SPMCRingBuffer(digital_shape, np.uint8)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.device.__exit__(exc_type, exc_value, traceback)


    def run(self):
        self.device.start_scan()
        analog_shape = (self.device.points_to_read, self.device.channels_to_read)
        digital_shape = (self.device.points_to_read, self.device.channels_to_read * 2)

        while self.device.acquiring:
            data = self.device.read_data()

            analog = np.reshape(np.frombuffer(data, dtype=np.int16), analog_shape)[:, :-1]
            pre = convert_to_pressure(analog)
            self.analog_buffer.enqueue(pre)

            # Digital is last channel read, and only the 2nd byte is necessary
            digital = np.reshape(np.asarray(data), digital_shape)[:,-1]
            dig = digital_to_array(digital)
            self.digital_buffer.enqueue(dig)

        self.device.end_scan()


    def new_analog_reader(self):
        return SPMCRingBufferReader(self.analog_buffer)


    def new_digital_reader(self):
        return SPMCRingBufferReader(self.digital_buffer)


    def get_sample_rate(self):
        return self.device.sample_rate


    def quit(self):
        self.device.stop()
        self.device.close_device()


# Testing purposes
def main():
    with BufferLoader() as loader:
        loader.run()


if __name__ == "__main__":
    main()
