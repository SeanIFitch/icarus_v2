from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel
)
from PySide6.QtCore import Signal


# Panel for counts of valves and such
class CounterDisplay(QGroupBox):
    save_settings = Signal(bool)


    def __init__(self, settings):
        super().__init__()

        # Counters
        self.pump_count = settings["pump_count"]
        self.pressurize_count = settings["pressurize_count"]
        self.depressurize_count = settings["depressurize_count"]
        self.pump_counter = QLabel(str(self.pump_count))
        self.pressurize_counter = QLabel(str(self.pressurize_count))
        self.depressurize_counter = QLabel(str(self.depressurize_count))
        self.stroke_display = QLabel("0")

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

        self.setLayout(layout)


    def increment_pump_count(self):
        self.pump_count += 1
        self.pump_counter.setText(str(self.pump_count))

        # Save counts to json every 10000 updates
        if self.pump_count + self.pressurize_count + self.depressurize_count % 10000 == 0:
            self.save_settings.emit(True)


    def increment_pressurize_count(self):
        self.pressurize_count += 1
        self.pressurize_counter.setText(str(self.pressurize_count))

        # Save counts to json every 10000 updates
        if self.pump_count + self.pressurize_count + self.depressurize_count % 10000 == 0:
            self.save_settings.emit(True)

    def increment_depressurize_count(self):
        self.depressurize_count += 1
        self.depressurize_counter.setText(str(self.depressurize_count))

        # Save counts to json every 10000 updates
        if self.pump_count + self.pressurize_count + self.depressurize_count % 10000 == 0:
            self.save_settings.emit(True)
