from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np


class EventPlot(pg.PlotWidget):
    # Dictionary of color to plot each channel
    CHANNEL_COLORS = {
        'target': '#FFDC00',        # yellow
        'depre_low': '#FF5252',     # salmon
        'depre_up': '#B9121B',      # red
        'pre_low': '#289976',       # cyan
        'pre_up': '#004B8D',        # dark blue
        'hi_pre_orig': '#732DD9',   # purple
        'hi_pre_sample': '#AB47BC', # magenta
        'pump': '#45BF55',          # light green
        'depre_valve': '#FD7400',   # orange
        'pre_valve': '#59D8E6',     # light blue
        'log': '#374140'            # gray
    }

    # Dictionary of coefficient to apply when plotting each channel
    CHANNEL_COEFFICIENTS = {
        'target': 0.2,
        'depre_low': 0.1,
        'depre_up': 0.1,
        'pre_low': 0.1,
        'pre_up': 0.1,
        'hi_pre_orig': 0.2,
        'hi_pre_sample': 0.2,
        'pump': 10,
        'depre_valve': 10.1,
        'pre_valve': 10.2,
        'log': 10.3
    }

    def __init__(self, display_channels, display_offset, title, x_unit = "ms", parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)

        # Amount of time in ms to offset x axis. t=0 should be the event occurence.
        self.display_offset = display_offset
        # Unit for x-axis
        self.x_unit = x_unit

        window_color = self.palette().color(QPalette.Window)
        text_color = self.palette().color(QPalette.WindowText)
        self.setBackground(window_color)

        self.setTitle(title, color=text_color, size="14pt")
        self.showGrid(x=True, y=True)
        self.setYRange(-6, 12, padding=0)
        self.setMouseEnabled(x=False, y=False) # Prevent zooming
        self.hideButtons() # Remove autoScale button

        # Axis Labels
        styles = {'color':text_color}
        self.setLabel('left', 'Pressure (kbar)', **styles)
        self.setLabel('bottom', f'Time ({x_unit})', **styles)

        dummy_x = [-10,140]
        dummy_y = [0,0]

        # Create a dictionary of lines for each channel listed in display_channels
        self.line_references = {}
        for channel in display_channels:
            color = self.CHANNEL_COLORS[channel]
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
            line_reference.setData(times, data[channel] * coefficient)


    def plot_line(self, x, y, color, style = Qt.SolidLine):
        pen = pg.mkPen(color=color, style=style)
        return self.plot(x, y, pen=pen)
