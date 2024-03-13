from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np

class DepressurizeEventPlot(pg.PlotWidget):
    def __init__(self, display_range, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)

        self.display_range = display_range

        window_color = self.palette().color(QPalette.Window)
        text_color = self.palette().color(QPalette.WindowText)
        self.setBackground(window_color)

        self.setTitle("Depressurize", color=text_color, size="20pt")
        self.showGrid(x=True, y=True)
        self.setYRange(-6, 12, padding=0)
        self.setXRange(-15, 145, padding=0)

        # Axis Labels
        styles = {'color':text_color}
        self.setLabel('left', 'Pressure (kbar)', **styles)
        self.setLabel('bottom', 'Time (ms)', **styles)

        dummy_x = [-10,140]
        dummy_y = [0,0]
        self.target = self.plot_line(dummy_x, dummy_y, 'black', style = Qt.DashLine)
        self.depre_low = self.plot_line(dummy_x, dummy_y, 'darkcyan')
        self.depre_up = self.plot_line(dummy_x, dummy_y, 'darkmagenta')
        self.hi_pre_sample = self.plot_line(dummy_x, dummy_y, 'red')
        self.depre_valve = self.plot_line(dummy_x, dummy_y, 'lightgreen')
        self.pre_valve = self.plot_line(dummy_x, dummy_y, 'blue', style = Qt.DashLine)


    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate


    def update_data(self, data):
        start, end = self.display_range
        step_size = (end - start) / len(data)
        times = np.arange(start, end, step_size) # in ms

        self.target.setData(times, data['target'])
        self.depre_low.setData(times, data['depre_low'])
        self.depre_up.setData(times, data['depre_up'])
        self.hi_pre_sample.setData(times, data['hi_pre_sample'])
        self.depre_valve.setData(times, data['depre_valve'] * 10)
        self.pre_valve.setData(times, data['pre_valve'] * 10.01)


    def plot_line(self, x, y, color, style = Qt.SolidLine):
        pen = pg.mkPen(color=color, style=style)
        return self.plot(x, y, pen=pen)
