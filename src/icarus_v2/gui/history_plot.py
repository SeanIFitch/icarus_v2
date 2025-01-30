from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from icarus_v2.backend.event import Event, Channel, HistStat
import numpy as np
from icarus_v2.gui.styled_plot_widget import StyledPlotWidget
from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES
from icarus_v2.gui.styled_plot_widget import theme
from icarus_v2.backend.configuration_manager import ConfigurationManager


class HistoryPlot(QWidget):
    # Dictionary of pens to plot each line
    LINE_STYLES = {
        HistStat.O_PRESS: (THEME_COLOR_VALUES[theme]['line']['yellow'], Qt.SolidLine),
        HistStat.S_PRESS: (THEME_COLOR_VALUES[theme]['line']['yellow'], Qt.DashLine),
        HistStat.DO_SLOPE: (THEME_COLOR_VALUES[theme]['line']['cyan'], Qt.SolidLine),
        HistStat.DS_SLOPE: (THEME_COLOR_VALUES[theme]['line']['cyan'], Qt.DashLine),
        HistStat.PO_SLOPE: (THEME_COLOR_VALUES[theme]['line']['red'], Qt.SolidLine),
        HistStat.PS_SLOPE: (THEME_COLOR_VALUES[theme]['line']['red'], Qt.DashLine),
        HistStat.DO_SWITCH: (THEME_COLOR_VALUES[theme]['line']['cyan'], Qt.SolidLine),
        HistStat.DS_SWITCH: (THEME_COLOR_VALUES[theme]['line']['cyan'], Qt.DashLine),
        HistStat.PO_SWITCH: (THEME_COLOR_VALUES[theme]['line']['red'], Qt.SolidLine),
        HistStat.PS_SWITCH: (THEME_COLOR_VALUES[theme]['line']['red'], Qt.DashLine),
    }

    def __init__(self):
        super().__init__()

        self.config_manager = ConfigurationManager()
        self.coefficients = None
        self.log_coefficients = None
        self.update_settings("plotting_coefficients")
        self.config_manager.settings_updated.connect(self.update_settings)
        self.initial_time = None
        self.can_plot_pressurize = None
        self.limits = None

        # Pressure plot
        self.pressure_plot = StyledPlotWidget(x_zoom=True)
        self.pressure_plot.set_title("Pressure")
        self.pressure_plot.set_y_label('Pressure (kBar)')
        self.pressure_plot.set_x_label('Time (s)')
        self.pressure_plot.setYRange(0, 3)
        self.pressure_plot.getPlotItem().getAxis("left").setWidth(45)
        style = self.LINE_STYLES[HistStat.O_PRESS]
        self.pressure_plot.add_line(HistStat.O_PRESS, style[0], style[1])
        style = self.LINE_STYLES[HistStat.S_PRESS]
        self.pressure_plot.add_line(HistStat.S_PRESS, style[0], style[1])
        self.pressure_plot.add_statistic(HistStat.O_PRESS, lambda x: x[-1], "Last: {:.3f}")
        self.pressure_plot.add_statistic(HistStat.O_PRESS, np.mean, "Avg: {:.3f}")

        # Slope plot
        self.slope_plot = StyledPlotWidget(x_zoom=True)
        self.slope_plot.set_title("Pressure Change Slope")
        self.slope_plot.set_y_label('Slope (kBar/ms)')
        self.slope_plot.set_x_label('Time (s)')
        self.slope_plot.setYRange(-1.1, 1.1)
        self.slope_plot.getPlotItem().getAxis("left").setWidth(45)
        style = self.LINE_STYLES[HistStat.DO_SLOPE]
        self.slope_plot.add_line(HistStat.DO_SLOPE, style[0], style[1])
        style = self.LINE_STYLES[HistStat.DS_SLOPE]
        self.slope_plot.add_line(HistStat.DS_SLOPE, style[0], style[1])
        style = self.LINE_STYLES[HistStat.PO_SLOPE]
        self.slope_plot.add_line(HistStat.PO_SLOPE, style[0], style[1])
        style = self.LINE_STYLES[HistStat.PS_SLOPE]
        self.slope_plot.add_line(HistStat.PS_SLOPE, style[0], style[1])
        # Connect the x-axis of all plots for zooming and panning
        self.slope_plot.setXLink(self.pressure_plot)
        self.slope_plot.add_statistic(HistStat.PO_SLOPE, lambda x: x[-1], "Last: {:.2f}")
        self.slope_plot.add_statistic(HistStat.PO_SLOPE, np.mean, "Avg: {:.2f}")
        self.slope_plot.add_statistic(HistStat.DO_SLOPE, lambda x: x[-1], "Last: {:.2f}")
        self.slope_plot.add_statistic(HistStat.DO_SLOPE, np.mean, "Avg: {:.2f}")

        # Switch time plot
        self.switch_time_plot = StyledPlotWidget(x_zoom=True)
        self.switch_time_plot.set_title("Switch Time")
        self.switch_time_plot.set_y_label('Time (ms)')
        self.switch_time_plot.set_x_label('Time (s)')
        self.switch_time_plot.setYRange(0, 45)
        self.switch_time_plot.getPlotItem().getAxis("left").setWidth(45)
        style = self.LINE_STYLES[HistStat.DO_SWITCH]
        self.switch_time_plot.add_line(HistStat.DO_SWITCH, style[0], style[1])
        style = self.LINE_STYLES[HistStat.DS_SWITCH]
        self.switch_time_plot.add_line(HistStat.DS_SWITCH, style[0], style[1])
        style = self.LINE_STYLES[HistStat.PO_SWITCH]
        self.switch_time_plot.add_line(HistStat.PO_SWITCH, style[0], style[1])
        style = self.LINE_STYLES[HistStat.PS_SWITCH]
        self.switch_time_plot.add_line(HistStat.PS_SWITCH, style[0], style[1])
        # Connect the x-axis of all plots for zooming and panning
        self.switch_time_plot.setXLink(self.pressure_plot)

        self.switch_time_plot.add_statistic(HistStat.PO_SWITCH, lambda x: x[-1], "Last: {:.2f}")
        self.switch_time_plot.add_statistic(HistStat.PO_SWITCH, np.mean, "Avg: {:.2f}")
        self.switch_time_plot.add_statistic(HistStat.DO_SWITCH, lambda x: x[-1], "Last: {:.2f}")
        self.switch_time_plot.add_statistic(HistStat.DO_SWITCH, np.mean, "Avg: {:.2f}")

        # Lines for displaying log view time
        self.press_time_press = None
        self.press_time_slope = None
        self.press_time_switch = None
        self.depress_time_press = None
        self.depress_time_slope = None
        self.depress_time_switch = None

        # Set layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.pressure_plot)
        self.layout.addWidget(self.slope_plot)
        self.layout.addWidget(self.switch_time_plot)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.reset_history()

    def reset_history(self):
        self.initial_time = None
        self.can_plot_pressurize = True

        self.pressure_plot.reset()
        self.slope_plot.reset()
        self.switch_time_plot.reset()

        self.limits = (0, 10)
        self.reset_limits()

        # Lines for displaying log view time
        self.pressure_plot.removeItem(self.press_time_press)
        self.slope_plot.removeItem(self.press_time_slope)
        self.switch_time_plot.removeItem(self.press_time_switch)
        self.pressure_plot.removeItem(self.depress_time_press)
        self.slope_plot.removeItem(self.depress_time_slope)
        self.switch_time_plot.removeItem(self.depress_time_switch)

        self.pressure_plot.setXRange(self.limits[0], self.limits[1])

    def add_event(self, event):
        # Define start time of plots
        if self.initial_time is None:
            self.initial_time = event.event_time

        # plot only one pressurize per pressurize. plots are noisy with multiple pressurizes.
        if event.event_type == Event.PRESSURIZE:
            if not self.can_plot_pressurize:
                return
            self.can_plot_pressurize = False
        elif event.event_type == Event.DEPRESSURIZE:
            self.can_plot_pressurize = True

        # Check if currently fully zoomed out
        currently_zoomed_out = self.pressure_plot.get_view_state()

        # use log coefficients if defined
        coefficients = self.coefficients if self.log_coefficients is None else self.log_coefficients

        # Time since first event
        time = event.event_time - self.initial_time

        if event.event_type == Event.PRESSURIZE:
            self.slope_plot.append_points({
                HistStat.PO_SLOPE: event.get_event_info(HistStat.PO_SLOPE) * coefficients[HistStat.PO_SLOPE],
                HistStat.PS_SLOPE: event.get_event_info(HistStat.PS_SLOPE) * coefficients[HistStat.PS_SLOPE]
            }, time)

            self.switch_time_plot.append_points({
                HistStat.PO_SWITCH: event.get_event_info(HistStat.PO_SWITCH) * coefficients[HistStat.PO_SWITCH],
                HistStat.PS_SWITCH: event.get_event_info(HistStat.PS_SWITCH) * coefficients[HistStat.PS_SWITCH]
            }, time)

        elif event.event_type == Event.DEPRESSURIZE:
            self.pressure_plot.append_points({
                HistStat.O_PRESS: event.get_event_info(HistStat.O_PRESS) * coefficients[HistStat.O_PRESS],
                HistStat.S_PRESS: event.get_event_info(HistStat.S_PRESS) * coefficients[HistStat.S_PRESS]
            }, time)

            self.slope_plot.append_points({
                HistStat.DO_SLOPE: event.get_event_info(HistStat.DO_SLOPE) * coefficients[HistStat.DO_SLOPE],
                HistStat.DS_SLOPE: event.get_event_info(HistStat.DS_SLOPE) * coefficients[HistStat.DS_SLOPE]
            }, time)

            self.switch_time_plot.append_points({
                HistStat.DO_SWITCH: event.get_event_info(HistStat.DO_SWITCH) * coefficients[HistStat.DO_SWITCH],
                HistStat.DS_SWITCH: event.get_event_info(HistStat.DS_SWITCH) * coefficients[HistStat.DS_SWITCH]
            }, time)

        # Update limits to fit new point
        max_view = max(time, self.pressure_plot.viewRange()[0][1], 10)
        self.limits = (0, max_view)
        self.reset_limits()
        # Update view range iff was already zoomed out
        if currently_zoomed_out:
            # Only need to do pressure plot since plot x ranges are linked
            self.pressure_plot.setXRange(self.limits[0], self.limits[1])

    def reset_limits(self):
        self.pressure_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1], minXRange=10)
        self.slope_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1], minXRange=10)
        self.switch_time_plot.setLimits(xMin=self.limits[0], xMax=self.limits[1], minXRange=10)

    # Assumes list is sorted by time
    def load_event_list(self, event_list):
        for event in event_list:
            self.add_event(event)

        # Only need to do pressure plot since plot x ranges are linked
        self.pressure_plot.setXRange(self.limits[0], self.limits[1])

    def update_settings(self, key):
        if key == "plotting_coefficients":
            plotting_coefficients = self.config_manager.get_settings(key)
            self.coefficients = self.define_coefficients(plotting_coefficients)

    def render_event_time(self, event):
        """
        Renders either pressurization or depressurization time based on event type.
        """
        # Determine whether the event is pressurization or depressurization
        if event.event_type == Event.PRESSURIZE:
            self.pressure_plot.removeItem(self.press_time_press)
            self.slope_plot.removeItem(self.press_time_slope)
            self.switch_time_plot.removeItem(self.press_time_switch)

            hist_stat = HistStat.PO_SLOPE
        else:
            self.pressure_plot.removeItem(self.depress_time_press)
            self.slope_plot.removeItem(self.depress_time_slope)
            self.switch_time_plot.removeItem(self.depress_time_switch)

            hist_stat = HistStat.DO_SLOPE

        # Compute time and style
        time = event.event_time - self.initial_time
        style = self.LINE_STYLES[hist_stat]
        pen = pg.mkPen(color=style[0], style=style[1])

        # Create new lines
        new_time_press = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)
        new_time_slope = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)
        new_time_switch = pg.InfiniteLine(pos=time, angle=90, movable=False, pen=pen)

        # Assign new lines to attributes
        if event.event_type == Event.PRESSURIZE:
            self.press_time_press = new_time_press
            self.press_time_slope = new_time_slope
            self.press_time_switch = new_time_switch
        else:
            self.depress_time_press = new_time_press
            self.depress_time_slope = new_time_slope
            self.depress_time_switch = new_time_switch

        # Add new lines to plots
        self.pressure_plot.addItem(new_time_press)
        self.slope_plot.addItem(new_time_slope)
        self.switch_time_plot.addItem(new_time_switch)

    def set_sample_sensor(self, connected):
        self.pressure_plot.toggle_line_visibility(HistStat.S_PRESS, connected)
        self.slope_plot.toggle_line_visibility(HistStat.PS_SLOPE, connected)
        self.slope_plot.toggle_line_visibility(HistStat.DS_SLOPE, connected)
        self.switch_time_plot.toggle_line_visibility(HistStat.PS_SWITCH, connected)
        self.switch_time_plot.toggle_line_visibility(HistStat.DS_SWITCH, connected)

    def set_log_coefficients(self, coefficients):
        self.log_coefficients = self.define_coefficients(coefficients)

    def update_theme(self):
        self.pressure_plot.update_theme()
        self.pressure_plot.set_title("Pressure")
        self.pressure_plot.set_y_label('Pressure (kBar)')
        self.pressure_plot.set_x_label('Time (s)')

        self.slope_plot.update_theme()
        self.slope_plot.set_title("Pressure Change Slope")
        self.slope_plot.set_y_label('Slope (kBar/ms)')
        self.slope_plot.set_x_label('Time (s)')

        self.switch_time_plot.update_theme()
        self.switch_time_plot.set_title("Switch Time")
        self.switch_time_plot.set_y_label('Time (ms)')
        self.switch_time_plot.set_x_label('Time (s)')

        from icarus_v2.gui.styled_plot_widget import theme
        color = self.get_line_styles(theme)["origin pressure"][0]
        size = 14
        self.last_pressure_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_pressure_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.last_pressure_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_pressure_label.setStyleSheet(f"color: {color}; font-size: {size}px;")

        color = self.get_line_styles(theme)["press origin slope"][0]
        self.last_press_slope_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_press_slope_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.last_press_slope_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_press_slope_label.setStyleSheet(f"color: {color}; font-size: {size}px;")

        color = self.get_line_styles(theme)["press origin switch"][0]
        self.last_press_switch_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_press_switch_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.last_press_switch_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_press_switch_label.setStyleSheet(f"color: {color}; font-size: {size}px;")

        color = self.get_line_styles(theme)["depress origin slope"][0]
        self.last_depress_slope_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_depress_slope_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.last_depress_slope_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_depress_slope_label.setStyleSheet(f"color: {color}; font-size: {size}px;")

        color = self.get_line_styles(theme)["depress origin switch"][0]
        self.last_depress_switch_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_depress_switch_display.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.last_depress_switch_label.setStyleSheet(f"color: {color}; font-size: {size}px;")
        self.avg_depress_switch_label.setStyleSheet(f"color: {color}; font-size: {size}px;")

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

        style = self.LINE_STYLES["origin pressure"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["origin pressure"] = self.pressure_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["sample pressure"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["sample pressure"] = self.pressure_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["origin pressure"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["origin pressure"] = self.pressure_plot.plot([], [], pen=pen)
        style = self.LINE_STYLES["sample pressure"]
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines["sample pressure"] = self.pressure_plot.plot([], [], pen=pen)


    def get_line_styles(self, theme):
        return {
            "origin pressure": (THEME_COLOR_VALUES[theme]['line']['yellow'], Qt.SolidLine),  # yellow
            "sample pressure": (THEME_COLOR_VALUES[theme]['line']['yellow'], Qt.DashLine),  # yellow dashed
            "depress origin slope": (THEME_COLOR_VALUES[theme]['line']['cyan'], Qt.SolidLine),  # cyan
            "depress sample slope": (THEME_COLOR_VALUES[theme]['line']['cyan'], Qt.DashLine),  # cyan dashed
            "press origin slope": (THEME_COLOR_VALUES[theme]['line']['red'], Qt.SolidLine),  # red
            "press sample slope": (THEME_COLOR_VALUES[theme]['line']['red'], Qt.DashLine),  # red dashed
            "depress origin switch": (THEME_COLOR_VALUES[theme]['line']['cyan'], Qt.SolidLine),  # cyan
            "depress sample switch": (THEME_COLOR_VALUES[theme]['line']['cyan'], Qt.DashLine),  # cyan dashed
            "press origin switch": (THEME_COLOR_VALUES[theme]['line']['red'], Qt.SolidLine),  # red
            "press sample switch": (THEME_COLOR_VALUES[theme]['line']['red'], Qt.DashLine),  # red dashed
        }

    # Dictionary of coefficient to apply when plotting each channel
    @staticmethod
    def define_coefficients(plotting_coefficients):
        if plotting_coefficients is None:
            return None
        # Dictionary of coefficient to apply when plotting each channel
        coefficients = {
            HistStat.O_PRESS: plotting_coefficients[Channel.HI_PRE_ORIG],
            HistStat.S_PRESS: plotting_coefficients[Channel.HI_PRE_SAMPLE],
            HistStat.DO_SLOPE: plotting_coefficients[Channel.HI_PRE_ORIG] * 4,
            HistStat.DS_SLOPE: plotting_coefficients[Channel.HI_PRE_SAMPLE] * 4,
            HistStat.PO_SLOPE: plotting_coefficients[Channel.HI_PRE_ORIG] * 4,
            HistStat.PS_SLOPE: plotting_coefficients[Channel.HI_PRE_SAMPLE] * 4,
            HistStat.DO_SWITCH: 0.25,
            HistStat.DS_SWITCH: 0.25,
            HistStat.PO_SWITCH: 0.25,  # ms per index
            HistStat.PS_SWITCH: 0.25,  # ms per index
        }
        return coefficients
