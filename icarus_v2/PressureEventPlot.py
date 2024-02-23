from PySide6.QtGui import QPalette
import pyqtgraph as pg
import numpy as np

class PressureEventPlot(pg.PlotWidget):
    def __init__(self, title, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)

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
        # TEST
        print(len(data))

        #times = float(len(data) * 1000) / self.sample_rate # in ms
        self.line1_ref.setData(range(len(data)), data)


    def plot_line(self, x, y, plotname, color):
        pen = pg.mkPen(color=color)
        return self.plot(x, y, name=plotname, pen=pen)
