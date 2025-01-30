from pyqtgraph import PlotWidget
from icarus_v2.qdarktheme.load_style import THEME_COLOR_VALUES

theme = 'dark'


def change_theme(new_theme):
    global theme
    theme = new_theme

class StyledPlotWidget(PlotWidget):
    def __init__(self, x_zoom=False):
        background = THEME_COLOR_VALUES[theme]['background']['base']
        self.text_color = THEME_COLOR_VALUES[theme]['foreground']['base']
        PlotWidget.__init__(self, background=background)

        self.showGrid(x=True, y=True)
        self.setMouseEnabled(x=x_zoom, y=False)  # Prevent zooming
        self.hideButtons()  # Remove autoScale button
        self.setStyleSheet("padding: 0px; border: none;")
        self.getPlotItem().layout.setSpacing(0)  # No extra space between elements

    def update_theme(self):
        background = THEME_COLOR_VALUES[theme]['background']['base']
        self.text_color = THEME_COLOR_VALUES[theme]['foreground']['base']
        self.setBackground(background)

    def set_title(self, title):
        self.setTitle(title, color=self.text_color, size="17pt")

    def set_y_label(self, label):
        self.setLabel('left', label, **{'color': self.text_color, 'font-size': '9pt'})

    def set_x_label(self, label):
        self.setLabel('bottom', label, **{'color': self.text_color, 'font-size': '9pt'})
