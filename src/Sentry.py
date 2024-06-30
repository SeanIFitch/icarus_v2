import numpy as np
from PySide6.QtCore import QThread, Signal
from Event import get_channel, Channel
from time import localtime, strftime


# Emits error if in experiment mode and 
# - pressure does not increase after rapid pump events
# - average pressure difference over periods exceeds 25% twice in a row
# Emits warning if in experiment mode and
# - pressure before depressurize event decreases by more than 10%
# - pressure before first pressurize event after a depressurize increases by more than 10%

# Emits warning if not in experiment mode and
# - pressure does not increase after rapid pump events

# Gets expected values for the experiment checks from the first example_events events of an experiment
class Sentry(QThread):
    warning_signal = Signal(str)
    error_signal = Signal(str)


    def __init__(self):
        super().__init__()
        # Number of events with which to define expected values
        self.example_events = 10
        # Percent difference from expected value to emit warning
        self.max_period_presure_difference = 0.25
        self.max_pump_rate_increase = 0.25
        self.max_pressure_before_depress_decrease = 0.1
        self.max_pressure_before_press_increase = 0.1

        self.current_experiment = False

        # Values defined after an experiment starts for defaults
        self.example_periods = []
        self.example_depress_pressures = []
        self.example_press_pressures = []
        self.pump_times = []
        self.expected_period = None
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None
        self.expected_pressure_before_pressurize = None

        # Values used to check current state against expected value
        self.last_pump_time = None
        self.last_pump_initial_pressure = None
        self.last_depressurize_time = None
        self.last_pressurize_time = None
        self.last_period_raised_error = False


    # Takes boolean representing the new state of bit 4
    # Resets all expected values
    def handle_experiment(self, event):
        self.current_experiment = not event
        self.expected_period = None
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None
        self.expected_pressure_before_pressurize = None
        self.pump_times = []
        self.example_depress_pressures = []
        self.example_press_pressures = []
        self.example_periods = []
        self.last_period_raised_error = False


    # Emits warning if pressure does not increase or pump rate exceeds expected value
    def handle_pump(self, event):
        # Check for increasing pressure when pump strokes are within 1 second of eachother
        if self.last_pump_time is not None and event.event_time - self.last_pump_time < 1:
            if event.get_initial_target() <= self.last_pump_initial_pressure:
                if self.current_experiment:
                    self.error_signal.emit(f"Shutdown: pressure not increasing after pump event at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")
                else:
                    self.warning_signal.emit(f"Warning: pressure not increasing after pump event at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")

        self.last_pump_initial_pressure = event.get_initial_target()
        self.last_pump_time = event.event_time

        if self.current_experiment:
            self.pump_times.append(event.event_time)
            # Define exepected pump rate
            if self.expected_pump_rate is None and len(self.pump_times) == self.example_events:
                avg = np.diff(self.pump_times).mean()
                self.expected_pump_rate = 1 / avg

            # Check for deviation from expected rate (averaged over last example_events)
            if len(self.pump_times) > self.example_events:
                self.pump_times.pop(0)
                pump_rate = 1 / np.diff(self.pump_times).mean()
                rate_percent_increase = (pump_rate - self.expected_pump_rate) / self.expected_pump_rate
                if rate_percent_increase > self.max_pump_rate_increase:
                    self.warning_signal.emit(f"Warning: pump rate at {strftime('%H:%M:%S', localtime(event.event_time))} is {pump_rate:.2f}, which is {rate_percent_increase:.2f}% over the expected rate from the beginning of the experiment. Possible leak.")


    # Emits warning if pressure right before event is decreasing. Possible leak.
    def handle_depressurize(self, event):
        self.last_depressurize_time = event.event_time

        if self.current_experiment:
            initial_pressure = get_channel(event, Channel.HI_PRE_ORIG)[:event.event_index].mean()

            # define expected pressure before depressurize
            if self.expected_pressure_before_depressurize is None:
                self.example_depress_pressures.append(initial_pressure)
                if len(self.example_depress_pressures) == self.example_events:
                    self.expected_pressure_before_depressurize = np.mean(self.example_depress_pressures)

            else:
                percent_decrease = (self.expected_pressure_before_depressurize - initial_pressure) / self.expected_pressure_before_depressurize
                if percent_decrease > self.max_pressure_before_depress_decrease:
                    self.warning_signal.emit(f"Warning: pressure before depressurize event decreasing at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")


    # Emits warning if pressure right before event is increasing. Possible leak.
    def handle_pressurize(self, event):
        # Boolean for whether or not this event is the first pressurize after a depressurize
        is_first_pressurize = (self.last_depressurize_time is not None and
                    (self.last_pressurize_time is None or
                    self.last_pressurize_time <  self.last_depressurize_time))
        self.last_pressurize_time = event.event_time

        # Check only the first pressurize event after depressurize
        if self.current_experiment and is_first_pressurize:
            initial_pressure = get_channel(event, Channel.HI_PRE_ORIG)[:event.event_index].mean()

            # define expected pressure before pressurize
            if self.expected_pressure_before_pressurize is None:
                self.example_press_pressures.append(initial_pressure)
                if len(self.example_press_pressures) == self.example_events:
                    self.expected_pressure_before_pressurize = np.mean(self.example_press_pressures)

            else:
                percent_increase = (initial_pressure - self.expected_pressure_before_pressurize) / self.expected_pressure_before_pressurize
                if percent_increase > self.max_pressure_before_press_increase:
                    self.warning_signal.emit(f"Warning: pressure before pressurize event increasing at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leaky pressurize valve.")


    # Emits warnings when origin pressure deviates from expected value
    def handle_period(self, event):
        if self.current_experiment:
            # Pad array with zeros. Only necessary when period width is less than 600/4000 seconds which should never happen
            padding_width = 600 - event.data.shape[1]
            # Should never happen
            if padding_width < 0:
                raise RuntimeError("Period of length greater than 600")
            if padding_width > 0:
                data = np.pad(event.data, ((0, 0), (0, padding_width)), mode='constant', constant_values=0)

            # Define exepected period
            if self.expected_period is None:
                self.example_periods.append(get_channel(data, Channel.HI_PRE_ORIG))
                if len(self.example_periods) == self.example_events:
                    stacked_data = np.asarray(self.example_periods)
                    self.expected_period = np.mean(stacked_data, axis=0)

            # Check for deviation from expected period
            else:
                diff = np.abs(np.mean(get_channel(data, Channel.HI_PRE_ORIG) - self.expected_period))
                if diff / np.mean(self.expected_period) > self.max_period_presure_difference:
                    self.warning_signal.emit(f"Pressure deviating from expected value at {strftime('%H:%M:%S', localtime(event.event_time))}.")
                    if self.last_period_raised_error:
                        self.error_signal.emit(f"Pressure deviated twice from expected value at {strftime('%H:%M:%S', localtime(event.event_time))}.")
                    self.last_period_raised_error = True
                else:
                    self.last_period_raised_error = False


    # On device disconnect
    def reset(self):
        # Exit experiment mode (argument is value of bit 4 and thus is high for normal operation)
        self.handle_experiment(True)

        # Also reset event times
        self.last_pump_time = None
        self.last_pump_initial_pressure = None
        self.last_depressurize_time = None
        self.last_pressurize_time = None
