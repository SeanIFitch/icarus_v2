from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from time import time


class PressurePlot(pg.PlotWidget):
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
        'hi_pre_orig': 1.,
        'hi_pre_sample': 1.,
        'pump': 10,
        'depre_valve': 10.1,
        'pre_valve': 10.2,
        'log': 10.3
    }

    def __init__(self, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)

        self.setup_plot()
        self.setup_lines()


    def setup_plot(self):
        window_color = self.palette().color(QPalette.Window)
        text_color = self.palette().color(QPalette.WindowText)
        self.setBackground(window_color)
        self.setTitle("Pressure", color=text_color, size="14pt")
        self.showGrid(x=True, y=True)
        self.setYRange(0, 3, padding=0)
        self.setMouseEnabled(x=False, y=False) # Prevent zooming
        self.hideButtons() # Remove autoScale button

        # Axis Labels
        styles = {'color': text_color}
        self.setLabel('left', 'Pressure (kbar)', **styles)
        self.setLabel('bottom', f'Time (s)', **styles)


    def setup_lines(self):
        display_channels = ['hi_pre_orig', 'hi_pre_sample']
        dummy_x = [0, 10]
        dummy_y = [0, 0]
        self.x = []
        self.y = {channel: [] for channel in display_channels}
        self.initial_time = None
        self.line_references = {}

        # Create a dictionary of lines for each channel listed in display_channels
        for channel in display_channels:
            color = self.CHANNEL_COLORS[channel]
            self.line_references[channel] = self.plot_line(dummy_x, dummy_y, color)


    def update_data(self, data):
        # Add pressure to each line plotted.
        # This is the average pressure after the max pressure
        for channel, y in self.y.items():
            max_index = np.argmax(data[channel])
            pressure = np.average(data[channel][max_index:])
            y.append(pressure)

        # Add current time to x values
        if self.initial_time is None:
            self.initial_time = time()
        time_since_start = time() - self.initial_time
        self.x.append(time_since_start)

        # update data for each line
        for channel, line_reference in self.line_references.items():
            coefficient = self.CHANNEL_COEFFICIENTS[channel]
            line_reference.setData(self.x, np.asarray(self.y[channel]) * coefficient)


    def plot_line(self, x, y, color, style=Qt.SolidLine):
        pen = pg.mkPen(color=color, style=style)
        return self.plot(x, y, pen=pen)
