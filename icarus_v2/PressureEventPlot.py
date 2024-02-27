from PySide6.QtGui import QPalette
import pyqtgraph as pg
import numpy as np

class PressureEventPlot(pg.PlotWidget):
    # Which channels to plot
    PLOT_PRESSURES = [0, 1, 2, 3, 4, 5, 6]
    PLOT_DIGITAL = [0, 1, 2, 3, 4, 5, 6]

    def __init__(self, title, display_range, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)

        self.display_range = display_range

        window_color = self.palette().color(QPalette.Window)
        text_color = self.palette().color(QPalette.WindowText)
        self.setBackground(window_color)

        self.setTitle(title, color=text_color, size="30pt")
        self.addLegend()
        self.showGrid(x=True, y=True)
        #self.setYRange(30, 40, padding=0)

        # Axis Labels
        styles = {'color':text_color}
        self.setLabel('left', 'Pressure (kbar)', **styles)
        self.setLabel('bottom', 'Time (ms)', **styles)

        self.line1_ref = self.plot_line([0], [0], "line 1", 'r')


    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate


    def update_data(self, data):
        start, end = self.display_range
        step_size = (end - start) / len(data)
        times = np.arange(start, end, step_size) # in ms

        self.line1_ref.setData(times, data)


    def plot_line(self, x, y, plotname, color):
        pen = pg.mkPen(color=color)
        return self.plot(x, y, name=plotname, pen=pen)
