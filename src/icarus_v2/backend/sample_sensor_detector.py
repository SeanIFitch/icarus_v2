from icarus_v2.backend.event import Channel, get_channel, Event
from PySide6.QtCore import QObject


# Detects whether the sample sensor is connected to the sample tube by receiving depressurize events
class SampleSensorDetector(QObject):
    low_threshold = 0.998
    high_threshold = 1.05

    def __init__(self, config_manager, signal=None):
        super().__init__()
        self.config_manager = config_manager
        self.config_manager.settings_updated.connect(self.update_settings)
        self.coefficients = config_manager.get_settings("plotting_coefficients")
        self.last_result = None

        self.sample_sensor_connected = signal

    def detect(self, event):
        if event.event_type == Event.DEPRESSURIZE:
            if not self.detect_sensor(event):
                # require 2 differences in a row to decrease likelihood of false positives
                if not self.last_result:
                    self.sample_sensor_connected.emit(False)
                self.last_result = False
            else:
                if self.last_result:
                    self.sample_sensor_connected.emit(True)
                self.last_result = True

    def detect_from_list(self, events, coefficients):
        # base decision off last 10 events
        depressurize = []
        for event in events[::-1]:
            if event.event_type == Event.DEPRESSURIZE:
                depressurize.append(event)
            if len(depressurize) == 10:
                break
        num_connected = sum([self.detect_sensor(event, coefficients) for event in depressurize])
        if len(depressurize) > 0:
            sample_sensor_connected = num_connected / len(depressurize) > 0.5
        else:
            sample_sensor_connected = True
        self.sample_sensor_connected.emit(sample_sensor_connected)

    def detect_sensor(self, depressurize_event, coefficients=None):
        if coefficients is None:
            coefficients = self.coefficients

        origin = get_channel(depressurize_event, Channel.HI_PRE_ORIG)[:depressurize_event.event_index].astype('float64')
        sample = get_channel(depressurize_event, Channel.HI_PRE_SAMPLE)[:depressurize_event.event_index].astype('float64')
        origin *= coefficients[Channel.HI_PRE_ORIG]
        sample *= coefficients[Channel.HI_PRE_SAMPLE]

        # AC noise is above 3 kBar, experiments are never run at this pressure
        if sample.max() > 3.0:
            return False

        # percent difference between the two signals
        diff = (origin.mean() - sample.mean()) / origin.mean()

        # If within range, sample sensor is reading a 100% difference and thus is not connected
        if self.low_threshold < diff < self.high_threshold:
            return False
        else:
            return True

    def update_settings(self, key):
        if key == "plotting_coefficients":
            self.coefficients = self.config_manager.get_settings(key)
