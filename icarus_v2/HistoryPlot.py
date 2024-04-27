from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from Event import Event
from Channel import Channel


class HistoryPlot(QWidget):
    # Dictionary of pens to plot each line
    PENS = {
        "origin pressure": pg.mkPen(color='#FFDC00', style=Qt.SolidLine),       # yellow
        "sample pressure": pg.mkPen(color='#FFDC00', style=Qt.DashLine),        # yellow dashed
        "depress origin slope": pg.mkPen(color='#59D8E6', style=Qt.SolidLine),  # cyan
        "depress sample slope": pg.mkPen(color='#59D8E6', style=Qt.DashLine),   # cyan dashed
        "press origin slope": pg.mkPen(color='#B9121B', style=Qt.SolidLine),    # red
        "press sample slope": pg.mkPen(color='#B9121B', style=Qt.DashLine),     # red dashed
        "depress origin switch": pg.mkPen(color='#59D8E6', style=Qt.SolidLine), # cyan
        "depress sample switch": pg.mkPen(color='#59D8E6', style=Qt.DashLine),  # cyan dashed
        "press origin switch": pg.mkPen(color='#B9121B', style=Qt.SolidLine),   # red
        "press sample switch": pg.mkPen(color='#B9121B', style=Qt.DashLine),    # red dashed
    }


    def __init__(self, sample_rate, config_manager):
        super().__init__()

        self.sample_rate = sample_rate
        self.config_manager = config_manager
        self.update_settings("plotting_coefficients")
        self.config_manager.settings_updated.connect(self.update_settings)

        # Dictionary of line references
        self.lines = {}
        # Colors for plots
        window_color = self.palette().color(QPalette.Window)
        text_color = self.palette().color(QPalette.WindowText)
        style = {'color': text_color}

        # Pressure plot
        self.pressure_plot = pg.PlotWidget()
        self.pressure_plot.setBackground(window_color)
        self.pressure_plot.showGrid(x=True, y=True)
        self.pressure_plot.setMouseEnabled(x=True, y=False)
        self.pressure_plot.setTitle("Pressure", color=text_color, size="14pt")
        self.pressure_plot.setLabel('left', 'Pressure (kBar)', **style)
        self.pressure_plot.setLabel('bottom', 'Time (s)', **style)
        #self.pressure_plot.setYRange(0, 3)
        self.pressure_plot.hideButtons() # Remove autoScale button
        self.lines["origin pressure"] = self.pressure_plot.plot([], [], pen=self.PENS["origin pressure"])
        self.lines["sample pressure"] = self.pressure_plot.plot([], [], pen=self.PENS["sample pressure"])

        # Slope plot
        self.slope_plot = pg.PlotWidget()
        self.slope_plot.setBackground(window_color)
        self.slope_plot.showGrid(x=True, y=True)
        self.slope_plot.setMouseEnabled(x=True, y=False)
        self.slope_plot.setTitle("Pressure Change Slope", color=text_color, size="14pt")
        self.slope_plot.setLabel('left', 'Slope (kBar/ms)', **style)
        self.slope_plot.setLabel('bottom', 'Time (s)', **style)
        #self.slope_plot.setYRange(-5, 5)
        self.slope_plot.hideButtons() # Remove autoScale button
        self.lines["depress origin slope"] = self.slope_plot.plot([], [], pen=self.PENS["depress origin slope"])
        self.lines["depress sample slope"] = self.slope_plot.plot([], [], pen=self.PENS["depress sample slope"])
        self.lines["press origin slope"] = self.slope_plot.plot([], [], pen=self.PENS["press origin slope"])
        self.lines["press sample slope"] = self.slope_plot.plot([], [], pen=self.PENS["press sample slope"])
        # Connect the x-axis of all plots for zooming and panning
        self.slope_plot.setXLink(self.pressure_plot)

        # Switch time plot
        self.switch_time_plot = pg.PlotWidget()
        self.switch_time_plot.setBackground(window_color)
        self.switch_time_plot.showGrid(x=True, y=True)
        self.switch_time_plot.setMouseEnabled(x=True, y=False)
        self.switch_time_plot.setTitle("Switch Time", color=text_color, size="14pt")
        self.switch_time_plot.setLabel('left', 'Time (ms)', **style)
        self.switch_time_plot.setLabel('bottom', 'Time (s)', **style)
        #self.switch_time_plot.setYRange(0, 48)
        self.switch_time_plot.hideButtons() # Remove autoScale button
        self.lines["depress origin switch"] = self.switch_time_plot.plot([], [], pen=self.PENS["depress origin switch"])
        self.lines["depress sample switch"] = self.switch_time_plot.plot([], [], pen=self.PENS["depress sample switch"])
        self.lines["press origin switch"] = self.switch_time_plot.plot([], [], pen=self.PENS["press origin switch"])
        self.lines["press sample switch"] = self.switch_time_plot.plot([], [], pen=self.PENS["press sample switch"])
        # Connect the x-axis of all plots for zooming and panning
        self.switch_time_plot.setXLink(self.pressure_plot)

        # Set layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.pressure_plot)
        self.layout.addWidget(self.slope_plot)
        self.layout.addWidget(self.switch_time_plot)
        self.setLayout(self.layout)

        self.reset_history()


    def reset_history(self):
        self.data = {
            "depress time": [],
            "press time": [],
            "origin pressure": [],
            "sample pressure": [],
            "depress origin slope": [],
            "depress sample slope": [],
            "press origin slope": [],
            "press sample slope": [],
            "depress origin switch": [],
            "depress sample switch": [],
            "press origin switch": [],
            "press sample switch": [],
        }
        self.initial_time = None

        for line in self.lines.values():
            line.setData([], [])

        self.limits = (0,1)
        self.pressure_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1])
        self.slope_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1])
        self.switch_time_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1])

        self.pressure_plot.setXRange(self.limits[0], self.limits[1])


    def add_event(self, event):
        # Define start time of plots
        if self.initial_time is None:
            self.initial_time = event.event_time

        # Check if currently fully zoomed out
        current_x_range = self.pressure_plot.viewRange()[0]
        low_diff = current_x_range[0] - self.limits[0]
        hi_diff = self.limits[1] - current_x_range[1]
        currently_zoomed_out = low_diff + hi_diff < 1

        if event.event_type == Event.PRESSURIZE:
            time_to_update = "press time"

            # list of lines to update
            lines_to_update =[
                "press origin slope", 
                "press sample slope", 
                "press origin switch", 
                "press sample switch"
            ]

        elif event.event_type == Event.DEPRESSURIZE:
            time_to_update = "depress time"

            # list of lines to update
            lines_to_update = [
                "origin pressure",
                "sample pressure",
                "depress origin slope", 
                "depress sample slope", 
                "depress origin switch", 
                "depress sample switch"
            ]

        else:
            raise RuntimeError(f"Event of type {event.event_type} sent to HistoryPlot.add_event")

        # Update data
        self.data[time_to_update].append(event.event_time - self.initial_time)
        for update in lines_to_update:
            # Add event to data dict
            self.data[update].append(event.get_event_info(update) * self.coefficients[update])
            # Update plot
            self.lines[update].setData(self.data[time_to_update], self.data[update])

        # Update limits to fit new point
        max_view = max(event.event_time - self.initial_time, self.pressure_plot.viewRange()[0][1])
        self.limits = (0, max_view)
        self.pressure_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1])
        self.slope_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1])
        self.switch_time_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1])
        # Update view range iff was already zoomed out
        if currently_zoomed_out:
            # Only need to do pressure plot since plot x ranges are linked
            self.pressure_plot.setXRange(self.limits[0], self.limits[1])


    def update_settings(self, key):
        if key == "plotting_coefficients":
            plotting_coefficients = self.config_manager.get_settings(key)
            # Dictionary of coefficient to apply when plotting each channel
            self.coefficients = {
                "origin pressure": plotting_coefficients[Channel.HI_PRE_ORIG],
                "sample pressure": plotting_coefficients[Channel.HI_PRE_SAMPLE],
                "depress origin slope": plotting_coefficients[Channel.HI_PRE_ORIG] * 4,
                "depress sample slope": plotting_coefficients[Channel.HI_PRE_SAMPLE] * 4,
                "press origin slope": plotting_coefficients[Channel.HI_PRE_ORIG] * 4,
                "press sample slope": plotting_coefficients[Channel.HI_PRE_SAMPLE] * 4,
                "depress origin switch": 0.25,
                "depress sample switch": 0.25,
                "press origin switch": 0.25,    # ms per index
                "press sample switch": 0.25,    # ms per index
            }
