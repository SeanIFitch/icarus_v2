import numpy as np
from PySide6.QtCore import QThread, Signal
from Event import get_channel, Channel
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

        # values defined after an experiment starts for defaults
        self.example_depress_pressures = []
        self.pump_times = []
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None

    # Takes boolean representing the new state of bit 4
    # Resets all expected values
    def handle_experiment(self, event):
        self.current_experiment = not event
        self.current_experiment = True
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None
        self.pump_times = []
        self.example_depress_pressures = []
        # update this only here so it is not changed for an ongoing experiment
        self.current_example_events = self.settings['example_events']

    # Emits warning pump rate exceeds expected value
    def handle_pump(self, event):
        if self.current_experiment:
            self.pump_times.append(event.event_time)
            # Define expected pump rate
            if self.expected_pump_rate is None and len(self.pump_times) == self.current_example_events:
                avg = np.diff(self.pump_times).mean()
                self.expected_pump_rate = 1 / avg

            # Check for deviation from expected rate (averaged over last example_events)
            if len(self.pump_times) > self.current_example_events:
                self.pump_times.pop(0)
                pump_rate = 1 / np.diff(self.pump_times).mean()
                rate_percent_increase = (pump_rate - self.expected_pump_rate) / self.expected_pump_rate
                if rate_percent_increase > self.settings["max_pump_rate_increase"]:
                    self.warning_signal.emit(
                        f"Warning: pump rate at {strftime('%H:%M:%S', localtime(event.event_time))} is "
                        f"{pump_rate:.2f}, which is {rate_percent_increase:.2f}% over the expected rate from the "
                        "beginning of the experiment. Possible leak.")

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
                    self.error_signal.emit(
                        f"Error: pressure decreasing at "
                        f"{strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")
                elif percent_change > self.settings["max_pressure_before_depress_increase"]:
                    self.warning_signal.emit(
                        f"Error: pressure increasing at "
                        f"{strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")


    # On device disconnect
    def reset(self):
        # Exit experiment mode (argument is value of bit 4 and thus is high for normal operation)
        self.handle_experiment(True)

    def update_settings(self, key='timing_settings'):
        if key == 'sentry_settings':
            self.settings = self.config_manager.get_settings(key)
