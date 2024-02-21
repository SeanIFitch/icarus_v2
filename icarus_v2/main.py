from Di4108USB import Di4108USB
from SPMCRingBuffer import SPMCRingBuffer, SPMCRingBufferReader
from Module import Module
from threading import Thread

# High level application control

def main():
    with Di4108USB() as device_instance:
        # Calculate size of buffer to store 2 mins of data
        seconds_per_chunk = float(device_instance.points_to_read) / float(device_instance.sample_rate)
        chunks_per_minute = 60 / seconds_per_chunk
        buffer_size = 2 * int(chunks_per_minute)

        # Declare buffering thread
        analog_buffer = SPMCRingBuffer(buffer_size)
        digital_buffer = SPMCRingBuffer(buffer_size)
        buffer_thread = Thread(target=device_instance.acquire, args=(analog_buffer, digital_buffer))

        # Declare module thread 1
        digital_reader = SPMCRingBufferReader(digital_buffer)
        mod = Module(digital_reader)
        module_thread = Thread(target=mod.read, daemon=True)

        # Run threads
        buffer_thread.start()
        module_thread.start()

        buffer_thread.join()
        module_thread.join()


if __name__ == "__main__":
    main()
