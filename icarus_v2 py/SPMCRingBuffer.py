from threading import Event

# One producer, N consumers. 
# Set size buffer composed of a python list.
# Indexes are stored absolutely, so use head % capacity to get a list index
class SPMCRingBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = [None for _ in range(capacity)]
        self.write_index = 0
        self.event = Event() # Notifies waiting threads when new data has been enqueued


    # Data is copied by reference. Be careful about changing data.
    # Overwrites oldest data
    def enqueue(self, data):
        self.buffer[self.write_index % self.capacity] = data
        self.write_index += 1

        # Notify readers that new data is available
        self.event.set()


class SPMCRingBufferReader:
    def __init__(self, buffer):
        self.buffer = buffer
        # Start with nothing to read
        self.read_index = buffer.write_index # Next index of the buffer for this reader to read


    def has_data(self):
        return self.read_index < self.buffer.write_index


    def read(self):
        # Block until data is available
        while not self.has_data():
            self.buffer.event.wait()

        # Raise error if the reader was lapped, meaning it did not look at some data
        if self.buffer.write_index > self.read_index + self.buffer.capacity:
            raise RuntimeError(f"Reader was lapped. Reading at {self.read_index} when head is at {self.buffer.write_index}.")

        data = self.buffer.buffer[self.read_index % self.buffer.capacity]
        self.read_index += 1

        # Reset event so next reader can be notified
        self.buffer.event.clear()

        return data
