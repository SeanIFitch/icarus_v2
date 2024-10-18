from pyqtgraph import PlotWidget

from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES

import pyqtgraph as pg

from pyqtgraph.graphicsItems.ButtonItem import ButtonItem

from pyqtgraph import icons

from pyqtgraph import PlotItem

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

        self.exportBtn = ButtonItem(icons.getGraphPixmap('auto'), 14,self.plotItem)
        self.exportBtn.clicked.connect(self.exportBtnClicked)
        self.exportBtn.setPos(30,210)
        self.exportBtn.hide()
        # self.scene.sigMouseMoved

        self.btn_proxy = pg.SignalProxy(self.scene().sigMouseHover, rateLimit=120, slot=self.hovering)


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

    def hovering(self):  
        self.exportBtn.show()

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