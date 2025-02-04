import traceback

from PySide6.QtCore import QThread, Signal
from icarus_v2.backend.buffer_loader import BufferLoader
from icarus_v2.backend.event import Event


SAMPLE_RATE = 4000
EVENT_UPDATE_HZ = 30
PRESSURE_UPDATE_HZ = 5
EVENT_DISPLAY_BOUNDS = (-10, 140)


class EventDetector(QThread):
    def __init__(self, loader: BufferLoader, event_signal: Signal) -> None:
        super().__init__()
        self.reader = loader.new_reader()
        self.event_signal = event_signal
        self.running = False

    # Loops to transmit data if an event occurs
    def run(self) -> None:
        self.running = True

        data_to_get = int(SAMPLE_RATE / EVENT_UPDATE_HZ)
        update_pressure_after = int(EVENT_UPDATE_HZ / PRESSURE_UPDATE_HZ)

        while self.running:
            try:
                data, buffer_index = self.reader.read(size=data_to_get, timeout=1)
            except TimeoutError:
                self.running = False
                break
            try:
                event, chunk_index = self.detect_event(data)
            except RuntimeWarning:
                # Case where 2 events occur in same chunk
                traceback.print_exc()
                event, chunk_index = False, -1

            # buffer_index is the index at which the chunk started in the buffer
            # chunk index is the index at which the event started in the chunk
            event_index = buffer_index + chunk_index

            # If an event occurs, transmit data to plot
            if event:
                event_data, event_start = self.handle_event(event_index)
                if event_data is not None:
                    new_event = Event(self.event_type, event_data, event_start)
                    self.signal.emit(new_event)

    def detect_dio_changed(self, data: bytes) -> bool:
        pass
