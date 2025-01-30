from pyqtgraph import PlotWidget
from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ButtonItem import ButtonItem
from PySide6.QtCore import QEvent
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QFileDialog, QLabel, QSizePolicy
from icarus_v2.backend.csv_exporter import CSVExporter
import numpy as np
from bisect import bisect_left, bisect_right


class StyledPlotWidget(PlotWidget):
    def __init__(self, x_zoom=False):
        theme = 'dark' #TODO: know that this is here
        background = THEME_COLOR_VALUES[theme]['background']['base']
        self.text_color = THEME_COLOR_VALUES[theme]['foreground']['base']
        self.full_init=False
        PlotWidget.__init__(self, background=background)

        self.showGrid(x=True, y=True)
        self.setMouseEnabled(x=x_zoom, y=False)  # Prevent zooming
        self.hideButtons()  # Remove autoScale button
        self.getPlotItem().getViewBox().setMenuEnabled(False) # Remove right click menu

        # Set up the export button
        self.exportBtn = ButtonItem("src/icarus_v2/resources/export_icon.svg", 20,self.plotItem)
        self.exportBtn.clicked.connect(self.export_clicked)
        self.exportBtn.setPos(0,210)
        self.exportBtn.hide()

        # Enable hover events. Needed so that button is only visible when hovering over graph
        self.setAttribute(Qt.WA_Hover)

        # Lines
        self.lines = {}
        self.line_visibility = {}

        # Export functionality
        self.default_filename = "icarus_graph"
        self.folder = None
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

    def set_title(self, title):
        self.setTitle(title, color=self.text_color, size="17pt")

    def set_y_label(self, label):
        self.test_label=label
        self.setLabel('left', label, **{'color': self.text_color})

    def set_x_label(self, label):
        self.setLabel('bottom', label, **{'color': self.text_color})

    # Add a new line to the plot with given style.
    def add_line(self, identifier, color, line_style=Qt.SolidLine):
        pen = pg.mkPen(color=color, style=line_style)
        self.lines[identifier] = self.plot([], [], name=str(identifier), pen=pen)
        self.line_visibility[identifier] = True
        return self.lines[identifier]

    # Update data for a specific line.
    def update_line_data(self, identifier, x_data, y_data, srate=None):
        if identifier in self.lines:
            self.lines[identifier].setData(x_data, y_data)

            # Update statistics if they exist for this line
            if identifier in self.statistics:
                for format_str, stat_info in self.statistics[identifier].items():
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
            points_dict: Dictionary mapping line identifiers to y values
            time: x value (time) for all points
        """
        for identifier, y_point in points_dict.items():
            if identifier in self.lines:
                line = self.lines[identifier]
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
    def toggle_line_visibility(self, identifier, visible):
        if identifier in self.lines:
            if visible and not self.line_visibility[identifier]:
                self.addItem(self.lines[identifier])
            elif not visible and self.line_visibility[identifier]:
                self.removeItem(self.lines[identifier])
            self.line_visibility[identifier] = visible

    def add_statistic(self, identifier, method, format_str, size=14):
        """
        Add a statistic display for a specific line.

        Args:
            identifier: The line identifier this statistic is associated with
            method: Function that takes an array and returns the statistic value
            format_str: Format string for the value (e.g., "Avg: {:.3f}")
            size: Font size in pixels
        """
        if identifier not in self.lines:
            raise KeyError(f"Line with identifier '{identifier}' does not exist")

        label = QLabel(format_str.format(0))
        line_color = self.lines[identifier].opts['pen'].color().name()
        label.setStyleSheet(f"color: {line_color}; font-size: {size}px;")

        # Add to layout
        label.setFixedSize(200, 18)
        label.setAlignment(Qt.AlignRight)
        self.stat_layout.addWidget(label, alignment=Qt.AlignRight)

        # Store the statistic info
        if identifier not in self.statistics:
            self.statistics[identifier] = {}
        self.statistics[identifier][format_str] = {
            'method': method,
            'label': label,
        }

    def update_statistics(self):
        """
        Update all statistics based on currently visible data
        """
        for identifier, stats in self.statistics.items():
            for format_str, stat_info in stats.items():
                if identifier in self.lines:
                    line = self.lines[identifier]
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

    # Clear all line data.
    def reset(self):
        for line in self.lines.values():
            line.setData([], [])

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
            self.exportBtn.show()
        elif event.type() == QEvent.HoverLeave:
            self.mouse_label.setText("")
            self.exportBtn.hide()
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
        png_button.clicked.connect(self.export_png)
        csv_button.clicked.connect(self.export_csv)
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

    def export_png(self):
        self.edit_dialog.close()

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save PNG",
            self.default_filename + ".png",
            "PNG Files (*.png)",
            options=options
        )

        if not filename:
            self.edit_dialog.close()
            return

        if not filename.endswith('.png'):
            filename += '.png'

        exporter = pg.exporters.ImageExporter(self.plotItem)
        exporter.parameters()['width'] = 650
        exporter.export(filename)
        self.edit_dialog.close()

    def export_csv(self):
        self.edit_dialog.close()

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            self.default_filename + ".csv",
            "CSV Files (*.csv)",
            options=options
        )

        if not filename:
            self.edit_dialog.close()
            return

        if not filename.endswith('.csv'):
            filename += '.csv'

        exporter = CSVExporter(self.plotItem)
        exporter.export(filename)
        self.edit_dialog.close()

    def resizeEvent(self, event):
        """Update the export button position based on the plot's size."""
        super().resizeEvent(event)

        if hasattr(self, 'exportBtn'):
            plot_height = self.height()

            button_y = plot_height - 24  # 85% from the top

            # Update button position and size
            self.exportBtn.setPos(0, button_y)

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
