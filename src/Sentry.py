import numpy as np
from PySide6.QtCore import QObject, Signal
from Event import get_channel, gaussian_filter, Channel


class Sentry(QObject):
    warning_signal = Signal(str)
    error_signal = Signal(str)


    def __init__(self):
        super().__init__()
        self.pump_times = []
        self.max_pump_rate = 20 # strokes/hr
        self.max_depressurize_switch_time = 50 # ms


    # Shutdown if there is a sudden loss of pressure
    # Indicates massive leak
    def check_pressure(self, data):
        pass


    # Check pump rate
    # Too high indicates a leak
    # Takes pump events
    def check_pump_rate(self, event):
        # update pump strokes/hr
        self.pump_times.append(event.event_time)
        if len(self.pump_times) >= 5:
            avg = np.diff(self.pump_times[-5:]).mean()
            strokes_per_hour = 2 * 3600 / avg
            if strokes_per_hour > self.max_pump_rate:
                self.warning_signal.emit(f"Warning: pump rate above threshold {self.max_pump_rate} strokes/hr.")


    # Shutdown if pumping on startup when valves are open
    def check_pumping_pressure(self):
        pass


    # Warn if pressure continues to increase after a valve event
    # Indicates leaky pressurize valve
    def check_increasing_pressure(self, event):
        y = get_channel(event, Channel.HI_PRE_ORIG)
        y = y[np.argmax(y) + 30:]

        # Calculate the first derivative of the data
        dy = np.diff(y)
        dy_smoothed = gaussian_filter(dy, 5, 5)

        if max(dy_smoothed) > 0:
            self.warning_signal.emit(f"Warning: pressure continuing to increase after pressurize event.")


    # Warn if pressure continues to decrease after a valve event
    # Indicates leaky depressurize valve
    def check_decreasing_pressure(self):
        pass