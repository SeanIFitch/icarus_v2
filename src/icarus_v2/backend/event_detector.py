from PySide6.QtCore import QThread, Signal
from icarus_v2.backend.buffer_loader import BufferLoader
from icarus_v2.backend.event import Event


SAMPLE_RATE = 4000
EVENT_UPDATE_HZ = 30
PRESSURE_UPDATE_HZ = 5
EVENT_DISPLAY_BOUNDS = (-10, 140)


class EventDetector(QThread):
    def __init__(self, loader: BufferLoader, event_signal: Signal) -> None:
        pass
