import csv
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QCoreApplication
import pyqtgraph.exporters


translate = QCoreApplication.translate


# Custom override of CSVExporter class
# Adds functionality to override auto-generated csv headers with custom ones
class CSVExporter(pg.exporters.CSVExporter):
    def __init__(self, item):
        pg.exporters.CSVExporter.__init__(self, item)

    def export(self, filename=None):
        # Initialize variables
        header = ["Time"]  # Start with Time column
        time_columns = []
        data_columns = []
        data_names = []

        # Collect data from all plot items
        for item in self.item.items:
            if hasattr(item, 'implements') and item.implements('plotData'):
                cd = item.getOriginalDataset()
                time_columns.append(cd[0])  # Store x-axis data
                data_columns.append(cd[1])  # Store y-axis data
                data_names.append(item.name().replace(' ', '_'))
                header.append(item.name().replace(' ', '_'))

        # Get unique sorted timestamps from all time columns
        filtered_columns = [arr for arr in time_columns if arr is not None]
        merged_time = np.unique(np.concatenate(filtered_columns)) if filtered_columns else np.array([])

        if len(merged_time) > 0:
            merged_time.sort()

            # Create a lookup dictionary for each data series
            series_data = {name: {} for name in data_names}
            for i in range(len(time_columns)):
                if time_columns[i] is not None:
                    series_data[data_names[i]] = dict(zip(time_columns[i], data_columns[i]))

            # First add the time column
            row_data = [merged_time]

            # Add data columns
            for name in data_names:
                column_data = []
                for t in merged_time:
                    value = series_data[name].get(t, "")
                    # Convert DIO values to int if necessary
                    if "DIO" in name and value != "":
                        value = int(bool(value))
                    column_data.append(value)
                row_data.append(column_data)

            # Transpose the data for writing
            output_data = list(map(list, zip(*row_data)))

        else:
            output_data = None

        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header)

            if output_data is not None:
                writer.writerows(output_data)

        self.data.clear()
