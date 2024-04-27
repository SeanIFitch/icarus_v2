from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from Channel import Channel, get_channel
from Event import Event
from PySide6.QtWidgets import QLabel, QGridLayout, QWidget


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


    def __init__(self, event_type, config_manager):
        super().__init__()

        self.event_type = event_type
        self.config_manager = config_manager
        self.config_manager.settings_updated.connect(self.update_settings)
        self.coefficients = config_manager.get_settings("plotting_coefficients")
        display_channels = [Channel.TARGET, Channel.HI_PRE_SAMPLE, Channel.HI_PRE_ORIG, Channel.DEPRE_VALVE, Channel.PRE_VALVE]

        if event_type == Event.PRESSURIZE:
            display_channels += [Channel.PRE_LOW, Channel.PRE_UP]
            self.x_unit = 'ms'
            title = "Pressurize"
            #self.plot.setXRange(-10, 140)
        elif event_type == Event.DEPRESSURIZE:
            display_channels += [Channel.DEPRE_LOW, Channel.DEPRE_UP]
            self.x_unit = 'ms'
            title = "Depressurize"
            #self.plot.setXRange(-10, 140)
        elif event_type == Event.PERIOD:
            self.x_unit = 's'
            title = "Period"


        self.plot = pg.PlotWidget(background= self.palette().color(QPalette.Window))
        self.plot.showGrid(x=True, y=True)
        #self.setYRange(0, 3)
        self.plot.setMouseEnabled(x=False, y=False) # Prevent zooming
        self.plot.hideButtons() # Remove autoScale button
        # Labels
        text_color = self.palette().color(QPalette.WindowText)
        self.plot.setTitle(title, color=text_color, size="14pt")
        self.plot.setLabel('left', 'Pressure (kbar)', **{'color':text_color})
        self.plot.setLabel('bottom', f'Time ({self.x_unit})', **{'color':text_color})

        # Create a dictionary of lines for each channel listed in display_channels
        self.line_references = {}
        for channel in display_channels:
            style = self.LINE_STYLES[channel]
            pen = pg.mkPen(color=style[0], style=style[1])
            self.line_references[channel] = self.plot.plot([], [], pen=pen)

        labels = self.init_labels()

        # Set layout
        layout = QGridLayout()
        layout.addWidget(self.plot, 0, 0)
        layout.addLayout(labels, 0, 0, Qt.AlignRight | Qt.AlignTop)
        self.setLayout(layout)


    def init_labels(self):
        layout = QGridLayout()
        press_color = self.LINE_STYLES[Channel.PRE_VALVE][0]
        depress_color = self.LINE_STYLES[Channel.DEPRE_VALVE][0]
        size = 11
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

        layout.setContentsMargins(0, 35, 5, 0)
        return layout


    def update_data(self, event):
        data = event.data
        # Calculate times based on event.data_end_time and event_index
        time_before_event = - event.data_end_time * event.event_index / (len(data) - event.event_index)
        times = np.linspace(time_before_event, event.data_end_time, len(data))
        if self.x_unit == "s":
            times /= 1000

        # update data for each line
        for channel, line_reference in self.line_references.items():
            coefficient = self.coefficients[channel]
            line_reference.setData(times, get_channel(data, channel) * coefficient)

        # Update timings labels
        if event.event_type == Event.PRESSURIZE or event.event_type == Event.DEPRESSURIZE:
            width = event.get_valve_open_time() / 4
            self.width_display.setText(f"{width:.2f}")

        elif event.event_type == Event.PERIOD:
            period_width = event.get_period_width()
            delay_width = event.get_delay_width()
            self.period_display.setText(f"{period_width:.2f}")
            self.delay_display.setText(f"{delay_width:.2f}")


    def update_settings(self, key):
        if key == "plotting_coefficients":
            self.coefficients = self.config_manager.get_settings(key)
