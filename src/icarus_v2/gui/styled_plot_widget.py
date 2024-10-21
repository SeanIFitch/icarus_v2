from pyqtgraph import PlotWidget
from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES

import pyqtgraph as pg
from pyqtgraph.graphicsItems.ButtonItem import ButtonItem
from pyqtgraph import icons
from pyqtgraph import PlotItem
import PySide6
from PySide6.QtCore import QEvent
from PySide6.QtGui import Qt
# import pyqtgraph.exporters
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
        self.exportBtn = ButtonItem(icons.getGraphPixmap('auto'), 14,self.plotItem)
        self.exportBtn.clicked.connect(self.exportBtnClicked)
        self.exportBtn.setPos(30,210)
        self.exportBtn.hide()

        #Enable hover events. Needed so that button is only visible when hovering over graph
        self.setAttribute(Qt.WA_Hover)

        self.csv_header = None


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

        print("Click")

    def export_png(self, filename):

        exporter = pg.exporters.ImageExporter(self.plotItem)


        # set export parameters if needed

        #TODO: figure out dimensions for graph

        exporter.parameters()['width'] = 650   # (note this also affects height parameter)


        # save to file

        exporter.export(filename+'.png')


    def export_csv(self, filename):

        exporter = CustomCSVExporter(self.plotItem)


        # save to file

        exporter.export(filename+'.csv',self.csv_header)