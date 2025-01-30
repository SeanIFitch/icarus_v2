import csv
import itertools
import pyqtgraph as pg
from PySide6.QtCore import QCoreApplication
import pyqtgraph.exporters


translate = QCoreApplication.translate


# Custom override of CSVExporter class
# Adds functionality to override auto-generated csv headers with custom ones
# Only exports the x values (time) for the first data item
class CSVExporter(pg.exporters.CSVExporter):
    def __init__(self, item):
        pg.exporters.CSVExporter.__init__(self, item)


    def export(self, filename=None):
        first = True
        header = []

        for item in self.item.items:
            if hasattr(item, 'implements') and item.implements('plotData'):
                cd = item.getOriginalDataset()

                if first:
                    self.data.append(cd[0])
                    header.append("Time")

                self.data.append(cd[1])
                header.append(item.name().replace(' ', '_'))
                first=False

        columns = [column for column in self.data]

        for i in range(len(header)):
            if "DIO" in str(header[i]):
                if columns[i] is not None:
                    columns[i] = columns[i].astype(bool).astype(int)

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header)
            if columns[0] is not None:
                for row in itertools.zip_longest(*columns, fillvalue=""):
                    writer.writerow(row)

        self.data.clear()
