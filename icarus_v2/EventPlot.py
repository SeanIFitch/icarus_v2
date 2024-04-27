from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from Channel import Channel, get_channel
from Event import Event
from PySide6.QtWidgets import QLabel, QGridLayout, QWidget


class EventPlot(QWidget):
    # Dictionary of color to plot each channel
    PENS = {
        Channel.TARGET: pg.mkPen(color='#45BF55', style=Qt.SolidLine),          # light green
        Channel.DEPRE_LOW: pg.mkPen(color='#AB47BC', style=Qt.SolidLine),       # magenta
        Channel.DEPRE_UP: pg.mkPen(color='#004B8D', style=Qt.SolidLine),        # blue
        Channel.PRE_LOW: pg.mkPen(color='#AB47BC', style=Qt.SolidLine),         # magenta
        Channel.PRE_UP: pg.mkPen(color='#004B8D', style=Qt.SolidLine),          # blue
        Channel.HI_PRE_ORIG: pg.mkPen(color='#FFDC00', style=Qt.SolidLine),     # yellow
        Channel.HI_PRE_SAMPLE: pg.mkPen(color='#FFDC00', style=Qt.DashLine),    # yellow dashed
        Channel.DEPRE_VALVE: pg.mkPen(color='#59D8E6', style=Qt.SolidLine),     # cyan
        Channel.PRE_VALVE: pg.mkPen(color='#B9121B', style=Qt.SolidLine),       # red
    }

    def __init__(self, event_type, config_manager):
        super().__init__()

        self.event_type = event_type
        self.config_manager = config_manager
        self.config_manager.settings_updated.connect(self.update_settings)
        self.coefficients = config_manager.get_settings("plotting_coefficients")
        display_channels = [Channel.TARGET, Channel.HI_PRE_SAMPLE, Channel.HI_PRE_ORIG, Channel.DEPRE_VALVE, Channel.PRE_VALVE]

        if event_type == Event.PRESSURIZE:
            display_channels += [Channel.PRE_LOW, Channel.PRE_UP]
            self.x_unit = 'ms'
            title = "Pressurize"
            #self.plot.setXRange(-10, 140)
        elif event_type == Event.DEPRESSURIZE:
            display_channels += [Channel.DEPRE_LOW, Channel.DEPRE_UP]
            self.x_unit = 'ms'
            title = "Depressurize"
            #self.plot.setXRange(-10, 140)
        elif event_type == Event.PERIOD:
            self.x_unit = 's'
            title = "Period"


        self.plot = pg.PlotWidget(background= self.palette().color(QPalette.Window))
        self.plot.showGrid(x=True, y=True)
        #self.setYRange(0, 3)
        self.plot.setMouseEnabled(x=False, y=False) # Prevent zooming
        self.plot.hideButtons() # Remove autoScale button
        # Labels
        text_color = self.palette().color(QPalette.WindowText)
        self.plot.setTitle(title, color=text_color, size="14pt")
        self.plot.setLabel('left', 'Pressure (kbar)', **{'color':text_color})
        self.plot.setLabel('bottom', f'Time ({self.x_unit})', **{'color':text_color})

        # Create a dictionary of lines for each channel listed in display_channels
        self.line_references = {}
        for channel in display_channels:
            self.line_references[channel] = self.plot.plot([], [], pen=self.PENS[channel])

        labels = self.init_labels()

        # Set layout
        layout = QGridLayout()
        layout.addWidget(self.plot, 0, 0)
        layout.addLayout(labels, 0, 0, Qt.AlignRight | Qt.AlignTop)
        self.setLayout(layout)


    def init_labels(self):
        layout = QGridLayout()
        if self.event_type == Event.PRESSURIZE:
            self.pressurize_display = QLabel("0")
            pressurize_label = QLabel("Pressurize Width (ms):")
            layout.addWidget(pressurize_label, 0, 0)
            layout.addWidget(self.pressurize_display, 0, 1)

        elif self.event_type == Event.DEPRESSURIZE:
            self.depressurize_display = QLabel("0")
            depressurize_label = QLabel("Depressurize Width (ms):")
            layout.addWidget(depressurize_label, 1, 0)
            layout.addWidget(self.depressurize_display, 1, 1)

        elif self.event_type == Event.PERIOD:
            self.period_display = QLabel("0")
            self.delay_display = QLabel("0")
            period_label = QLabel("Period (s):")
            delay_label = QLabel("Delay (s):")
            layout.addWidget(period_label, 0, 0)
            layout.addWidget(delay_label, 1, 0)
            layout.addWidget(self.period_display, 0, 1)
            layout.addWidget(self.delay_display, 1, 1)

        #layout.setContentsMargins(0, title_height, 0, 0)
        return layout



    def update_data(self, event):
        data = event.data
        # Calculate times based on event.data_end_time and event_index
        time_before_event = - event.data_end_time * event.event_index / (len(data) - event.event_index)
        times = np.linspace(time_before_event, event.data_end_time, len(data))
        if self.x_unit == "s":
            times /= 1000

        # update data for each line
        for channel, line_reference in self.line_references.items():
            coefficient = self.coefficients[channel]
            line_reference.setData(times, get_channel(data, channel) * coefficient)

        # Update timings labels
        if event.event_type == Event.PRESSURIZE:
            pressurize_width = event.get_valve_open_time() / 4
            self.pressurize_display.setText(f"{pressurize_width:.2f}")

        elif event.event_type == Event.DEPRESSURIZE:
            depressurize_width = event.get_valve_open_time() / 4
            self.depressurize_display.setText(f"{depressurize_width:.2f}")

        elif event.event_type == Event.PERIOD:
            period_width = event.get_period_width()
            delay_width = event.get_delay_width()
            self.period_display.setText(f"{period_width:.2f}")
            self.delay_display.setText(f"{delay_width:.2f}")


    def update_settings(self, key):
        if key == "plotting_coefficients":
            self.coefficients = self.config_manager.get_settings(key)
