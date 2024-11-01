import csv
import itertools

import numpy as np

import pyqtgraph as pg
from pyqtgraph.graphicsItems import ErrorBarItem, PlotItem
# from ..parametertree import Parameter
from PySide6.QtCore import QCoreApplication

# from ..Qt import QtCore
import pyqtgraph.exporters

translate = QCoreApplication.translate

# __all__ = ['CustomCSVExporter']
    
    
'''
#Custom override of CSVExporter class
#Adds functionality to override auto-generated csv headers with custom ones
#Only exports the x values for the first data item
'''
class CustomCSVExporter(pg.exporters.CSVExporter):
    def __init__(self, item):
        pg.exporters.CSVExporter.__init__(self, item)

    def _exportPlotDataItem(self, plotDataItem, useX=True) -> None:
        if hasattr(plotDataItem, 'getOriginalDataset'):
            # try to access unmapped, unprocessed data
            cd = plotDataItem.getOriginalDataset()
        else:
             # fall back to earlier access method
            cd = plotDataItem.getData()
        if cd[0] is None:
            # no data found, break out...
            return None
        
        if useX:
            self.data.append(cd[0])

        #Only adding cd[1] so that we don't have x values repeated
        self.data.append(cd[1])

        index = next(self.index_counter)
        if plotDataItem.name() is not None:
            name = plotDataItem.name().replace('"', '""') + '_'
            xName = f"{name}x"
            yName = f"{name}y"
        else:
            xName = f'x{index:04}'
            yName = f'y{index:04}'
        appendAllX = self.params['columnMode'] == '(x,y) per plot'
        if (appendAllX or index == 0) and useX:
            self.header.extend([xName, yName])
        else:
            self.header.extend([yName])
        return None

    def export(self, fileName=None, custom_header=None):
        if not isinstance(self.item, PlotItem.PlotItem):
            raise TypeError("Must have a PlotItem selected for CSV export.")

        if fileName is None:
            self.fileSaveDialog(filter=["*.csv", "*.tsv"])
            return

        needX=True

        for item in self.item.items:
            if isinstance(item, ErrorBarItem.ErrorBarItem):
                self._exportErrorBarItem(item)
            elif hasattr(item, 'implements') and item.implements('plotData'):
                self._exportPlotDataItem(item,needX)
                needX=False

        if(custom_header is not None):
            # print("CUstom")
            self.header = custom_header

        sep = "," if self.params['separator'] == 'comma' else "\t"
        # we want to flatten the nested arrays of data into columns
        # columns = [column for dataset in self.data for column in dataset]
        columns = [column for column in self.data]
        with open(fileName, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=sep, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(self.header)
            for row in itertools.zip_longest(*columns, fillvalue=""):
                row_to_write = [
                    item if isinstance(item, str) 
                    else np.format_float_positional(
                        item, precision=self.params['precision']
                    )
                    for item in row
                ]
                writer.writerow(row_to_write)

        self.data.clear()

# CustomCSVExporter.register()
