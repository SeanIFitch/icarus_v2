from threading import Event

# One producer, N consumers.
# Set size buffer composed of an np array.
# Indexes are stored absolutely, so use head % capacity to get a list index
class SPMCRingBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = [None for _ in range(capacity)]
        self.write_index = 0
        self.new_data = Event() # Notifies waiting threads when new data has been enqueued


    # Data is copied by reference. Be careful about changing data.
    # Overwrites oldest data
    def enqueue(self, data):
        self.buffer[self.write_index % self.capacity] = data
        self.write_index += 1

        # Notify readers that new data is available
        self.new_data.set()


# All viewers should be terminated before the writer
class SPMCRingBufferViewer:
    def __init__(self, buffer):
        self.buffer = buffer


    def has_data(self):
        return self.read_index < self.buffer.write_index


    # Returns range of data without advancing read_index
    def retrieve_range(self, start, end, timeout=None):
        c = self.buffer.capacity
        if end - start > c:
            raise RuntimeError("Retrieving more data than buffer can store")

        # Wait for data to be available up till end
        while end >= self.buffer.write_index:
            if self.buffer.new_data.wait(timeout):
                self.buffer.new_data.clear()
            else:
                raise TimeoutError

        # Case where range goes through end of buffer
        if end % c < start % c:
            return self.buffer.buffer[start % c:] + self.buffer.buffer[:end % c]
        else:
            return self.buffer.buffer[start % c:end % c]


class SPMCRingBufferReader(SPMCRingBufferViewer):
    def __init__(self, buffer):
        super().__init__(buffer)
        # Start with nothing to read
        self.read_index = buffer.write_index # Next index of the buffer for this reader to read


    def read(self, timeout=None):
        # Block until data is available
        while not self.has_data():
            if self.buffer.new_data.wait(timeout):
                self.buffer.new_data.clear()
            else:
                raise TimeoutError

        # Raise error if the reader was lapped, meaning it did not look at some data
        if self.buffer.write_index > self.read_index + self.buffer.capacity:
            raise RuntimeError(f"Reader was lapped. Reading at {self.read_index} when head is at {self.buffer.write_index}.")

        data = self.buffer.buffer[self.read_index % self.buffer.capacity]
        self.read_index += 1

        return data, self.read_index - 1
