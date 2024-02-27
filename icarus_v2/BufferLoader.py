from PySide6.QtCore import QThread
from Di4108USB import Di4108USB
from DataConverter import ADC_to_pressure, digital_to_array
from SPMCRingBuffer import SPMCRingBuffer, SPMCRingBufferViewer, SPMCRingBufferReader
import numpy as np


class BufferLoader(QThread):
    def __init__(self, minutes_of_data=2) -> None:
        super().__init__()
        self.minutes_of_data = minutes_of_data
        self.device = Di4108USB()

        # Calculate size of buffers
        seconds_per_chunk = float(self.device.points_to_read) / float(self.device.sample_rate)
        chunks_per_minute = 60 / seconds_per_chunk
        buffer_size = self.minutes_of_data * int(chunks_per_minute)

        self.analog_buffer = SPMCRingBuffer(buffer_size)
        self.digital_buffer = SPMCRingBuffer(buffer_size)


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.device.__exit__(exc_type, exc_value, traceback)


    def run(self):
        self.device.start_scan()
        data_shape = self.device.get_data_shape()

        while self.device.acquiring:
            data = self.device.read_data()

            analog = np.reshape(np.frombuffer(data, dtype=np.int16), data_shape)[:, :-1]
            pressures = ADC_to_pressure(analog)

            # Digital is last channel read, and only the 2nd byte is necessary
            digital = np.reshape(np.asarray(data), (self.points_to_read, self.channels_to_read*2))[:,-1]
            digital_array = digital_to_array(digital)


            self.analog_queue.enqueue(pressures)
            self.digital_queue.enqueue(digital_array)
        self.device.end_scan()


    def new_digital_viewer(self):
        return SPMCRingBufferViewer(self.digital_buffer)


    def new_analog_viewer(self):
        return SPMCRingBufferViewer(self.analog_buffer)


    def new_digital_reader(self):
        return SPMCRingBufferReader(self.digital_buffer)


    def new_analog_reader(self):
        return SPMCRingBufferReader(self.analog_buffer)


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
