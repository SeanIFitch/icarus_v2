import pyqtgraph as pg
from PySide6.QtWidgets import QApplication

def on_view_changed():
    print("View changed")

app = QApplication([])

pw = pg.PlotWidget()
pw.plot([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])

pw.getPlotItem().getViewBox().sigStateChanged.connect(on_view_changed)

pw.show()
app.exec_()