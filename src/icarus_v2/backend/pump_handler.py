from icarus_v2.backend.event_handler import EventHandler
import numpy as np
from icarus_v2.backend.event import Channel, get_channel, Event


# Detects pump strokes and sends to counter
# Take average of average_every points, take the derivative, and smooth it with a gaussian filter.
# Pump strokes are defined as points where this result falls below low_threshold.
# Only the points which initially exceed the thresholds are considered.
class PumpHandler(EventHandler):
    def __init__(self, loader, signal, sample_rate) -> None:
        self.sigma = 5
        self.threshold = 0.01

        self.overlap = 2000 # number of points to add before each chunk
        self.overlap_data = None

        self.event_report_range = (-50, 1500)
        self.event_type = Event.PUMP

        update_rate = 2
        super().__init__(loader, signal, sample_rate, update_rate)


    # Override
    # Loops to transmit data if an event occurs
    def run(self):
        self.running = True
        while self.running:
            # Make sure to fetch a multiple of the average_every points
            data_to_get = int(self.sample_rate / self.update_rate)
            try:
                data, buffer_index = self.reader.read(size=data_to_get, timeout=1)
            except TimeoutError:
                self.running = False
                break

            target_pressure = get_channel(data, Channel.TARGET)

            if self.overlap_data is not None:
                target_pressure = np.concatenate((self.overlap_data, target_pressure))

            x = np.arange(-25, 26)
            y = np.exp(-0.5 * (x / self.sigma) ** 2)
            dy2 = np.roll(y, -1) + np.roll(y, 1) - 2 * y
            dy2 /= dy2.min()
            corr = np.correlate(target_pressure, dy2, mode='same') / np.correlate(target_pressure, y, mode='same')
            stroke = (np.roll(corr, -1) < corr) & (np.roll(corr, 1) < corr) & (corr > self.threshold) & (
                    np.roll(target_pressure, -35) < target_pressure) & (
                             np.roll(target_pressure, 35) < target_pressure) & (target_pressure > 2000)

            # Remove detections near the edges
            if self.overlap_data is not None:
                stroke[:int(self.overlap / 2)] = False
            stroke[-int(self.overlap / 2):] = False

            indices = np.where(stroke)[0]

            # Emit for every dip
            for i in indices:
                event_index = buffer_index + i - self.overlap
                event_data = self.get_event_data(event_index)
                if event_data is not None:
                    sample_rate_kHz = float(self.sample_rate) / 1000
                    chunk_event_index = int( - self.event_report_range[0] * sample_rate_kHz)
                    new_event = Event(self.event_type, event_data, chunk_event_index)
                    self.signal.emit(new_event)

            self.overlap_data = target_pressure[-self.overlap:]

    def reset(self):
        self.overlap_data = None
