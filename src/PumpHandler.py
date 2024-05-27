from EventHandler import EventHandler
import numpy as np
from Event import Channel, get_channel, gaussian_filter, Event


# Detects pump strokes and sends to counter
# Take average of average_every points, take the derivative, and smooth it with a gaussian filter.
# Pump strokes are defined as points where this result falls below low_threshold.
# Only the points which initially exceed the thresholds are considered.
class PumpHandler(EventHandler):
    def __init__(self, loader, signal, sample_rate) -> None:
        self.threshold = -0.0007 # Threshold for pressure drop
        self.average_every = 100 # Number of points to average

        self.last_low_index = None
        self.last_averaged_target = None

        # max 10% of last 10 data chunks
        # used for scaling
        self.last_chunk_maxes = [[0]]

        self.event_report_range = (-50, 1500)
        self.event_type = Event.PUMP

        update_rate = 2
        super().__init__(loader, signal, sample_rate, update_rate)


    # Override
    # Loops to transmit data if an event occurs
    def run(self):
        self.running = True
        while(self.running):
            # Make sure to fetch a multiple of the average_every points
            data_to_get = int(self.sample_rate / (self.update_rate * self.average_every)) * self.average_every
            try:
                data, buffer_index = self.reader.read(size=data_to_get, timeout=1)
            except TimeoutError:
                self.running = False
                break

            target_pressure = get_channel(data, Channel.TARGET)
            averaged_data = np.mean(target_pressure.reshape(-1, self.average_every), axis=1)
            if self.last_averaged_target is None:
                self.last_averaged_target = averaged_data[0]
            averaged_data = np.insert(averaged_data, 0, self.last_averaged_target)
            self.last_averaged_target = averaged_data[-1]

            # scale data by average of the highest values of the last 10 chunks
            flattened_maxes = np.concatenate(self.last_chunk_maxes)
            scale_factor = np.sort(flattened_maxes)[::-1][:int(0.1*len(averaged_data))].mean()
            # add max 10% of this chunk to last_chunk_maxes
            max_ten_percent = np.sort(averaged_data)[::-1][:int(0.1*len(averaged_data))]
            self.last_chunk_maxes.append(max_ten_percent)
            if len(self.last_chunk_maxes) > 10:
                self.last_chunk_maxes.pop(0)
            # dont emit if the data is too small (many false positives due to noise)
            if scale_factor < 1000:
                continue

            # Smooth the derivative of the target pressure
            scaled_data = averaged_data / scale_factor
            dy = np.diff(scaled_data) / self.average_every
            dy_smoothed = gaussian_filter(dy, 3, 1)

            # Find indices which exceed threshold
            low_indices = np.where(dy_smoothed < self.threshold)[0]
            if self.last_low_index is None:
                self.last_low_index = -2 # does not interfere as long as its not -1
            low_indices = np.insert(low_indices, 0, self.last_low_index)

            # Remove all sequential indices
            breaks = np.where(np.diff(low_indices) != 1)[0]
            low_indices = low_indices[breaks + 1]

            # Emit for every dip
            for i in low_indices:
                event_index = buffer_index + i * self.average_every
                event_data = self.get_event_data(event_index)
                if event_data is not None:
                    sample_rate_kHz = float(self.sample_rate) / 1000
                    event_index = int( - self.event_report_range[0] * sample_rate_kHz)
                    new_event = Event(self.event_type, event_data, event_index)
                    self.signal.emit(new_event)

            if len(low_indices) > 0:
                self.last_low_index = low_indices[-1] - len(dy_smoothed)
            else:
                self.last_low_index -= len(dy_smoothed)


    def reset(self):
        self.last_low_index = None
        self.last_averaged_target = None
        self.last_chunk_maxes = [[0]]
