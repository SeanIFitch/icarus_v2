import numpy as np
from PySide6.QtCore import QThread, Signal
from Event import get_channel, gaussian_filter, Channel
from time import localtime, strftime, time, sleep


class Sentry(QThread):
    warning_signal = Signal(str)
    error_signal = Signal(str)


    def __init__(self):
        super().__init__()
        self.max_switch_time = 50 # ms
        self.sample_rate = 4000
        # Number of events with which to define expected values
        self.num_example_periods = 2
        self.example_pumps = 10
        # Max percent difference between expected and actual period
        self.max_difference = {
            Channel.TARGET: 0.25,
            Channel.DEPRE_LOW: 0.25,
            Channel.DEPRE_UP: 0.25,
            Channel.PRE_LOW: 0.25,
            Channel.PRE_UP: 0.25,
            Channel.HI_PRE_ORIG: 0.25,
            Channel.HI_PRE_SAMPLE: 0.25,
            Channel.DEPRE_VALVE: 0.25,
            Channel.PRE_VALVE: 0.25,
        }
        self.max_pump_rate_increase = 0.25

        self.current_experiment = False
        self.example_periods = []

        self.last_pressurize_time = None
        self.last_depressurize_time = None
        self.expected_period = None
        self.expected_pump_rate = None
        self.pump_times = []


    def run(self):
        self.running = True
        while self.running:
            if not self.no_hang_sleep(time() + 1):
                break


    # Takes boolean representing the new state of bit 4
    # Resets all expected values
    def handle_experiment(self, event):
        self.current_experiment = not event
        #self.current_experiment = True
        self.expected_period = None
        self.expected_pump_rate = None
        self.pump_times = []
        self.example_periods = []


    # Emits warnings when period deviates from expected value
    # TODO: implement outlier rejection
    def handle_period(self, event):
        if not self.current_experiment:
            return

        # Pad array with zeros. Only necessary when period width is less than 600/4000 seconds
        padding_width = 600 - event.data.shape[1]
        if padding_width < 0:
            raise RuntimeError("Period of length greater than 600")
        if padding_width > 0:
            data = np.pad(event.data, ((0, 0), (0, padding_width)), mode='constant', constant_values=0)

        # Define exepected period
        if self.expected_period is None:
            self.example_periods.append(data)
            if len(self.example_periods) == self.num_example_periods:
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
            for channel, max_difference in self.max_difference.items():
                avg_difference = np.mean(get_channel(data_diff, channel) )
                avg = np.mean(get_channel(self.expected_period, channel))
                if avg_difference / avg > max_difference:
                    deviated_channels.append(channel)
            if len(deviated_channels) > 0:
                self.warning_signal.emit(f"Warning: period deviating from expected value in channels {deviated_channels} at {strftime('%H:%M:%S', localtime(event.event_time))}.")


    # Emits warning if pressure does not increase or pump rate exceeds expected value
    def handle_pump(self, event):
        # Check for increasing pressure
        target = get_channel(event.data, Channel.TARGET)
        before_pump = target[:event.event_index]
        after_pump = target[event.event_index:]
        high_avg_before = np.mean(np.sort(before_pump)[int(-0.1*len(before_pump)):])
        high_avg_after = np.mean(np.sort(after_pump)[int(-0.1*len(after_pump)):])
        if high_avg_after < high_avg_before:
            self.warning_signal.emit(f"Warning: pressure not increasing after pump event at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")

        if not self.current_experiment:
            return

        self.pump_times.append(event.event_time)
        # Define exepected pump rate
        if self.expected_pump_rate is None and len(self.pump_times) == self.example_pumps:
            avg = np.diff(self.pump_times).mean()
            self.expected_pump_rate = 1 / avg

        # Check for deviation from expected rate
        if len(self.pump_times) > self.example_pumps:
            self.pump_times.pop(0)
            if 1 / np.diff(self.pump_times).mean() - self.expected_pump_rate > self.max_pump_rate_increase * self.expected_pump_rate:
                self.warning_signal.emit(f"Warning: pump rate exceeding expected value at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leak.")


    # Emits warning if pressure increases after the min # TODO NEEDS HANDLING FOR INCREASE AFTER CLOSE EVENTS
    # TODO: warn if presure decreases below expected
    def handle_depressurize(self, event):
        self.last_depressurize_time = event.event_time

        y = get_channel(event, Channel.HI_PRE_ORIG)
        check_after = np.argmin(y) + 30
        if check_after < len(y):
            y = y[np.argmin(y) + 30:]

            # Calculate the first derivative of the data
            dy = np.diff(y)
            dy_smoothed = gaussian_filter(dy, 5, 5)

            if max(dy_smoothed) > 0:
                self.warning_signal.emit(f"Warning: pressure continuing to increase after depressurize event at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leaky pressurize valve.")


    # Emits warning if pressure increases after the max # TODO NEEDS HANDLING FOR INCREASE AFTER CLOSE EVENTS
    # TODO: warn if presure decreases below expected
    def handle_pressurize(self, event):
        self.last_pressurize_time = event.event_time

        y = get_channel(event, Channel.HI_PRE_ORIG)
        check_after = np.argmax(y) + 30
        if check_after < len(y):
            y = y[np.argmax(y) + 30:]

            # Calculate the first derivative of the data
            dy = np.diff(y)
            dy_smoothed = gaussian_filter(dy, 5, 5)

            if max(dy_smoothed) > 0:
                self.warning_signal.emit(f"Warning: pressure continuing to increase after pressurize event at {strftime('%H:%M:%S', localtime(event.event_time))}. Possible leaky pressurize valve.")


    # TODO: warn on unexpected sudden pressure change
    def handle_pressure(self, event):
        pass


    # Sleep until end_time, checking for self.pulsing frequently
    # Returns False if self.running becomes false, true otherwise
    def no_hang_sleep(self, end_time, running_check_hz = 10):
        remaining_time = end_time - time()
        while remaining_time >= 0:
            sleep_time = min(1 / running_check_hz, remaining_time)
            sleep(sleep_time)
            remaining_time = end_time - time()

            if not self.running:
                return False
        return True


    def quit(self):
        self.running = False
