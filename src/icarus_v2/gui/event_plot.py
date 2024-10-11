from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from icarus_v2.backend.event import Event, Channel, get_channel
from PySide6.QtWidgets import QLabel, QGridLayout, QWidget, QSpacerItem, QSizePolicy
from icarus_v2.gui.styled_plot_widget import StyledPlotWidget


class EventPlot(QWidget):
    # Dictionary of color to plot each channel
    LINE_STYLES = {
        Channel.TARGET: ('#45BF55', Qt.SolidLine),          # light green
        Channel.DEPRE_LOW: ('#AB47BC', Qt.SolidLine),       # magenta
        Channel.DEPRE_UP: ('#004B8D', Qt.SolidLine),        # blue
        Channel.PRE_LOW: ('#AB47BC', Qt.SolidLine),         # magenta
        Channel.PRE_UP: ('#004B8D', Qt.SolidLine),          # blue
        Channel.HI_PRE_ORIG: ('#FFDC00', Qt.SolidLine),     # yellow
        Channel.HI_PRE_SAMPLE: ('#FFDC00', Qt.DashLine),    # yellow dashed
        Channel.DEPRE_VALVE: ('#59D8E6', Qt.SolidLine),     # cyan
        Channel.PRE_VALVE: ('#B9121B', Qt.SolidLine),       # red
    }

    def __init__(self, event_type, config_manager, parent=None):
        super().__init__(parent=parent)

        self.event_type = event_type
        self.config_manager = config_manager
        self.config_manager.settings_updated.connect(self.update_settings)
        self.coefficients = config_manager.get_settings("plotting_coefficients")
        self.log_coefficients = None
        self.hide_valve_setting = config_manager.get_settings("hide_valve_sensors")
        self.hide_sample_sensor = False
        display_channels = [
            Channel.TARGET, Channel.HI_PRE_SAMPLE, Channel.HI_PRE_ORIG, Channel.DEPRE_VALVE, Channel.PRE_VALVE
        ]

        if event_type == Event.PRESSURIZE:
            display_channels += [Channel.PRE_LOW, Channel.PRE_UP]
            self.x_unit = 'ms'
            title = "Pressurize"
        elif event_type == Event.DEPRESSURIZE:
            display_channels += [Channel.DEPRE_LOW, Channel.DEPRE_UP]
            self.x_unit = 'ms'
            title = "Depressurize"
        else:
            self.x_unit = 's'
            title = "Period"

        self.plot = StyledPlotWidget()
        self.plot.setYRange(0, 3)
        self.plot.set_title(title)
        self.plot.set_y_label('Pressure (kbar)')
        self.plot.set_x_label(f'Time ({self.x_unit})')
        self.width_display = None
        self.period_display = None
        self.delay_display = None
        self.mouse_label = None
        self.proxy = None

        # Create a dictionary of lines for each channel listed in display_channels
        self.line_references = {}
        self.line_currently_shown = {}
        for channel in display_channels:
            style = self.LINE_STYLES[channel]
            pen = pg.mkPen(color=style[0], style=style[1])
            self.line_references[channel] = self.plot.plot([], [], pen=pen)
            self.line_currently_shown[channel] = True

        labels = self.init_labels()
        self.hide_valve_sensors(self.hide_valve_setting)

        # Set layout
        layout = QGridLayout()
        layout.addWidget(self.plot, 0, 0)
        layout.addLayout(labels, 0, 0, Qt.AlignRight | Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def init_labels(self):
        layout = QGridLayout()
        press_color = self.LINE_STYLES[Channel.PRE_VALVE][0]
        depress_color = self.LINE_STYLES[Channel.DEPRE_VALVE][0]
        size = 14
        if self.event_type == Event.PRESSURIZE or self.event_type == Event.DEPRESSURIZE:
            color = press_color if self.event_type == Event.PRESSURIZE else depress_color
            self.width_display = QLabel("0.00")
            label = QLabel("Valve Open (ms):")
            self.width_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
            label.setStyleSheet(f"color: {color}; font-size: {size}px;")
            layout.addWidget(label, 0, 0)
            layout.addWidget(self.width_display, 0, 1)

        elif self.event_type == Event.PERIOD:
            self.period_display = QLabel("0")
            self.delay_display = QLabel("0")
            period_label = QLabel("Period (s):")
            delay_label = QLabel("Delay (s):")
            self.period_display.setStyleSheet(f"color: {depress_color}; font-size: {size}px;")
            self.delay_display.setStyleSheet(f"color: {press_color}; font-size: {size}px;")
            period_label.setStyleSheet(f"color: {depress_color}; font-size: {size}px;")
            delay_label.setStyleSheet(f"color: {press_color}; font-size: {size}px;")
            layout.addWidget(period_label, 0, 0)
            layout.addWidget(delay_label, 1, 0)
            layout.addWidget(self.period_display, 0, 1)
            layout.addWidget(self.delay_display, 1, 1)

        # Mouse position label
        spacer = QSpacerItem(0, 0, QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.mouse_label = QLabel("")
        self.mouse_label.setStyleSheet(f"font-size: {size}px;")
        # Limit rate of mouseMoved signal to 60 Hz
        self.proxy = pg.SignalProxy(self.plot.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)
        layout.addItem(spacer, 2, 0)
        layout.addWidget(self.mouse_label, 3, 0, 1, 2, Qt.AlignRight | Qt.AlignBottom)

        layout.setContentsMargins(0, 35, 5, 45)
        return layout

    def update_data(self, event):
        if event is None:
            self.reset_history()
            return

        data = event.data
        # Calculate times based on event.step_time and event_index
        time_before_event = - event.event_index * event.step_time
        time_after_event = (len(event.data) - event.event_index - 1) * event.step_time
        times = np.linspace(time_before_event, time_after_event, len(data))
        if self.x_unit == "s":
            times /= 1000

        # update data for each line
        coefficients = self.coefficients if self.log_coefficients is None else self.log_coefficients
        for channel, line_reference in self.line_references.items():
            coefficient = coefficients[channel]
            line_reference.setData(times, get_channel(data, channel) * coefficient)

        # Update timings labels
        if event.event_type == Event.PRESSURIZE or event.event_type == Event.DEPRESSURIZE:
            width = event.get_valve_open_time() / 4
            self.width_display.setText(f"{width:.2f}")

        elif event.event_type == Event.PERIOD:
            period_width = event.get_period_width() / 4000
            delay_width = event.get_delay_width() / 4000
            self.period_display.setText(f"{period_width:.2f}")
            self.delay_display.setText(f"{delay_width:.2f}")

    def update_settings(self, key):
        if key == "plotting_coefficients":
            self.coefficients = self.config_manager.get_settings(key)
        elif key == "hide_valve_sensors":
            self.hide_valve_setting = self.config_manager.get_settings(key)
            self.hide_valve_sensors(self.hide_valve_setting)

    def reset_history(self):
        for line_reference in self.line_references.values():
            line_reference.setData([], [])

    def mouse_moved(self, event):
        mouse_point = self.plot.getViewBox().mapSceneToView(event[0])
        view_range = self.plot.getViewBox().viewRange()

        # Check if the mouse point is within the view range
        if (view_range[0][0] <= mouse_point.x() <= 0.98 * view_range[0][1] and
                view_range[1][0] <= mouse_point.y() <= view_range[1][1]):
            self.mouse_label.setText(f"{mouse_point.x():.2f}, {mouse_point.y():.2f}")
        else:
            self.mouse_label.setText("")

    def hide_valve_sensors(self, hide_valve_sensors):
        if self.event_type == Event.PRESSURIZE:
            valve_sensors = [Channel.PRE_LOW, Channel.PRE_UP]
        elif self.event_type == Event.DEPRESSURIZE:
            valve_sensors = [Channel.DEPRE_LOW, Channel.DEPRE_UP]
        else:
            valve_sensors = []

        if hide_valve_sensors:
            for channel in valve_sensors:
                if self.line_currently_shown[channel]:
                    self.plot.removeItem(self.line_references[channel])
                    self.line_currently_shown[channel] = False
        else:
            for channel in valve_sensors:
                if not self.line_currently_shown[channel]:
                    self.plot.addItem(self.line_references[channel])
                    self.line_currently_shown[channel] = True

    def set_sample_sensor(self, connected):
        if not connected and not self.hide_sample_sensor:
            self.plot.removeItem(self.line_references[Channel.HI_PRE_SAMPLE])
            self.hide_sample_sensor = True
        elif connected and self.hide_sample_sensor:
            self.plot.addItem(self.line_references[Channel.HI_PRE_SAMPLE])
            self.hide_sample_sensor = False

    def set_log_coefficients(self, coefficients):
        self.log_coefficients = coefficients
