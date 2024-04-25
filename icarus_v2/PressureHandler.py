from EventHandler import EventHandler
from Event import Event


# Sends pressure data constantly. Events always occur.
class PressureHandler(EventHandler):
    def __init__(self, loader, sample_rate, update_rate) -> None:
        super().__init__(loader, sample_rate, update_rate)
        self.event_type = Event.PRESSURE


    # Loops to transmit data if an event occurs
    # Overridden because events always occur for this handler and all data is used
    def run(self):
        self.running = True
        while(self.running):
            data_to_get = int(self.sample_rate / self.update_rate)
            data, buffer_index = self.reader.read(size=data_to_get, timeout=2)

            # Transmit data to plot
            new_event = Event(self.event_type, data, None)
            self.event_signal.emit(new_event)
