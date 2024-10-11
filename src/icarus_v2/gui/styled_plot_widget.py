from pyqtgraph import PlotWidget
from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES


class StyledPlotWidget(PlotWidget):
    def __init__(self, x_zoom=False):
        theme = 'dark'
        background = THEME_COLOR_VALUES[theme]['background']['base']
        self.text_color = THEME_COLOR_VALUES[theme]['foreground']['base']
        PlotWidget.__init__(self, background=background)

        self.showGrid(x=True, y=True)
        self.setMouseEnabled(x=x_zoom, y=False)  # Prevent zooming
        self.hideButtons()  # Remove autoScale button

    def set_title(self, title):
        self.setTitle(title, color=self.text_color, size="17pt")

    def set_y_label(self, label):
        self.setLabel('left', label, **{'color': self.text_color})

    def set_x_label(self, label):
        self.setLabel('bottom', label, **{'color': self.text_color})
