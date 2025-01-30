from array import array
from threading import Lock
import lzma
import pickle
import numpy as np
import csv


# Fake device to load example data files
# Used only for testing.
class RawLogReader:
    def __init__(self, filename) -> None:
        self.sample_rate = 4000
        self.points_to_read = 64
        self.channels_to_read = 8
        self.initial_time = None
        self.current_dio = None
        self.acquiring = None
        self.bytes_to_read = self.channels_to_read * 2 * self.points_to_read

        # Used to tell how long to wait on reads
        self.read_count = 0
        # File
        self.file = lzma.open(filename, "rb")

    def read_data(self):
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

    def process_data(self, data):
        data_shape = (64, 8)

        int_array = np.frombuffer(data, dtype=np.int16)
        reshaped_array = np.reshape(int_array, data_shape)
        reshaped_array[:,-1] = reshaped_array[:,-1] >> 8    # Digital is only in the 1st byte

        return reshaped_array

    def close_device(self):
        self.file.close()


def read_and_write_to_csv(raw_log_reader, output_filename):
    with open(output_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write header
        header = [f'Channel_{i}' for i in range(raw_log_reader.channels_to_read - 1)] + ['Digital']
        csv_writer.writerow(header)

        try:
            while True:
                raw_data = raw_log_reader.read_data()
                processed_data = raw_log_reader.process_data(raw_data)

                for row in processed_data:
                    csv_writer.writerow(row)

        except RuntimeError as e:
            if str(e) == "End of file reached.":
                print("Finished reading the file.")
            else:
                print(f"An error occurred: {e}")
        finally:
            raw_log_reader.close_device()


# Usage
input_file = "logs/example/log_2024-07-19_18-19-00.xz"
output_file = "output.csv"

reader = RawLogReader(input_file)
read_and_write_to_csv(reader, output_file)