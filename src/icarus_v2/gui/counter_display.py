from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QSizePolicy
)
from icarus_v2.backend.event import Event
from PySide6.QtCore import QCoreApplication
import numpy as np


# Panel for counts of valves and such
class CounterDisplay(QGroupBox):
    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.config_manager.settings_updated.connect(self.update_settings)
        self.counts = config_manager.get_settings("counter_settings")
        QCoreApplication.instance().aboutToQuit.connect(self.save_settings)

        self.pump_times = []

        # Counters
        self.pump_counter = QLabel(str(self.counts["pump_count"]))
        self.pressurize_counter = QLabel(str(self.counts["pressurize_count"]))
        self.depressurize_counter = QLabel(str(self.counts["depressurize_count"]))
        self.stroke_display = QLabel("0.00")

        # Labels
        pump_count_label = QLabel("Pump Count:")
        pressurize_count_label = QLabel("Pressurize Count:")
        depressurize_count_label = QLabel("Depressurize Count:")
        stroke_display_label = QLabel("Pump Strokes/hr:")

        # Set main layout
        layout = QGridLayout()
        layout.addWidget(pump_count_label, 0, 0)
        layout.addWidget(pressurize_count_label, 1, 0)
        layout.addWidget(depressurize_count_label, 2, 0)
        layout.addWidget(stroke_display_label, 3, 0)
        layout.addWidget(self.pump_counter, 0, 1)
        layout.addWidget(self.pressurize_counter, 1, 1)
        layout.addWidget(self.depressurize_counter, 2, 1)
        layout.addWidget(self.stroke_display, 3, 1)

        self.setStyleSheet("font-size: 14pt;")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setLayout(layout)


    def increment_count(self, event):
        if event.event_type == Event.PUMP:
            self.counts["pump_count"] += 1
            self.pump_counter.setText(str(self.counts['pump_count']))

            # update pump strokes/hr
            self.pump_times.append(event.event_time)
            if len(self.pump_times) == 5:
                diff_in_sec = np.diff(self.pump_times).mean()
                strokes_per_hour = 3600 / diff_in_sec
                self.stroke_display.setText(f"{strokes_per_hour:.2f}")
                self.pump_times.pop(0)

        elif event.event_type == Event.PRESSURIZE:
            self.counts["pressurize_count"] += 1
            self.pressurize_counter.setText(str(self.counts['pressurize_count']))
        elif event.event_type == Event.DEPRESSURIZE:
            self.counts["depressurize_count"] += 1
            self.depressurize_counter.setText(str(self.counts['depressurize_count']))

        # Save counts to json every 100 updates
        if sum(self.counts.values()) % 100 == 0:
            # Do not emit so that this does not call self.update_settings
            self.save_settings()


    def save_settings(self):
        self.config_manager.save_settings("counter_settings", self.counts, emit=False)


    def update_settings(self, key):
        if key == 'counter_settings':
            self.counts = self.config_manager.get_settings(key)
            self.pump_counter.setText(str(self.counts['pump_count']))
            self.pressurize_counter.setText(str(self.counts['pressurize_count']))
            self.depressurize_counter.setText(str(self.counts['depressurize_count']))
