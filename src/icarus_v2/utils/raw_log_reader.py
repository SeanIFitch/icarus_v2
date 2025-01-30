from array import array
from threading import Lock
from time import time, sleep
import lzma
import pickle


# Fake device to load example data files
# Used only for testing.
class RawLogReader:
    def __init__(self, filename) -> None:
        self.stop_lock = Lock() # Used to make sure you do not stop the device while reading
        self.sample_rate = 4000
        self.points_to_read = 64
        self.channels_to_read = 8
        self.initial_time = None
        self.current_dio = None
        self.acquiring = None
        self.bytes_to_read = self.channels_to_read * 2 * self.points_to_read
        self.stop()

        # Used to tell how long to wait on reads
        self.read_count = 0
        # File
        self.file = lzma.open(filename, "rb")

    def read_data(self):
        if self.read_count == 0:
            self.initial_time = time()
        else:
            speed = 2
            next_read = self.initial_time + self.read_count * self.points_to_read / (self.sample_rate * speed)
            sleep(max(0, next_read - time()))
        self.read_count += 1

        try:
            # Deserialize each object from the file
            data = pickle.load(self.file)
            # Append the array if it matches the expected structure
            if not isinstance(data, array):
                raise TypeError("Error parsing example data file: Data is not an array.")
            return data
        except EOFError:
            raise RuntimeError("End of file reached.")

    def close_device(self):
        self.file.close()

    # Dummy functions to simulate DI4108USB behavior.
    # None of these do anything more than change member variables.

    def set_dio(self, value=0b1111111, check_echo=True):
        self.current_dio = int(value)

    def start_scan(self):
        # Prevent stopping device while reading
        self.stop_lock.acquire()
        # Start reading
        self.acquiring = True

    def end_scan(self):
        if self.stop_lock.locked():
            self.stop_lock.release()

    def stop(self):
        """
        - stops data acquisition
        - set digital IO to all high
        """
        self.acquiring = False # Signals to stop acquiring
        with self.stop_lock:
            pass
        # Turn all valves off
        self.set_dio(0b1111111, check_echo=False)

    def get_current_dio(self):
        return self.current_dio
