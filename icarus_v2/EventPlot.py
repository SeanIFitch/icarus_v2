from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from Channel import Channel, get_channel
from Event import Event


class EventPlot(pg.PlotWidget):
    # Dictionary of color to plot each channel
    CHANNEL_COLORS = {
        Channel.TARGET: '#45BF55',        # light green
        Channel.DEPRE_LOW: '#AB47BC',     # magenta
        Channel.DEPRE_UP: '#004B8D',      # blue
        Channel.PRE_LOW: '#AB47BC',       # magenta
        Channel.PRE_UP: '#004B8D',        # blue
        Channel.HI_PRE_ORIG: '#FFDC00',   # yellow
        Channel.HI_PRE_SAMPLE: '#FFDC00', # yellow
        Channel.PUMP: None,               # N/A
        Channel.DEPRE_VALVE: '#59D8E6',   # cyan
        Channel.PRE_VALVE: '#B9121B',     # red
        Channel.LOG: None                 # N/A
    }

    # Dictionary of coefficient to apply when plotting each channel
    CHANNEL_COEFFICIENTS = {
        Channel.TARGET: 0.2,
        Channel.DEPRE_LOW: 0.1,
        Channel.DEPRE_UP: 0.1,
        Channel.PRE_LOW: 0.1,
        Channel.PRE_UP: 0.1,
        Channel.HI_PRE_ORIG: 0.2,
        Channel.HI_PRE_SAMPLE: 0.2,
        Channel.PUMP: 2000,
        Channel.DEPRE_VALVE: 2000,
        Channel.PRE_VALVE: 2000,
        Channel.LOG: 2000
    }

    def __init__(self, event_type, display_offset):
        super().__init__()

        if event_type == Event.PRESSURIZE:
            display_channels = [Channel.TARGET, Channel.PRE_LOW, Channel.PRE_UP, Channel.HI_PRE_SAMPLE, Channel.HI_PRE_ORIG, Channel.DEPRE_VALVE, Channel.PRE_VALVE]
            self.x_unit = 'ms'
            title = "Pressurize"
        elif event_type == Event.DEPRESSURIZE:
            display_channels = [Channel.TARGET, Channel.DEPRE_LOW, Channel.DEPRE_UP, Channel.HI_PRE_SAMPLE, Channel.HI_PRE_ORIG, Channel.DEPRE_VALVE, Channel.PRE_VALVE]
            self.x_unit = 'ms'
            title = "Depressurize"
        elif event_type == Event.PERIOD:
            display_channels = [Channel.TARGET, Channel.HI_PRE_SAMPLE, Channel.HI_PRE_ORIG, Channel.DEPRE_VALVE, Channel.PRE_VALVE]
            self.x_unit = 's'
            title = "Period"

        # Amount of time in ms to offset x axis. t=0 should be the event occurence.
        self.display_offset = display_offset

        window_color = self.palette().color(QPalette.Window)
        text_color = self.palette().color(QPalette.WindowText)
        self.setBackground(window_color)

        self.setTitle(title, color=text_color, size="14pt")
        self.showGrid(x=True, y=True)
        #self.setYRange(-6, 12, padding=0)
        self.setMouseEnabled(x=False, y=False) # Prevent zooming
        self.hideButtons() # Remove autoScale button

        # Axis Labels
        styles = {'color':text_color}
        self.setLabel('left', 'Pressure (kbar)', **styles)
        self.setLabel('bottom', f'Time ({self.x_unit})', **styles)

        dummy_x = [-10,140]
        dummy_y = [0,0]

        # Create a dictionary of lines for each channel listed in display_channels
        self.line_references = {}
        for channel in display_channels:
            color = self.CHANNEL_COLORS[channel]
            if channel == Channel.HI_PRE_SAMPLE:
                 self.line_references[channel] = self.plot_line(dummy_x, dummy_y, color, Qt.DashLine)
            else:
                 self.line_references[channel] = self.plot_line(dummy_x, dummy_y, color)


    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate


    def update_data(self, event):
        data = event.data
        # Calculate times based on time before event, length of data, and sample rate
        indeces = np.asarray(range(len(data)))
        if self.x_unit == "ms":
            sample_rate_kHz = float(self.sample_rate) / 1000 # Hz to kHz
            times = (indeces / sample_rate_kHz) - self.display_offset
        elif self.x_unit == "s":
            offset_sec = float(self.display_offset) / 1000 # ms to s
            times = (indeces / self.sample_rate) - offset_sec

        # update data for each line
        for channel, line_reference in self.line_references.items():
            coefficient = self.CHANNEL_COEFFICIENTS[channel]
            line_reference.setData(times, get_channel(data, channel) * coefficient)


    def plot_line(self, x, y, color, style = Qt.SolidLine):
        pen = pg.mkPen(color=color, style=style)
        return self.plot(x, y, pen=pen)
