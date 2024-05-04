from EventHandler import EventHandler
import numpy as np
from Event import Channel, get_channel, gaussian_filter, Event


# Detects pump strokes and sends to counter
# Take average of average_every points, take the derivative, and smooth it with a gaussian filter.
# Pump strokes are defined as points where this result falls below low_threshold and within pummp_width seconds rises above high_threshold.
# Only the points which initially exceed the thresholds are considered.
class PumpHandler(EventHandler):
    def __init__(self, loader, signal, sample_rate) -> None:
        self.pump_width = 0.7   # Time (s) after pressure drop within which increase is expected
        self.low_threshold = -2 # Threshold for pressure drop
        self.high_threshold = 1 # Threshold for increase
        self.average_every = 100 # Number of points to average
        self.last_low_index = - int(self.pump_width * sample_rate)
        self.last_high_index = - int(self.pump_width * sample_rate)

        update_rate = 1 / (self.pump_width * sample_rate)
        super().__init__(loader, signal, sample_rate, update_rate)


    # Override
    # Loops to transmit data if an event occurs
    def run(self):
        self.running = True
        while(self.running):
            # Make sure to fetch a multiple of the average_every points
            data_to_get = int(self.pump_width * self.sample_rate / self.average_every) * self.average_every
            try:
                data, buffer_index = self.reader.read(size=data_to_get, timeout=1)
            except TimeoutError:
                self.running = False
                break

            target_pressure = get_channel(data, Channel.TARGET)
            averaged_data = np.mean(target_pressure.reshape(-1, self.average_every), axis=1)

            # Smooth the derivative of the target pressure
            dy = np.diff(averaged_data) / self.average_every
            dy_smoothed = gaussian_filter(dy, 5, 5)

            # Find indices which exceed thresholds
            low_indices = np.where(dy_smoothed < self.low_threshold)[0]
            high_indices = np.where(dy_smoothed > self.high_threshold)[0]
            low_indices = np.insert(low_indices, 0, self.last_low_index)
            high_indices = np.insert(high_indices, 0, self.last_high_index)

            # Remove all sequential indices
            # CHECK: low indices maybe should be the end of sequences rather than the beginning (though a large enough pump_width should make this irrelevant)
            low_breaks = np.where(np.diff(low_indices) != 1)[0]
            high_breaks = np.where(np.diff(high_indices) != 1)[0]
            low_indices = low_indices[low_breaks]
            low_indices = np.insert(low_indices, 0, self.last_low_index) # Last one was always a break
            high_indices = high_indices[high_breaks]

            # Emit for every high index with a low index within pump_width
            for i in high_indices:
                most_recent = low_indices[low_indices < i][-1]
                if i - most_recent <= self.pump_width * self.sample_rate / self.average_every:
                    self.signal.emit(Event(Event.PUMP, None))

            self.last_low_index = len(dy_smoothed) - low_indices[-1]
            high_indices = np.insert(high_indices, 0, self.last_low_index) # Last one was always a break, but if we put it in earlier then this one would get checked again
            self.last_high_index = len(dy_smoothed) - high_indices[-1]
