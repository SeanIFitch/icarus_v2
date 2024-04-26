from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from Channel import Channel, get_channel
from Event import Event


class EventPlot(pg.PlotWidget):
    # Dictionary of color to plot each channel
    PENS = {
        Channel.TARGET: pg.mkPen(color='#45BF55', style=Qt.SolidLine),          # light green
        Channel.DEPRE_LOW: pg.mkPen(color='#AB47BC', style=Qt.SolidLine),       # magenta
        Channel.DEPRE_UP: pg.mkPen(color='#004B8D', style=Qt.SolidLine),        # blue
        Channel.PRE_LOW: pg.mkPen(color='#AB47BC', style=Qt.SolidLine),         # magenta
        Channel.PRE_UP: pg.mkPen(color='#004B8D', style=Qt.SolidLine),          # blue
        Channel.HI_PRE_ORIG: pg.mkPen(color='#FFDC00', style=Qt.SolidLine),     # yellow
        Channel.HI_PRE_SAMPLE: pg.mkPen(color='#FFDC00', style=Qt.DashLine),    # yellow dashed
        Channel.DEPRE_VALVE: pg.mkPen(color='#59D8E6', style=Qt.SolidLine),     # cyan
        Channel.PRE_VALVE: pg.mkPen(color='#B9121B', style=Qt.SolidLine),       # red
    }

    def __init__(self, event_type, display_offset, sample_rate, config_manager):
        super().__init__()

        display_channels = [Channel.TARGET, Channel.HI_PRE_SAMPLE, Channel.HI_PRE_ORIG, Channel.DEPRE_VALVE, Channel.PRE_VALVE]

        if event_type == Event.PRESSURIZE:
            display_channels += [Channel.PRE_LOW, Channel.PRE_UP]
            self.x_unit = 'ms'
            title = "Pressurize"
            self.setXRange(-10, 140)
        elif event_type == Event.DEPRESSURIZE:
            display_channels += [Channel.DEPRE_LOW, Channel.DEPRE_UP]
            self.x_unit = 'ms'
            title = "Depressurize"
            self.setXRange(-10, 140)
        elif event_type == Event.PERIOD:
            self.x_unit = 's'
            title = "Period"

        # Amount of time in ms to offset x axis. t=0 should be the event occurence.
        self.display_offset = display_offset

        self.sample_rate = sample_rate
        self.config_manager = config_manager
        self.config_manager.settings_updated.connect(self.update_settings)
        self.coefficients = config_manager.get_settings("plotting_coefficients")

        window_color = self.palette().color(QPalette.Window)
        text_color = self.palette().color(QPalette.WindowText)
        self.setBackground(window_color)

        self.setTitle(title, color=text_color, size="14pt")
        self.showGrid(x=True, y=True)
        self.setYRange(0, 3)
        self.setMouseEnabled(x=False, y=False) # Prevent zooming
        self.hideButtons() # Remove autoScale button

        # Axis Labels
        styles = {'color':text_color}
        self.setLabel('left', 'Pressure (kbar)', **styles)
        self.setLabel('bottom', f'Time ({self.x_unit})', **styles)

        # Create a dictionary of lines for each channel listed in display_channels
        self.line_references = {}
        for channel in display_channels:
            self.line_references[channel] = self.plot([], [], pen=self.PENS[channel])


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
            coefficient = self.coefficients[channel]
            line_reference.setData(times, get_channel(data, channel) * coefficient)


    def update_settings(self, key):
        if key == "plotting_coefficients":
            self.coefficients = self.config_manager.get_settings(key)
