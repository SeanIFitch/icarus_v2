from threading import Condition


# One producer, N consumers. Data stays in the buffer until all consumers have read it. 
# Set size buffer composed of a python list.
class SPMCRingBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = [None for _ in range(capacity)]
        self.to_read_chunks = [0 for _ in range(capacity)] # Count of consumers left to read each chunk
        self.consumer_count = 0
        self.head = 0  # Next index to write
        self.size = 0  # Number of elements in the buffer
        self.condition = Condition()


    # Data is copied by reference. Be careful about changing data.
    def enqueue(self, data):
        while self.size == self.capacity:
            print("Producer waiting for space in SPMCRingBuffer")
            self.condition.wait()  # Wait for space to become available

        # Sanity check. This should never occur.
        if self.to_read_chunks[self.head] > 0:
             raise RuntimeError("Writing to chunk with remaining consumers")

        self.buffer[self.head] = data
        self.to_read_chunks[self.head] = self.consumer_count
        self.head = (self.head + 1) % self.capacity
        self.size += 1

        self.condition.notify_all()  # Notify consumers


    def add_consumer(self):
        # New consumer starts reading from the lowest chunk still to be read
        consumer = SPMCRingBufferConsumer(self, self.tail)
        self.consumer_count += 1

        # Increment number of consumers to read any chunks which have data
        for i in range(self.capacity):
            if self.buffer[i] is not None:
                self.to_read_chunks[i] += 1

        return consumer


    def __sizeof__(self) -> int:
        return self.size


class SPMCRingBufferConsumer:
    def __init__(self, buffer, index, id):
        self.buffer = buffer
        self.index = index # Next index of the buffer for this consumer to read


    def read(self):
        # Read at head only if buffer is full
        
        #THIS WHILE CONDITION IS BROKEN
        while self.index == self.buffer.head and self.buffer.size < self.buffer.capacity:
            self.buffer.condition.wait()  # Wait for data to be available

        data = self.buffer.buffer[self.index]
        self.buffer.to_read_chunks[self.index] -= 1
        self.index = (self.index + 1) % self.buffer.capacity

        if self.buffer.to_read_chunks[self.index] == 0:
            self.buffer.tail = (self.buffer.tail + 1) % self.buffer.capacity
            self.buffer.size -= 1
            self.buffer.condition.notify_all()  # Notify producers

        return data
