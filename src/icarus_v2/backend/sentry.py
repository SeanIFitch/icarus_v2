import numpy as np
from PySide6.QtCore import QThread, Signal
from icarus_v2.backend.event import get_channel, Channel
from time import localtime, strftime

# Gets expected values for the experiment checks from the first example_events events of an experiment
class Sentry(QThread):
    warning_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.settings = config_manager.get_settings('sentry_settings')
        self.config_manager.settings_updated.connect(self.update_settings)
        self.current_example_events = None

        self.current_experiment = False
        self.last_error_time = -10
        self.suppress_errors = 2  # suppress errors for 2 seconds after one error

        # values defined after an experiment starts for defaults
        self.example_depress_pressures = []
        self.example_pump_times = [] # last example_events stroke times
        self.recent_pump_times = [] # all times within pump_window
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None
        self.num_pressure_decreases = 0

    # Takes boolean representing the new state of bit 4
    # Resets all expected values
    def handle_experiment(self, event):
        self.current_experiment = not event
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None
        self.example_pump_times = []
        self.recent_pump_times = []
        self.example_depress_pressures = []
        self.num_pressure_decreases = 0
        self.last_error_time = -10
        # update this only here so it is not changed for an ongoing experiment
        self.current_example_events = self.settings['example_events']

    def handle_pump(self, event):
        if self.current_experiment:
            self.example_pump_times.append(event.event_time)
            # Define expected pump rate
            if self.expected_pump_rate is None and len(self.example_pump_times) == self.current_example_events:
                avg = np.diff(self.example_pump_times).mean()
                self.expected_pump_rate = 1 / avg

            # Check for deviation from expected rate (averaged over last example_events)
            if len(self.example_pump_times) > self.current_example_events:
                self.example_pump_times.pop(0)
                pump_rate = 1 / np.diff(self.example_pump_times).mean()
                rate_percent_increase = (pump_rate - self.expected_pump_rate) / self.expected_pump_rate
                if event.event_time - self.last_error_time > self.suppress_errors:
                    if rate_percent_increase > self.settings["max_pump_rate_increase"]:
                        self.warning_signal.emit(
                            f"Warning: pump rate at {strftime('%H:%M:%S', localtime(event.event_time))} is "
                            f"{pump_rate:.2f}, which is {rate_percent_increase:.2f}% over the expected rate from the "
                            "beginning of the experiment. Possible leak.")

            # check for max_pumps within pump_window
            self.recent_pump_times.append(event.event_time)
            self.recent_pump_times = [t for t in self.recent_pump_times if t > event.event_time - self.settings["pump_window"]]
            if event.event_time - self.last_error_time > self.suppress_errors:
                if len(self.recent_pump_times) > self.settings["max_pumps_in_window"]:
                    self.error_signal.emit(
                        f"Error: {len(self.recent_pump_times)} pump strokes occurred within {self.settings['pump_window']} seconds.")
                    self.last_error_time = event.event_time

    def handle_depressurize(self, event):
        if self.current_experiment:
            initial_pressure = get_channel(event, Channel.HI_PRE_ORIG)[:event.event_index].mean()

            # define expected pressure before depressurize
            if self.expected_pressure_before_depressurize is None:
                self.example_depress_pressures.append(initial_pressure)
                if len(self.example_depress_pressures) == self.current_example_events:
                    self.expected_pressure_before_depressurize = np.mean(self.example_depress_pressures)

            else:
                percent_change = ((initial_pressure - self.expected_pressure_before_depressurize) /
                                    self.expected_pressure_before_depressurize)
                if percent_change < - self.settings["max_pressure_before_depress_decrease"]:
                    self.num_pressure_decreases += 1
                    if event.event_time - self.last_error_time > self.suppress_errors:
                        if self.num_pressure_decreases >= self.settings["decrease_count_to_error"]:
                            self.error_signal.emit(
                                f"Error: pressure decreased {self.num_pressure_decreases} times in a row at "
                                f"{strftime('%H:%M:%S', localtime(event.event_time))}. Likely leak")
                            self.last_error_time = event.event_time
                        else:
                            self.warning_signal.emit(
                                f"Warning: pressure decreasing at "
                                f"{strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")
                else:
                    self.num_pressure_decreases = 0

                if event.event_time - self.last_error_time > self.suppress_errors:
                    if percent_change > self.settings["max_pressure_before_depress_increase"]:
                        self.warning_signal.emit(
                            f"Warning: pressure increasing at "
                            f"{strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")

    # On device disconnect
    def reset(self):
        # Exit experiment mode (argument is value of bit 4 and thus is high for normal operation)
        self.handle_experiment(True)

    def update_settings(self, key='sentry_settings'):
        if key == 'sentry_settings':
            self.settings = self.config_manager.get_settings(key)
