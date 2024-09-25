from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QSpacerItem, QSizePolicy
import pyqtgraph as pg
from icarus_v2.backend.event import Event, Channel
from bisect import bisect_right, bisect_left
import numpy as np
from icarus_v2.gui.styled_plot_widget import StyledPlotWidget

class HistoryPlot(QWidget):
    # Dictionary of pens to plot each line
    LINE_STYLES = {
        "origin pressure": ('#FFDC00', Qt.SolidLine),  # yellow
        "sample pressure": ('#FFDC00', Qt.DashLine),  # yellow dashed
        "depress origin slope": ('#59D8E6', Qt.SolidLine),  # cyan
        "depress sample slope": ('#59D8E6', Qt.DashLine),  # cyan dashed
        "press origin slope": ('#B9121B', Qt.SolidLine),  # red
        "press sample slope": ('#B9121B', Qt.DashLine),  # red dashed
        "depress origin switch": ('#59D8E6', Qt.SolidLine),  # cyan
        "depress sample switch": ('#59D8E6', Qt.DashLine),  # cyan dashed
        "press origin switch": ('#B9121B', Qt.SolidLine),  # red
        "press sample switch": ('#B9121B', Qt.DashLine),  # red dashed
    }

    # Dictionary of lines updated on certain events
    EVENT_LINES = {
        Event.PRESSURIZE: [
            "press origin slope",
            "press sample slope",
            "press origin switch",
            "press sample switch"
        ],
        Event.DEPRESSURIZE: [
            "origin pressure",
            "sample pressure",
            "depress origin slope",
            "depress sample slope",
            "depress origin switch",
            "depress sample switch"
        ]
    }

    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.coefficients = None
        self.log_coefficients = None
        self.update_settings("plotting_coefficients")
        self.config_manager.settings_updated.connect(self.update_settings)
        self.data = None
        self.initial_time = None
        self.can_plot_pressurize = None
        self.limits = None
        self.min_zoom = None

        # Dictionary of line references
        self.lines = {}
        self.hide_sample_sensor = False
        # Used to prevent plotting multiple pressurizes per depressurize which results in noisy plots
        self.can_plot_pressurize = True
        # Dictionary of mouse position labels
        self.mouse_labels = {}

        # Pressure plot
        self.pressure_plot = StyledPlotWidget(x_zoom=True)
        self.pressure_plot.set_title("Pressure")
        self.pressure_plot.set_y_label('Pressure (kBar)')
        self.pressure_plot.set_x_label('Time (s)')
        self.pressure_plot.setYRange(0, 3)
        style = self.LINE_STYLES["origin pressure"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["origin pressure"] = self.pressure_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["sample pressure"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["sample pressure"] = self.pressure_plot.plot([], [], pen=pen)
        self.pressure_plot.getPlotItem().getViewBox().sigStateChanged.connect(self.set_text)

        # Slope plot
        self.slope_plot = StyledPlotWidget(x_zoom=True)
        self.slope_plot.set_title("Pressure Change Slope")
        self.slope_plot.set_y_label('Slope (kBar/ms)')
        self.slope_plot.set_x_label('Time (s)')
        self.slope_plot.setYRange(-1.1, 1.1)
        style = self.LINE_STYLES["depress origin slope"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["depress origin slope"] = self.slope_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["depress sample slope"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["depress sample slope"] = self.slope_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["press origin slope"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["press origin slope"] = self.slope_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["press sample slope"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["press sample slope"] = self.slope_plot.plot([], [], pen=pen)
        # Connect the x-axis of all plots for zooming and panning
        self.slope_plot.setXLink(self.pressure_plot)

        # Switch time plot
        self.switch_time_plot = StyledPlotWidget(x_zoom=True)
        self.switch_time_plot.set_title("Switch Time")
        self.switch_time_plot.set_y_label('Time (ms)')
        self.switch_time_plot.set_x_label('Time (s)')
        self.switch_time_plot.setYRange(0, 45)
        style = self.LINE_STYLES["depress origin switch"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["depress origin switch"] = self.switch_time_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["depress sample switch"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["depress sample switch"] = self.switch_time_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["press origin switch"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["press origin switch"] = self.switch_time_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["press sample switch"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["press sample switch"] = self.switch_time_plot.plot([], [], pen=pen)
        # Connect the x-axis of all plots for zooming and panning
        self.switch_time_plot.setXLink(self.pressure_plot)

        # Statistics labels
        size = 14
        # Pressure plot
        self.last_pressure_display = QLabel("0.000")
        self.avg_pressure_display = QLabel("0.000")
        last_pressure_label = QLabel("Last:")
        avg_pressure_label = QLabel("Avg:")
        color = self.LINE_STYLES["origin pressure"][0]
        self.last_pressure_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_pressure_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        last_pressure_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        avg_pressure_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        # Mouse label
        self.mouse_labels[self.pressure_plot] = QLabel("")
        self.mouse_labels[self.pressure_plot].setStyleSheet(f"font-size: {size}px;")

        # Limit rate of mouseMoved signal to 60 Hz
        def pressure_func(x):
            self.mouse_moved(self.pressure_plot, x)

        self.pressure_proxy = pg.SignalProxy(self.pressure_plot.scene().sigMouseMoved, rateLimit=120,
                                             slot=pressure_func)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        pressure_labels = QGridLayout()
        pressure_labels.setContentsMargins(0, 35, 5, 45)
        pressure_labels.addWidget(last_pressure_label, 0, 1)
        pressure_labels.addWidget(avg_pressure_label, 1, 1)
        pressure_labels.addWidget(self.last_pressure_display, 0, 2)
        pressure_labels.addWidget(self.avg_pressure_display, 1, 2)
        pressure_labels.addItem(spacer, 2, 0)
        pressure_labels.addWidget(self.mouse_labels[self.pressure_plot], 3, 0, 1, 3, Qt.AlignRight | Qt.AlignBottom)
        # Slope plot
        self.last_press_slope_display = QLabel("0.00")
        self.avg_press_slope_display = QLabel("0.00")
        last_press_slope_label = QLabel("Last:")
        avg_press_slope_label = QLabel("Avg:")
        color = self.LINE_STYLES["press origin slope"][0]
        self.last_press_slope_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_press_slope_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        last_press_slope_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        avg_press_slope_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.last_depress_slope_display = QLabel("0.00")
        self.avg_depress_slope_display = QLabel("0.00")
        last_depress_slope_label = QLabel("Last:")
        avg_depress_slope_label = QLabel("Avg:")
        color = self.LINE_STYLES["depress origin slope"][0]
        self.last_depress_slope_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_depress_slope_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        last_depress_slope_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        avg_depress_slope_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        # Mouse label
        self.mouse_labels[self.slope_plot] = QLabel("")
        self.mouse_labels[self.slope_plot].setStyleSheet(f"font-size: {size}px;")

        # Limit rate of mouseMoved signal to 60 Hz

        def slope_func(x):
            self.mouse_moved(self.slope_plot, x)

        self.slope_proxy = pg.SignalProxy(self.slope_plot.scene().sigMouseMoved, rateLimit=120, slot=slope_func)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        slope_labels = QGridLayout()
        slope_labels.setContentsMargins(0, 35, 5, 45)
        slope_labels.addWidget(last_press_slope_label, 0, 1)
        slope_labels.addWidget(avg_press_slope_label, 1, 1)
        slope_labels.addWidget(self.last_press_slope_display, 0, 2)
        slope_labels.addWidget(self.avg_press_slope_display, 1, 2)
        slope_labels.addWidget(last_depress_slope_label, 2, 1)
        slope_labels.addWidget(avg_depress_slope_label, 3, 1)
        slope_labels.addWidget(self.last_depress_slope_display, 2, 2)
        slope_labels.addWidget(self.avg_depress_slope_display, 3, 2)
        slope_labels.addItem(spacer, 4, 0)
        slope_labels.addWidget(self.mouse_labels[self.slope_plot], 5, 0, 1, 3, Qt.AlignRight | Qt.AlignBottom)
        # Switch Time Plot
        self.last_press_switch_display = QLabel("0.00")
        self.avg_press_switch_display = QLabel("0.00")
        last_press_switch_label = QLabel("Last:")
        avg_press_switch_label = QLabel("Avg:")
        color = self.LINE_STYLES["press origin switch"][0]
        self.last_press_switch_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_press_switch_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        last_press_switch_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        avg_press_switch_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.last_depress_switch_display = QLabel("0.00")
        self.avg_depress_switch_display = QLabel("0.00")
        last_depress_switch_label = QLabel("Last:")
        avg_depress_switch_label = QLabel("Avg:")
        color = self.LINE_STYLES["depress origin switch"][0]
        self.last_depress_switch_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_depress_switch_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        last_depress_switch_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        avg_depress_switch_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        # Mouse label
        self.mouse_labels[self.switch_time_plot] = QLabel("")
        self.mouse_labels[self.switch_time_plot].setStyleSheet(f"font-size: {size}px;")

        # Limit rate of mouseMoved signal to 60 Hz
        def switch_func(x):
            self.mouse_moved(self.switch_time_plot, x)

        self.switch_proxy = pg.SignalProxy(self.switch_time_plot.scene().sigMouseMoved, rateLimit=120, slot=switch_func)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        switch_labels = QGridLayout()
        switch_labels.setContentsMargins(0, 35, 5, 45)
        switch_labels.addWidget(last_press_switch_label, 0, 1)
        switch_labels.addWidget(avg_press_switch_label, 1, 1)
        switch_labels.addWidget(self.last_press_switch_display, 0, 2)
        switch_labels.addWidget(self.avg_press_switch_display, 1, 2)
        switch_labels.addWidget(last_depress_switch_label, 2, 1)
        switch_labels.addWidget(avg_depress_switch_label, 3, 1)
        switch_labels.addWidget(self.last_depress_switch_display, 2, 2)
        switch_labels.addWidget(self.avg_depress_switch_display, 3, 2)
        switch_labels.addItem(spacer, 4, 0)
        switch_labels.addWidget(self.mouse_labels[self.switch_time_plot], 5, 0, 1, 3, Qt.AlignRight | Qt.AlignBottom)

        # Lines for displaying log view time
        self.press_time_press = None
        self.press_time_slope = None
        self.press_time_switch = None
        self.depress_time_press = None
        self.depress_time_slope = None
        self.depress_time_switch = None

        # Set layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.pressure_plot, 0, 0)
        self.layout.addLayout(pressure_labels, 0, 0, Qt.AlignRight | Qt.AlignTop)
        self.layout.addWidget(self.slope_plot, 1, 0)
        self.layout.addLayout(slope_labels, 1, 0, Qt.AlignRight | Qt.AlignTop)
        self.layout.addWidget(self.switch_time_plot, 2, 0)
        self.layout.addLayout(switch_labels, 2, 0, Qt.AlignRight | Qt.AlignTop)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.reset_history()

    def reset_history(self):
        self.data = {
            "time": {
                Event.DEPRESSURIZE: [],
                Event.PRESSURIZE: []
            },
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
        self.can_plot_pressurize = True

        for line in self.lines.values():
            line.setData([], [])

        self.limits = (0, 1)
        self.min_zoom = 1
        self.reset_limits()

        self.last_pressure_display.setText("0.000")
        self.avg_pressure_display.setText("0.000")
        self.last_press_slope_display.setText("0.00")
        self.avg_press_slope_display.setText("0.00")
        self.last_depress_slope_display.setText("0.00")
        self.avg_depress_slope_display.setText("0.00")
        self.last_press_switch_display.setText("0.00")
        self.avg_press_switch_display.setText("0.00")
        self.last_depress_switch_display.setText("0.00")
        self.avg_depress_switch_display.setText("0.00")

        # Lines for displaying log view time
        self.pressure_plot.removeItem(self.press_time_press)
        self.slope_plot.removeItem(self.press_time_slope)
        self.switch_time_plot.removeItem(self.press_time_switch)
        self.pressure_plot.removeItem(self.depress_time_press)
        self.slope_plot.removeItem(self.depress_time_slope)
        self.switch_time_plot.removeItem(self.depress_time_switch)

        self.pressure_plot.setXRange(self.limits[0], self.limits[1])

    def add_event(self, event):
        # plot only one pressurize per pressurize. plots are noisy with multiple pressurizes.
        if event.event_type == Event.PRESSURIZE:
            if not self.can_plot_pressurize:
                return
            self.can_plot_pressurize = False
        elif event.event_type == Event.DEPRESSURIZE:
            self.can_plot_pressurize = True

        # Check if currently fully zoomed out
        current_x_range = self.pressure_plot.viewRange()[0]
        low_diff = current_x_range[0] - self.limits[0]
        hi_diff = self.limits[1] - current_x_range[1]
        currently_zoomed_out = low_diff + hi_diff < 1

        self.process_data(event)
        for update in self.EVENT_LINES[event.event_type]:
            self.lines[update].setData(self.data["time"][event.event_type], self.data[update])

        # Update limits to fit new point
        max_view = max(event.event_time - self.initial_time, self.pressure_plot.viewRange()[0][1])
        self.limits = (0, max_view)
        if self.min_zoom < 10 <= max_view:
            self.min_zoom = 10
        self.reset_limits()
        # Update view range iff was already zoomed out
        if currently_zoomed_out:
            # Only need to do pressure plot since plot x ranges are linked
            self.pressure_plot.setXRange(self.limits[0], self.limits[1])

    def reset_limits(self):
        self.pressure_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1], minXRange=self.min_zoom)
        self.slope_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1], minXRange=self.min_zoom)
        self.switch_time_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1], minXRange=self.min_zoom)

    # Assumes list is sorted by time
    def load_event_list(self, event_list):
        if len(event_list) == 0:
            return

        for event in event_list:
            if event.event_type == Event.DEPRESSURIZE:
                self.can_plot_pressurize = True
                self.process_data(event)
            if event.event_type == Event.PRESSURIZE and self.can_plot_pressurize:
                self.can_plot_pressurize = False
                self.process_data(event)

        for update in self.EVENT_LINES[Event.DEPRESSURIZE]:
            self.lines[update].setData(self.data["time"][Event.DEPRESSURIZE], self.data[update])
        for update in self.EVENT_LINES[Event.PRESSURIZE]:
            self.lines[update].setData(self.data["time"][Event.PRESSURIZE], self.data[update])

        max_view = max(event_list[-1].event_time - self.initial_time, self.pressure_plot.viewRange()[0][1])
        self.limits = (0, max_view)
        if self.min_zoom < 10 <= max_view:
            self.min_zoom = 10
        self.reset_limits()
        # Only need to do pressure plot since plot x ranges are linked
        self.pressure_plot.setXRange(self.limits[0], self.limits[1])
        self.set_text()

    def process_data(self, event):
        # Define start time of plots
        if self.initial_time is None:
            self.initial_time = event.event_time

        # Update data
        self.data["time"][event.event_type].append(event.event_time - self.initial_time)
        coefficients = self.coefficients if self.log_coefficients is None else self.log_coefficients
        for update in self.EVENT_LINES[event.event_type]:
            # Add event to data dict
            self.data[update].append(event.get_event_info(update) * coefficients[update])

    # Sets all text to the data in view
    def set_text(self):
        view_range = self.pressure_plot.viewRange()[0]
        press_range = (
            bisect_left(self.data["time"][Event.PRESSURIZE], view_range[0]),
            bisect_right(self.data["time"][Event.PRESSURIZE], view_range[1]) - 1
        )
        depress_range = (
            bisect_left(self.data["time"][Event.DEPRESSURIZE], view_range[0]),
            bisect_right(self.data["time"][Event.DEPRESSURIZE], view_range[1]) - 1
        )

        if depress_range[1] - depress_range[0] > 0:
            self.last_pressure_display.setText(f"{self.data['origin pressure'][depress_range[1]]:.3f}")
            self.avg_pressure_display.setText(
                f"{np.mean(self.data['origin pressure'][depress_range[0]:depress_range[1]]):.3f}"
            )
            self.last_depress_slope_display.setText(f"{self.data['depress origin slope'][depress_range[1]]:.2f}")
            self.avg_depress_slope_display.setText(
                f"{np.mean(self.data['depress origin slope'][depress_range[0]:depress_range[1]]):.2f}"
            )
            self.last_depress_switch_display.setText(f"{self.data['depress origin switch'][depress_range[1]]:.2f}")
            self.avg_depress_switch_display.setText(
                f"{np.mean(self.data['depress origin switch'][depress_range[0]:depress_range[1]]):.2f}"
            )
        if press_range[1] - press_range[0] > 0:
            self.last_press_slope_display.setText(f"{self.data['press origin slope'][press_range[1]]:.2f}")
            self.avg_press_slope_display.setText(
                f"{np.mean(self.data['press origin slope'][press_range[0]:press_range[1]]):.2f}"
            )
            self.last_press_switch_display.setText(f"{self.data['press origin switch'][press_range[1]]:.2f}")
            self.avg_press_switch_display.setText(
                f"{np.mean(self.data['press origin switch'][press_range[0]:press_range[1]]):.2f}"
            )

    def update_settings(self, key):
        if key == "plotting_coefficients":
            plotting_coefficients = self.config_manager.get_settings(key)
            self.coefficients = self.define_coefficients(plotting_coefficients)

    def render_pressurize_time(self, event):
        # Remove old time
        self.pressure_plot.removeItem(self.press_time_press)
        self.slope_plot.removeItem(self.press_time_slope)
        self.switch_time_plot.removeItem(self.press_time_switch)

        if event is not None:
            time = event.event_time - self.initial_time
            style = self.LINE_STYLES["press origin slope"]
            pen = pg.mkPen(color=style[0], style=style[1])
            self.press_time_press = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)
            self.press_time_slope = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)
            self.press_time_switch = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)
            self.pressure_plot.addItem(self.press_time_press)
            self.slope_plot.addItem(self.press_time_slope)
            self.switch_time_plot.addItem(self.press_time_switch)

    def render_depressurize_time(self, event):
        # Remove old time
        self.pressure_plot.removeItem(self.depress_time_press)
        self.slope_plot.removeItem(self.depress_time_slope)
        self.switch_time_plot.removeItem(self.depress_time_switch)

        if event is not None:
            time = event.event_time - self.initial_time
            style = self.LINE_STYLES["depress origin slope"]
            pen = pg.mkPen(color=style[0], style=style[1])
            self.depress_time_press = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)
            self.depress_time_slope = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)
            self.depress_time_switch = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)
            self.pressure_plot.addItem(self.depress_time_press)
            self.slope_plot.addItem(self.depress_time_slope)
            self.switch_time_plot.addItem(self.depress_time_switch)

    def mouse_moved(self, plot, event):
        mouse_point = plot.getViewBox().mapSceneToView(event[0])
        view_range = plot.getViewBox().viewRange()

        # Check if the mouse point is within the view range
        if (view_range[0][0] <= mouse_point.x() <= 0.98 * view_range[0][1] and
                view_range[1][0] <= mouse_point.y() <= view_range[1][1]):
            self.mouse_labels[plot].setText(f"{mouse_point.x():.2f}, {mouse_point.y():.2f}")
        else:
            self.mouse_labels[plot].setText("")

    def set_sample_sensor(self, connected):
        if not connected and not self.hide_sample_sensor:
            self.pressure_plot.removeItem(self.lines["sample pressure"])
            self.slope_plot.removeItem(self.lines["press sample slope"])
            self.slope_plot.removeItem(self.lines["depress sample slope"])
            self.switch_time_plot.removeItem(self.lines["press sample switch"])
            self.switch_time_plot.removeItem(self.lines["depress sample switch"])
            self.hide_sample_sensor = True

        elif connected and self.hide_sample_sensor:
            self.pressure_plot.addItem(self.lines["sample pressure"])
            self.slope_plot.addItem(self.lines["press sample slope"])
            self.slope_plot.addItem(self.lines["depress sample slope"])
            self.switch_time_plot.addItem(self.lines["press sample switch"])
            self.switch_time_plot.addItem(self.lines["depress sample switch"])
            self.hide_sample_sensor = False

    def set_log_coefficients(self, coefficients):
        self.log_coefficients = self.define_coefficients(coefficients)

    # Dictionary of coefficient to apply when plotting each channel
    @staticmethod
    def define_coefficients(plotting_coefficients):
        if plotting_coefficients is None:
            return None
        # Dictionary of coefficient to apply when plotting each channel
        coefficients = {
            "origin pressure": plotting_coefficients[Channel.HI_PRE_ORIG],
            "sample pressure": plotting_coefficients[Channel.HI_PRE_SAMPLE],
            "depress origin slope": plotting_coefficients[Channel.HI_PRE_ORIG] * 4,
            "depress sample slope": plotting_coefficients[Channel.HI_PRE_SAMPLE] * 4,
            "press origin slope": plotting_coefficients[Channel.HI_PRE_ORIG] * 4,
            "press sample slope": plotting_coefficients[Channel.HI_PRE_SAMPLE] * 4,
            "depress origin switch": 0.25,
            "depress sample switch": 0.25,
            "press origin switch": 0.25,  # ms per index
            "press sample switch": 0.25,  # ms per index
        }
        return coefficients
