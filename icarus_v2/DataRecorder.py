from datetime import datetime
from time import time
from struct import pack
import csv
from BufferLoader import device_readings

# Takes raw data from device and writes to bin for future testing/debugging
class DataRecorder():
    def __init__(self) -> None:
        super().__init__()
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.csv_filename = f"data_{current_datetime}.csv"
        self.bin_filename = f"data_{current_datetime}.bin"



    def append_pressurize_event(self, data):
        with open(self.csv_filename, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(data)



    # appends data to bin. data is array of ints.
    def append_data_to_bin(self, data):
        packed_data = pack(f'<I{len(data)}B', int(time()), *data)
        with open(self.bin_filename, 'ab') as bin_file:
            bin_file.write(packed_data)


    # Appends data to CSV file. Data is a list of values.
    def append_data_to_csv(self, data):
        with open(self.csv_filename, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(data)