import numpy as np
from icarus_v2.backend.event import Event, Channel, get_channel
from PySide6.QtWidgets import QGridLayout, QWidget
from icarus_v2.gui.styled_plot_widget import StyledPlotWidget
from icarus_v2.backend.configuration_manager import ConfigurationManager


class EventPlot(QWidget):
    DISPLAY_CHANNELS = {
        Event.PRESSURIZE: [
            Channel.TARGET,
            Channel.HI_PRE_SAMPLE,
            Channel.HI_PRE_ORIG,
            Channel.DEPRE_VALVE,
            Channel.PRE_VALVE,
            Channel.PRE_LOW,
            Channel.PRE_UP
        ],
        Event.DEPRESSURIZE: [
            Channel.TARGET,
            Channel.HI_PRE_SAMPLE,
            Channel.HI_PRE_ORIG,
            Channel.DEPRE_VALVE,
            Channel.PRE_VALVE,
            Channel.DEPRE_LOW,
            Channel.DEPRE_UP
        ],
        Event.PERIOD: [
            Channel.TARGET,
            Channel.HI_PRE_SAMPLE,
            Channel.HI_PRE_ORIG,
            Channel.DEPRE_VALVE,
            Channel.PRE_VALVE
        ]
    }

    def __init__(self, event_type, parent=None):
        super().__init__(parent=parent)

        self.event_type = event_type
        self.config_manager = ConfigurationManager()
        self.config_manager.settings_updated.connect(self.update_settings)
        self.coefficients = self.config_manager.get_settings("plotting_coefficients")
        self.log_coefficients = None
        self.hide_valve_setting = self.config_manager.get_settings("hide_valve_sensors")

        self.plot = StyledPlotWidget()
        self.plot.setYRange(0, 3)
        self.plot.set_y_label('Pressure (kbar)')

        for channel in self.DISPLAY_CHANNELS[event_type]:
            self.plot.add_line(channel)

        # local statistics functions
        def get_valve_open_time(y_data, srate):
            low_idx = y_data.argmin()
            duration = y_data[low_idx:].argmax()

            # Case where the end of the event is not in the reported data
            if y_data[low_idx + duration] == 0:
                duration = len(y_data) - low_idx

            return duration / srate

        def get_period_width(y_data, srate):
            """
            Periods are defined as the distance between depressurize signals.
            Period events have buffers of 10ms on either side.
            This is a magic number, but it's way easier since period events are down-sampled.
            """
            duration = len(y_data) / srate
            duration -= 10 * 2 / 1000

            return duration

        def get_delay_width(y_data, srate):
            """
            Delay is the time from the depressurize event to pressurize.
            There is a 10ms buffer on the left side of the depressurize event.
            """
            duration = np.argmin(y_data) / srate
            duration -= 10 / 1000

            return  duration

        if event_type == Event.PRESSURIZE:
            self.x_unit = 'ms'
            self.plot.set_title("Pressurize")
            self.plot.add_statistic(Channel.PRE_VALVE, get_valve_open_time, "Valve Open (ms): {:.2f}")
        elif event_type == Event.DEPRESSURIZE:
            self.x_unit = 'ms'
            self.plot.set_title("Depressurize")
            self.plot.add_statistic(Channel.DEPRE_VALVE, get_valve_open_time, "Valve Open (ms): {:.2f}")
        else:
            self.x_unit = 's'
            self.plot.set_title("Period")
            self.plot.add_statistic(Channel.DEPRE_VALVE, get_period_width, "Period (s): {:.2f}")
            self.plot.add_statistic(Channel.PRE_VALVE, get_delay_width, "Delay (s): {:.2f}:")

        self.plot.set_x_label(f'Time ({self.x_unit})')
        self.hide_valve_sensors(self.hide_valve_setting)

        # Set layout
        layout = QGridLayout()
        layout.addWidget(self.plot)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def update_data(self, event):
        if event is None:
            self.plot.reset()
            return

        data = event.data
        # Calculate times based on event.step_time and event_index
        frequency = event.step_time
        if self.x_unit == "s":  # frequencies are in ms by default
            frequency /= 1000
        srate = 1.0 / frequency

        time_before_event = - event.event_index * frequency
        time_after_event = (len(event.data) - event.event_index - 1) * frequency
        times = np.linspace(time_before_event, time_after_event, len(data))

        # update data for each line
        coefficients = self.coefficients if self.log_coefficients is None else self.log_coefficients
        for channel in self.DISPLAY_CHANNELS[self.event_type]:
            y_data = get_channel(data, channel) * coefficients[channel]
            self.plot.update_line_data(channel, times, y_data, srate)

    def update_settings(self, key):
        if key == "plotting_coefficients":
            self.coefficients = self.config_manager.get_settings(key)
        elif key == "hide_valve_sensors":
            self.hide_valve_setting = self.config_manager.get_settings(key)
            self.hide_valve_sensors(self.hide_valve_setting)

    def hide_valve_sensors(self, hide_valve_sensors):
        valve_sensors = [Channel.PRE_LOW, Channel.PRE_UP, Channel.DEPRE_LOW, Channel.DEPRE_UP]
        visible = not hide_valve_sensors

        for channel in valve_sensors:
            self.plot.toggle_line_visibility(channel, visible)

    # Hide the sample sensor if it is disconnected.
    def set_sample_sensor(self, connected):
        self.plot.toggle_line_visibility(Channel.HI_PRE_SAMPLE, connected)

    def set_log_coefficients(self, coefficients):
        self.log_coefficients = coefficients
