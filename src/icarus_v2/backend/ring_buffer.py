from threading import Event
import numpy as np

# One producer, N consumer, which each read sequentially from the start without skipping any data.
# Set size buffer composed of an np array.
# Assumes data is only loaded along dimension 0.
# Indexes are stored absolutely, so use head % capacity to get a list index.
class RingBuffer:
    def __init__(self, shape, dtype=int):
        if isinstance(shape, int):
            shape = (shape,)
        self.capacity = shape[0]
        self.buffer = np.empty(shape, dtype=dtype)
        self.write_index = 0
        self.new_data = Event() # Notifies waiting threads when new data has been enqueued


    # Data is copied by reference. Be careful about changing data.
    # Overwrites oldest data
    def enqueue(self, data):
        start = self.write_index % self.capacity
        end = start + len(data)
        if end < self.capacity:
            self.buffer[start:end] = data
        # Case where writing over end of buffer
        else:
            self.buffer[start:] = data[:self.capacity - start]
            self.buffer[:end - self.capacity] = data[self.capacity - start:]
        self.write_index += len(data)

        # Notify readers that new data is available
        self.new_data.set()


# All readers should be terminated before the writer
class SPMCRingBufferReader:
    def __init__(self, buffer):
        self.buffer = buffer
        # Start with nothing to read
        self.read_index = buffer.write_index # Next index of the buffer for this reader to read


    # Returns view of range of data without advancing read_index
    def retrieve_range(self, start, end, timeout=2):
        cap = self.buffer.capacity
        start = max(0, start)

        if end - start > cap:
            raise RuntimeError("Retrieving more data than buffer can store")

        # Raise error if the reader was lapped, meaning some data was overwritten
        if self.buffer.write_index >= end + cap:
            raise RuntimeError(f"Reader was lapped. Reading at {self.read_index} when head is at {self.buffer.write_index}.")

        # Wait for data to be available up till end
        while end > self.buffer.write_index:
            if self.buffer.new_data.wait(timeout):
                self.buffer.new_data.clear()
            else:
                raise TimeoutError

        # Case where range goes through end of buffer
        if end % cap < start % cap:
            a1 = self.buffer.buffer[start % cap:]
            a2 = self.buffer.buffer[:end % cap]
            return np.concatenate((a1,a2))
        else:
            return self.buffer.buffer[start % cap:end % cap]


    # Read block of size size starting at the last index read by this reader
    # Returns a view of that data and the starting index of it
    def read(self, size, timeout=2):
        end = self.read_index + size
        data = self.retrieve_range(self.read_index, end, timeout=timeout)

        self.read_index += size

        return data, self.read_index - size
