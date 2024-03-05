from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np

class DepressurizeEventPlot(pg.PlotWidget):
    # Which channels to plot
    PLOT_PRESSURES = [0, 1, 2, 5] # target pressure, depressurization lower, depressurization upper, high pressure transducer
    PLOT_DIGITAL = [1, 2] # depressurize, pressurize

    def __init__(self, display_range, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)

        self.display_range = display_range

        window_color = self.palette().color(QPalette.Window)
        text_color = self.palette().color(QPalette.WindowText)
        self.setBackground(window_color)

        self.setTitle("Depressurize", color=text_color, size="20pt")
        self.showGrid(x=True, y=True)
        #self.setYRange(0, 4, padding=0)
        #self.setXRange(-10, 140, padding=0)
        #self.addLegend()

        # Axis Labels
        styles = {'color':text_color}
        self.setLabel('left', 'Pressure (kbar)', **styles)
        self.setLabel('bottom', 'Time (ms)', **styles)

        dummy_x = [-10,140]
        dummy_y = [0,0]
        self.ana_0 = self.plot_line(dummy_x, dummy_y, "Target Pressure", 'black', style = Qt.DashLine)
        self.ana_1 = self.plot_line(dummy_x, dummy_y, "Depressurization Lower", 'darkcyan')
        self.ana_2 = self.plot_line(dummy_x, dummy_y, "Depressurization Upper", 'darkmagenta')
        self.ana_5 = self.plot_line(dummy_x, dummy_y, "Sample", 'red')
        self.dig_1 = self.plot_line(dummy_x, dummy_y, "Depressurization Valve", 'lightgreen')
        self.dig_2 = self.plot_line(dummy_x, dummy_y, "Pressurization Valve", 'blue', style = Qt.DashLine)


    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate


    def update_data(self, data):
        analog, digital = data

        start, end = self.display_range
        step_size = (end - start) / len(analog)
        times = np.arange(start, end, step_size) # in ms

        self.ana_0.setData(times, analog[:,0])
        self.ana_1.setData(times, analog[:,1])
        self.ana_2.setData(times, analog[:,2])
        self.ana_5.setData(times, analog[:,5])
        self.dig_1.setData(times, digital[:,1])
        self.dig_2.setData(times, digital[:,2])


    def plot_line(self, x, y, plotname, color, style = Qt.SolidLine):
        pen = pg.mkPen(color=color, style=style)
        return self.plot(x, y, name=plotname, pen=pen)