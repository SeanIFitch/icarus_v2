import lzma
import pickle
from Event import Event
from PySide6.QtCore import Signal, QObject

# Load events from logs
class EventLoader(QObject):
    pressurize_event_signal = Signal(Event)
    depressurize_event_signal = Signal(Event)

    def __init__(self):
        super().__init__()
        self.events = []
        self.index = 0


    def read_events(self, filename):
        file = lzma.open(filename, "rb")  # Open file in read binary mode
        try:
            while True:
                # Deserialize event data using pickle
                event_dict = pickle.load(file)
                event = Event(
                    event_dict['event_type'],
                    event_dict['data'],
                    event_dict['event_index'],
                    event_dict['event_time']
                )
                self.events.append(event)
        except EOFError:
            pass  # End of file reached


    def emit_next_event(self):
        event = self.events[self.index]
        if event.event_type == Event.DEPRESSURIZE:
            self.depressurize_event_signal.emit(event)
        elif event.event_type == Event.PRESSURIZE:
            self.pressurize_event_signal.emit(event)
        if self.index < len(self.events):
            self.index += 1


    def emit_last_event(self):
        if self.index > 0:
            self.index -= 1
        event = self.events[self.index]
        if event.event_type == Event.DEPRESSURIZE:
            self.depressurize_event_signal.emit(event)
        elif event.event_type == Event.PRESSURIZE:
            self.pressurize_event_signal.emit(event)


    def close(self):
        self.file.close()
