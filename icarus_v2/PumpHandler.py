from EventHandler import EventHandler
import numpy as np
from Event import Channel, get_channel, gaussian_filter


# Detects pump strokes and sends to counter
# Pump stroke is defined as the index where the smoothed derivative of the target pressure falls below the threshold
# They cannot occur within min_interval seconds of each other
class PumpHandler(EventHandler):
    def __init__(self, loader, signal, sample_rate, min_interval = 0.25, threshold = -30) -> None:
        self.min_interval = min_interval
        self.threshold = threshold
        update_rate = 1 / min_interval
        super().__init__(loader, signal, sample_rate, update_rate)
        self.last_event_index = - int(min_interval * sample_rate)


    # Override
    # Loops to transmit data if an event occurs
    def run(self):
        self.running = True
        while(self.running):
            data_to_get = int(self.sample_rate / self.update_rate)
            try:
                data, buffer_index = self.reader.read(size=data_to_get, timeout=1)
            except TimeoutError:
                self.running = False
                break

            target_pressure = get_channel(data, Channel.TARGET)
            # Smooth the derivative of the target pressure
            dy = np.diff(target_pressure) / np.diff(np.arange(data_to_get))
            dy_smoothed = gaussian_filter(dy, 5, 5)

            min_index = max(0, self.last_event_index + self.sample_rate * self.min_interval - buffer_index)
            indeces = np.where(dy_smoothed[min_index:] < self.threshold)[0]
            if indeces.size > 0:
                stroke_index = indeces[0] + min_index + buffer_index
                self.last_event_index = stroke_index
                self.signal.emit()
