from pyqtgraph import PlotWidget
from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ButtonItem import ButtonItem
from PySide6.QtCore import QEvent
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QFileDialog, QLabel, QGridLayout, QSizePolicy
from icarus_v2.backend.custom_csv_exporter import CustomCSVExporter

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

        #Enable hover events. Needed so that button is only visible when hovering over graph
        self.setAttribute(Qt.WA_Hover)

        self.csv_header = None
        self.default_filename = "icarus_graph"
        self.folder = None
        self.edit_dialog = None

        #Mouse coordinates
        self.mouse_label = QLabel("")
        size = 14
        self.mouse_label.setStyleSheet(f"font-size: {size}px;")
        self.mouse_label.setFixedSize(70, 16)  # Locks label at specific size. Removal will cause UI errors

        layout = QGridLayout()
        layout.addWidget(self.mouse_label, 3, 0, 1, 2, Qt.AlignRight | Qt.AlignBottom)
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

    # Formatting for header is array of strings with x as the first values
    # Ex: ["X","Graph1","Graph2","Graph3"]
    def set_csv_header(self,csv_header):
        self.csv_header = csv_header

    # Activates whenever the mouse hovers over or leaves the graph
    # - Makes the export button visible only when the mouse is hovering over the graph
    # - Makes the mouse coordinates appear when the mouse is hovering over the graph
    def event(self, event):
        if(not self.full_init):
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

        exporter = CustomCSVExporter(self.plotItem)
        exporter.export(filename, self.csv_header)
        self.edit_dialog.close()

    def resizeEvent(self, event):
        """Update the export button position based on the plot's size."""
        super().resizeEvent(event)

        if hasattr(self, 'exportBtn'):
            plot_height = self.height()

            button_y = plot_height - 24  # 85% from the top

            # Update button position and size
            self.exportBtn.setPos(0, button_y)
