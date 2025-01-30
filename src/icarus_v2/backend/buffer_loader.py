from PySide6.QtCore import QThread, Signal
from icarus_v2.backend.ring_buffer import RingBuffer, SPMCRingBufferReader
import numpy as np
import usb.core
from icarus_v2.backend.logger import Logger


# This class is responsible for creating a buffer, reading from the device, processing the data, and putting it into the buffer.
class BufferLoader(QThread):
    device_disconnected = Signal()

    def __init__(self, buffer_seconds=120) -> None:
        super().__init__()
        num_channels = 8
        buffer_capacity = int(buffer_seconds * 4000)
        self.buffer = RingBuffer((buffer_capacity, num_channels), np.int16)
        self.device = None

        # TESTING ONLY. logs all example data.
        self.log_raw = False


    def set_device(self, device):
        self.device = device


    def run(self):
        if self.device is None: return

        if self.log_raw:
            self.raw_logger = Logger()
            self.raw_logger.new_log_file(raw = True)

        self.device.start_scan()

        while self.device.acquiring:
            try:
                data = self.device.read_data()
            except usb.core.USBError:
                # Device disconnected
                self.device.acquiring = False
                self.device_disconnected.emit()
                return
            except RuntimeError as e:
                if "End of file reached." in str(e):
                    # End of file reached
                    self.device.acquiring = False
                    self.device_disconnected.emit()
                    return
                else:
                    raise e

            if self.log_raw:
                self.raw_logger.log_raw(data)
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
        self.may_start = False
        if self.device is not None and self.device.acquiring:
            self.device.stop()
            self.device.close_device()
