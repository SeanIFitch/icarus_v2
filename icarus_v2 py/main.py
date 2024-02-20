from Di4108_USB import Di4108_USB
from SPMCRingBuffer import SPMCRingBuffer, SPMCRingBufferReader
import threading
from Module import Module


def main():
    with Di4108_USB() as device_instance:
        analog_buffer = SPMCRingBuffer(10)
        digital_buffer = SPMCRingBuffer(10)
        buffer_thread = threading.Thread(target=device_instance.acquire, args=(analog_buffer, digital_buffer))

        digital_reader = SPMCRingBufferReader(digital_buffer)
        mod = Module(digital_reader)
        module_thread = threading.Thread(target=mod.read, daemon=True)

        buffer_thread.start()
        module_thread.start()

        buffer_thread.join()
        module_thread.join()


if __name__ == "__main__":
    main()
