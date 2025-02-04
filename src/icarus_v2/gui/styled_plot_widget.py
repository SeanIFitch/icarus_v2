import os
from pyqtgraph import PlotWidget
from icarus_v2.backend.configuration_manager import ConfigurationManager
from icarus_v2.backend.event import Channel, HistStat, Event
from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES, ACCENT_COLORS, url, color
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ButtonItem import ButtonItem
from PySide6.QtCore import QEvent, QStandardPaths
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QFileDialog, QLabel, QSizePolicy
from icarus_v2.backend.csv_exporter import CSVExporter
import numpy as np
from bisect import bisect_left, bisect_right


class StyledPlotWidget(PlotWidget):
    def __init__(self, x_zoom=False):
        self.full_init=False

        self.config_manager = ConfigurationManager()
        self.config_manager.settings_updated.connect(self.update_theme)

        background = self.get_background_color()
        PlotWidget.__init__(self, background=background)

        self.showGrid(x=True, y=True, alpha=0.3)
        self.setMouseEnabled(x=x_zoom, y=False)  # Prevent zooming
        self.hideButtons()  # Remove autoScale button
        self.getPlotItem().getViewBox().setMenuEnabled(False) # Remove right click menu

        # Set up the export button
        self.export_button = ButtonItem( width=20, parentItem=self.plotItem)
        self.export_button.clicked.connect(self.export_clicked)
        self.export_button.setPos(0, 210)
        self.export_button.hide()
        self.update_export_icon()

        # Enable hover events. Needed so that button is only visible when hovering over graph
        self.setAttribute(Qt.WA_Hover)

        # Lines
        self.lines = {}
        self.line_visibility = {}

        # Export functionality
        self.edit_dialog = None

        # Mouse coordinates
        self.mouse_label = QLabel("")
        size = 14
        self.mouse_label.setStyleSheet(f"font-size: {size}px;")
        self.mouse_label.setFixedSize(200, 17)
        self.mouse_label.setAlignment(Qt.AlignRight)

        # Add statistics tracking
        self.statistics = {}
        self.stat_displays = {}
        self.stat_layout = QVBoxLayout()
        if x_zoom:
            self.getPlotItem().getViewBox().sigStateChanged.connect(self.update_statistics)


        layout = QVBoxLayout()
        layout.addLayout(self.stat_layout)
        layout.addStretch(1)
        layout.addWidget(self.mouse_label, alignment=Qt.AlignRight)
        layout.setContentsMargins(0, 35, 5, 45)

        self.setLayout(layout)

        self.full_init=True

    def update_theme(self, settings_key: str | None = None, size: int = 14) -> None:
        # skip setting theme if this is triggered by settings updates
        if settings_key is not None and settings_key != "theme":
            return

        background = self.get_background_color()
        text_color = self.get_text_color()

        self.setBackground(background)

        plot = self.getPlotItem()
        plot.titleLabel.setText(plot.titleLabel.text, color=text_color)
        pen = pg.mkPen(color=text_color)
        plot.getAxis('left').setPen(pen)
        plot.getAxis('bottom').setPen(pen)

        for channel, line in self.lines.items():
            style = self.get_line_style(channel)
            pen = pg.mkPen(color=style[0], style=style[1])
            line.setPen(pen)

        for channel, stats in self.statistics.items():
            for _, stat_info in stats.items():
                line_color = self.get_line_style(channel)[0]
                stat_info['label'].setStyleSheet(f"color: {line_color}; font-size: {size}px;")

        self.update_export_icon()

    def set_title(self, title):
        text_color = self.get_text_color()
        self.setTitle(title, color=text_color, size="17pt")

    def set_y_label(self, label):
        text_color = self.get_text_color()
        self.setLabel('left', label, **{'color': text_color, 'font-size': '8pt'})

    def set_x_label(self, label):
        text_color = self.get_text_color()
        self.setLabel('bottom', label, **{'color': text_color, 'font-size': '8pt'})

    # Add a new line to the plot with given style.
    def add_line(self, channel):
        style = self.get_line_style(channel)
        pen = pg.mkPen(color=style[0], style=style[1])
        self.lines[channel] = self.plot([], [], name=str(channel), pen=pen)
        self.line_visibility[channel] = True
        return self.lines[channel]

    # Update data for a specific line.
    def update_line_data(self, channel, x_data, y_data, srate=None):
        if channel in self.lines:
            self.lines[channel].setData(x_data, y_data)

            # Update statistics if they exist for this line
            if channel in self.statistics:
                for format_str, stat_info in self.statistics[channel].items():
                    if len(y_data) > 0:
                        if srate is None:
                            value = stat_info['method'](y_data)
                        else:
                            value = stat_info['method'](y_data, srate)
                        stat_info['label'].setText(format_str.format(value))
                    else:
                        stat_info['label'].setText(format_str.format(0))

    def append_points(self, points_dict, x_point):
        """
        Append points at the same x value.

        Args:
            points_dict: Dictionary mapping line channels to y values
            x_point: x value
        """
        for channel, y_point in points_dict.items():
            if channel in self.lines:
                line = self.lines[channel]
                # Get existing data
                x_data, y_data = line.getData()
                if x_data is None:
                    x_data = []
                    y_data = []

                # Append new point
                x_data = np.append(x_data, x_point)
                y_data = np.append(y_data, y_point)

                # Update the line
                line.setData(x_data, y_data)

    # Show/hide a specific line.
    def toggle_line_visibility(self, channel, visible):
        if channel in self.lines:
            if visible and not self.line_visibility[channel]:
                self.addItem(self.lines[channel])
            elif not visible and self.line_visibility[channel]:
                self.removeItem(self.lines[channel])
            self.line_visibility[channel] = visible

    def add_statistic(self, channel, method, format_str, size=14):
        """
        Add a statistic display for a specific line.

        Args:
            channel: The line channel this statistic is associated with
            method: Function that takes an array and returns the statistic value
            format_str: Format string for the value (e.g., "Avg: {:.3f}")
            size: Font size in pixels
        """
        if channel not in self.lines:
            raise KeyError(f"Line with channel '{channel}' does not exist")

        label = QLabel(format_str.format(0))
        line_color = self.get_line_style(channel)[0]
        label.setStyleSheet(f"color: {line_color}; font-size: {size}px;")

        # Add to layout
        label.setFixedSize(200, 18)
        label.setAlignment(Qt.AlignRight)
        self.stat_layout.addWidget(label, alignment=Qt.AlignRight)

        # Store the statistic info
        if channel not in self.statistics:
            self.statistics[channel] = {}
        self.statistics[channel][format_str] = {
            'method': method,
            'label': label,
        }

    def update_statistics(self):
        """
        Update all statistics based on currently visible data
        """
        for channel, stats in self.statistics.items():
            for format_str, stat_info in stats.items():
                if channel in self.lines:
                    line = self.lines[channel]
                    x_data, y_data = line.getData()

                    if x_data is None:
                        stat_info['label'].setText(format_str.format(0))
                        continue

                    view_range = self.plotItem.viewRange()
                    x_min, x_max = view_range[0]  # Get current x-axis (time) range
                    start_idx = bisect_left(x_data, x_min)
                    end_idx = bisect_right(x_data, x_max)
                    visible_y_data = y_data[start_idx:end_idx]

                    if len(visible_y_data) > 0:
                        value = stat_info['method'](visible_y_data)
                        formatted_value = format_str.format(value)
                        stat_info['label'].setText(formatted_value)
                    else:
                        stat_info['label'].setText(format_str.format(0))

    def add_vertical_line(self, channel, x):
        if channel in self.lines:
            self.removeItem(self.lines[channel])

        if x is None:
            return

        line_color = self.get_line_style(channel)[0]
        pen = pg.mkPen(color=line_color)

        self.lines[channel] = pg.InfiniteLine(pos=x, angle=90, movable=False, pen=pen)
        self.addItem(self.lines[channel])

    # Clear all line data.
    def reset(self):
        for line in self.lines.values():
            if isinstance(line, pg.PlotDataItem):
                line.setData([], [])
            elif isinstance(line, pg.InfiniteLine):
                self.removeItem(line)

        for stats in self.statistics.values():
            for format_str, stat_info in stats.items():
                stat_info['label'].setText(format_str.format(0))

    # Activates whenever the mouse hovers over or leaves the graph
    # - Makes the export button visible only when the mouse is hovering over the graph
    # - Makes the mouse coordinates appear when the mouse is hovering over the graph
    def event(self, event):
        if not self.full_init:
            return super().event(event)

        if event.type() == QEvent.HoverEnter:
            self.export_button.show()
        elif event.type() == QEvent.HoverLeave:
            self.mouse_label.setText("")
            self.export_button.hide()
        elif event.type() == QEvent.HoverMove:
            mouse_point = self.getPlotItem().getViewBox().mapSceneToView(event.position())
            view_range = self.getPlotItem().getViewBox().viewRange()

            if (view_range[0][0] <= mouse_point.x() <= view_range[0][1] and
                view_range[1][0] <= mouse_point.y() <= view_range[1][1]):
                self.mouse_label.setText(f"{mouse_point.x():.2f}, {mouse_point.y():.2f}")
            else:
                self.mouse_label.setText("")

        return super().event(event)

    def export_clicked(self):
        self.edit_dialog = QDialog(self)

        png_button = QPushButton("Export as PNG")
        csv_button = QPushButton("Export as CSV")
        png_button.clicked.connect(lambda x: self.export('png'))
        csv_button.clicked.connect(lambda x: self.export('csv'))
        png_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        csv_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Ensure no button is selected by default
        png_button.setAutoDefault(False)
        csv_button.setAutoDefault(False)

        layout = QVBoxLayout()
        layout.addWidget(png_button)
        layout.addWidget(csv_button)

        self.edit_dialog.setWindowTitle("Export Graph")
        self.edit_dialog.setFixedSize(300, 150)
        self.edit_dialog.setLayout(layout)
        self.edit_dialog.show()

    def export(self, extension):
        self.edit_dialog.close()

        options = QFileDialog.Options()
        default_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        filename = self.getPlotItem().titleLabel.text.lower().replace(' ', '_') + f"_plot.{extension}"
        filename = os.path.join(default_dir, filename)

        # Check if the file already exists and modify the filename accordingly
        counter = 1
        while os.path.exists(filename):
            filename = filename.replace('.csv', f" ({counter}).{extension}")
            counter += 1

        filename, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {extension.upper()}",
            filename,
            f"{extension.upper()} Files (*.{extension})",
            options=options
        )

        if not filename:
            self.edit_dialog.close()
            return

        if not filename.endswith(f'.{extension}'):
            filename += f'.{extension}'

        if extension == 'csv':
            exporter = CSVExporter(self.plotItem)
        elif extension == 'png':
            exporter = pg.exporters.ImageExporter(self.plotItem)
            exporter.parameters()['width'] = 650
        else:
            raise RuntimeError(f"Unsupported file extension '{extension}'")

        exporter.export(filename)
        self.edit_dialog.close()

    def resizeEvent(self, event):
        """Update the export button position based on the plot's size."""
        super().resizeEvent(event)

        if hasattr(self, 'export_button'):
            plot_height = self.height()

            button_y = plot_height - 24  # 85% from the top

            # Update button position and size
            self.export_button.setPos(0, button_y)

    def get_view_state(self):
        """
        Check if the plot is currently fully zoomed out.
        Returns: bool indicating if the view shows the full data range
        """
        current_range = self.viewRange()[0]
        view_limits = self.getViewBox().state['limits']['xLimits']
        if view_limits is None:
            return True

        low_diff = current_range[0] - view_limits[0]
        hi_diff = view_limits[1] - current_range[1]
        return low_diff + hi_diff < 1

    def get_line_style(self, channel):
        theme = self.config_manager.get_settings('theme')

        match channel:
            case Channel.TARGET:
                return ACCENT_COLORS[theme]['light_green'], Qt.SolidLine
            case Channel.DEPRE_LOW | Channel.PRE_LOW:
                return ACCENT_COLORS[theme]['magenta'], Qt.SolidLine
            case Channel.DEPRE_UP | Channel.PRE_UP:
                return ACCENT_COLORS[theme]['blue'], Qt.SolidLine
            case Channel.HI_PRE_ORIG | HistStat.O_PRESS:
                return ACCENT_COLORS[theme]['yellow'], Qt.SolidLine
            case Channel.HI_PRE_SAMPLE | HistStat.S_PRESS:
                return ACCENT_COLORS[theme]['yellow'], Qt.DashLine
            case Channel.DEPRE_VALVE | HistStat.DO_SLOPE | HistStat.DO_SWITCH | Event.DEPRESSURIZE:
                return ACCENT_COLORS[theme]['cyan'], Qt.SolidLine
            case HistStat.DS_SLOPE | HistStat.DS_SWITCH:
                return ACCENT_COLORS[theme]['cyan'], Qt.DashLine
            case Channel.PRE_VALVE | HistStat.PO_SLOPE | HistStat.PO_SWITCH | Event.PRESSURIZE:
                return ACCENT_COLORS[theme]['red'], Qt.SolidLine
            case HistStat.PS_SLOPE | HistStat.PS_SWITCH:
                return ACCENT_COLORS[theme]['red'], Qt.DashLine
            case _:
                raise ValueError(f"Unknown channel: {channel}")

    def get_text_color(self):
        theme = self.config_manager.get_settings('theme')
        return THEME_COLOR_VALUES[theme]['foreground']['base']

    def get_background_color(self):
        theme = self.config_manager.get_settings('theme')
        return THEME_COLOR_VALUES[theme]['background']['base']

    def update_export_icon(self):
        theme = self.config_manager.get_settings('theme')
        color_info = THEME_COLOR_VALUES[theme]["foreground"]
        icon_color = color(color_info, state="icon")
        icon = url(icon_color, "file_export")[4:-1]  # Removes 'url(' at the start and ')' at the end
        self.export_button.setImageFile(icon)
