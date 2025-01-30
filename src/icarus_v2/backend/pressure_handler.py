from icarus_v2.backend.event_handler import EventHandler
from icarus_v2.backend.event import Event


# Sends pressure data constantly. Events always occur.
class PressureHandler(EventHandler):
    def __init__(self, loader, signal, sample_rate, update_rate) -> None:
        super().__init__(loader, signal, sample_rate, update_rate)
        self.event_type = Event.PRESSURE


    # Loops to transmit data if an event occurs
    # Overridden because events always occur for this handler and all data is used
    def run(self):
        self.running = True
        while(self.running):
            data_to_get = int(self.sample_rate / self.update_rate)
            try:
                data, buffer_index = self.reader.read(size=data_to_get, timeout=1)
            except TimeoutError:
                self.running = False
                break

            # Transmit data to plot
            new_event = Event(self.event_type, data)
            self.signal.emit(new_event)
