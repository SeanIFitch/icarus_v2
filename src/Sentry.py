import numpy as np
from PySide6.QtCore import QThread, Signal
from Event import get_channel, Channel
from time import localtime, strftime


class Sentry(QThread):
    warning_signal = Signal(str)
    error_signal = Signal(str)


    def __init__(self):
        super().__init__()
        # Number of events with which to define expected values
        self.example_events = 10
        # Max percent difference between expected and actual period
        '''self.max_period_diff = {
            Channel.TARGET: 0.25,
            Channel.DEPRE_LOW: 0.25,
            Channel.DEPRE_UP: 0.25,
            Channel.PRE_LOW: 0.25,
            Channel.PRE_UP: 0.25,
            Channel.HI_PRE_ORIG: 0.25,
            Channel.HI_PRE_SAMPLE: 0.25,
            Channel.DEPRE_VALVE: 0.25,
            Channel.PRE_VALVE: 0.25,
        }'''
        self.max_pump_rate_increase = 0.25
        self.max_pressure_before_depress_decrease = 0.1
        self.max_pressure_before_press_increase = 0.1

        self.current_experiment = False

        #self.example_periods = []
        self.example_depress_pressures = []
        self.example_press_pressures = []
        self.pump_times = []
        self.last_pump_time = None
        self.last_pump_initial_pressure = None
        self.last_depressurize_time = None
        self.last_pressurize_time = None

        #self.expected_period = None
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None
        self.expected_pressure_before_pressurize = None


    # Takes boolean representing the new state of bit 4
    # Resets all expected values
    def handle_experiment(self, event):
        self.current_experiment = not event
        self.current_experiment = True
        self.expected_period = None
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None
        self.expected_pressure_before_pressurize = None
        self.pump_times = []
        self.example_depress_pressures = []
        self.example_press_pressures = []
        self.example_periods = []


    # Emits warning if pressure does not increase or pump rate exceeds expected value
    def handle_pump(self, event):
        # Check for increasing pressure when pump strokes are within 1 second of eachother
        if self.last_pump_time is not None and event.event_time - self.last_pump_time < 1:
            if event.get_initial_target() <= self.last_pump_initial_pressure:
                self.warning_signal.emit(f"Warning: pressure not increasing after pump event at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")

        self.last_pump_initial_pressure = event.get_initial_target()
        self.last_pump_time = event.event_time

        if not self.current_experiment:
            return

        self.pump_times.append(event.event_time)
        # Define exepected pump rate
        if self.expected_pump_rate is None and len(self.pump_times) == self.example_events:
            avg = np.diff(self.pump_times).mean()
            self.expected_pump_rate = 1 / avg

        # Check for deviation from expected rate
        if len(self.pump_times) > self.example_events:
            self.pump_times.pop(0)
            pump_rate = 1 / np.diff(self.pump_times).mean()
            rate_percent_increase = (pump_rate - self.expected_pump_rate) / self.expected_pump_rate
            if rate_percent_increase > self.max_pump_rate_increase:
                self.warning_signal.emit(f"Warning: pump rate at {strftime('%H:%M:%S', localtime(event.event_time))} is {pump_rate:.2f}, which is {rate_percent_increase:.2f} over the expected rate from the beginning of the experiment. Possible leak.")


    # Emits warning if pressure at beginning is decreasing. Possible leak.
    def handle_depressurize(self, event):
        self.last_depressurize_time = event.event_time

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


    # Emits warning if pressure at beginning is increasing. Possible leak.
    def handle_pressurize(self, event):
        # Check only the first pressurize event after depressurize
        if (self.last_depressurize_time is not None and
                self.last_pressurize_time is not None and
                self.last_pressurize_time >  self.last_depressurize_time
            ):
            return
        self.last_pressurize_time = event.event_time

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


    def reset(self):
        self.current_experiment = False

        #self.example_periods = []
        self.example_depress_pressures = []
        self.example_press_pressures = []
        self.pump_times = []
        self.last_pump_time = None
        self.last_pump_initial_pressure = None
        self.last_depressurize_time = None
        self.last_pressurize_time = None

        #self.expected_period = None
        self.expected_pump_rate = None
        self.expected_pressure_before_depressurize = None
        self.expected_pressure_before_pressurize = None

    '''
    # TODO: warn on unexpected sudden pressure change
    def handle_pressure(self, event):
        pass


    # Emits warnings when period deviates from expected value
    # TODO: implement outlier rejection
    def handle_period(self, event):
        return
        if not self.current_experiment:
            return

        # Pad array with zeros. Only necessary when period width is less than 600/4000 seconds which shouldnt ever happen
        padding_width = 600 - event.data.shape[1]
        if padding_width < 0:
            raise RuntimeError("Period of length greater than 600")
        if padding_width > 0:
            data = np.pad(event.data, ((0, 0), (0, padding_width)), mode='constant', constant_values=0)

        # Define exepected period
        if self.expected_period is None:
            self.example_periods.append(data)
            if len(self.example_periods) == self.example_events:
                stacked_data = np.asarray(self.example_periods)
                self.expected_period = np.mean(stacked_data, axis=0)

                # Digital should be mode
                #find unique values in array along with their counts
                vals, counts = np.unique(stacked_data[:,:,-1], axis=0, return_counts=True)
                mode = vals[np.argmax(counts, axis=0)]
                self.expected_period[:,-1] = mode

        # Check for deviation from expected period
        else:
            deviated_channels = []
            data_diff = np.abs(data - self.expected_period)
            for channel, max_difference in self.max_period_diff.items():
                avg_difference = np.mean(get_channel(data_diff, channel) )
                avg = np.mean(get_channel(self.expected_period, channel))
                if avg_difference / avg > max_difference:
                    deviated_channels.append(channel)
            if len(deviated_channels) > 0:
                self.warning_signal.emit(f"Warning: period deviating from expected value in channels {deviated_channels} at {strftime('%H:%M:%S', localtime(event.event_time))}.")
    '''