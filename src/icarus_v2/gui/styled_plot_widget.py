from pyqtgraph import PlotWidget
from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES

import os
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ButtonItem import ButtonItem
from pyqtgraph import icons
from pyqtgraph import PlotItem
import PySide6
from PySide6.QtCore import QEvent
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QFileDialog
from icarus_v2.backend.custom_csv_exporter import CustomCSVExporter

class StyledPlotWidget(PlotWidget):
    def __init__(self, x_zoom=False):
        theme = 'dark' #TODO: know that this is here
        background = THEME_COLOR_VALUES[theme]['background']['base']
        self.text_color = THEME_COLOR_VALUES[theme]['foreground']['base']
        PlotWidget.__init__(self, background=background)

        self.showGrid(x=True, y=True)
        self.setMouseEnabled(x=x_zoom, y=False)  # Prevent zooming
        self.hideButtons()  # Remove autoScale button
        self.getPlotItem().getViewBox().setMenuEnabled(False) # Remove right click menu

        #Setup the export button
        self.exportBtn = ButtonItem("src/icarus_v2/resources/export_icon.svg", 20,self.plotItem)
        self.exportBtn.clicked.connect(self.exportBtnClicked)
        self.exportBtn.setPos(30,210)
        self.exportBtn.hide()

        #Enable hover events. Needed so that button is only visible when hovering over graph
        self.setAttribute(Qt.WA_Hover)

        self.csv_header = None
        self.default_filename = "icarus_graph"
        self.folder = None


    def set_title(self, title):
        self.setTitle(title, color=self.text_color, size="17pt")

    def set_y_label(self, label):
        self.test_label=label
        self.setLabel('left', label, **{'color': self.text_color})

    def set_x_label(self, label):
        self.setLabel('bottom', label, **{'color': self.text_color})

    '''
    #Formatting for header is array of strings with x as the first values
    #Ex: ["X","Graph1","Graph2","Graph3"]
    '''
    def set_csv_header(self,csv_header):
        self.csv_header = csv_header

    #Tracks the hover enter and leave events
    def event(self, event):
        if event.type() == QEvent.HoverEnter:
            self.exportBtn.show()
        elif event.type() == QEvent.HoverLeave:
            self.exportBtn.hide()
        return super().event(event)

    def exportBtnClicked(self):
        self.edit_dialog = QDialog(self)

        self.export_file = QLineEdit()
        self.export_file.setText(self.default_filename)
        extension_length = len(self.default_filename.split('.')[-1]) + 1
        self.export_file.setSelection(0, len(self.default_filename) - extension_length)

        folder_button = QPushButton("Choose Folder")
        folder_button.clicked.connect(self.export_folder)

        png_button = QPushButton("Export as PNG")
        csv_button = QPushButton("Export as CSV")
        png_button.clicked.connect(self.export_png)
        csv_button.clicked.connect(self.export_csv)

        layout = QVBoxLayout()
        layout.addWidget(self.export_file)
        layout.addWidget(folder_button)
        layout.addWidget(png_button)
        layout.addWidget(csv_button)

        self.edit_dialog.setWindowTitle("Export Graph")
        self.edit_dialog.setFixedSize(500, 200)
        self.edit_dialog.setLayout(layout)
        self.edit_dialog.show()

    #Allows the user to choose the directory for the export
    def export_folder(self):
        #This is how to get the folder
        self.folder = QFileDialog.getExistingDirectory(self, 'Select Folder')

    def export_png(self, filename=None):
        if(not filename):
            if(self.export_file is None):
                filename = self.default_filename 
            else:
                filename = self.export_file.text()
                self.edit_dialog.done(0)

        exporter = pg.exporters.ImageExporter(self.plotItem)

        # set export parameters if needed
        exporter.parameters()['width'] = 650   # (note this also affects height parameter)

        # save to file
        if(self.folder is not None and self.folder!=""):
            exporter.export(self.folder+"/"+filename+'.png')
        else:
            exporter.export(filename+'.png')

    def export_csv(self, filename):
        if(not filename):
            if(self.export_file is None):
                filename = self.default_filename
            else:
                filename = self.export_file.text()
                self.edit_dialog.done(0)

        exporter = CustomCSVExporter(self.plotItem)

        # save to file
        if(self.folder is not None and self.folder!=""):
            exporter.export(self.folder+"/"+filename+'.csv',self.csv_header)
        else:
            exporter.export(filename+'.csv',self.csv_header)