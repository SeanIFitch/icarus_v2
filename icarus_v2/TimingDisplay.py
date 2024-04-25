from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel
)
from Event import Event


# Panel for counts of valves and such
class TimingDisplay(QGroupBox):
    def __init__(self):
        super().__init__()

        # Displays
        self.pressurize_display = QLabel("0")
        self.depressurize_display = QLabel("0")
        self.period_display = QLabel("0")
        self.delay_display = QLabel("0")

        # Labels
        pressurize_label = QLabel("Pressurize Width (ms):")
        depressurize_label = QLabel("Depressurize Width (ms):")
        period_label = QLabel("Period (s):")
        delay_label = QLabel("Delay (s):")

        # Set main layout
        layout = QGridLayout()
        layout.addWidget(pressurize_label, 0, 0)
        layout.addWidget(depressurize_label, 1, 0)
        layout.addWidget(period_label, 2, 0)
        layout.addWidget(delay_label, 3, 0)
        layout.addWidget(self.pressurize_display, 0, 1)
        layout.addWidget(self.depressurize_display, 1, 1)
        layout.addWidget(self.period_display, 2, 1)
        layout.addWidget(self.delay_display, 3, 1)

        self.setLayout(layout)


    def update_widths(self, event):
        if event.event_type == Event.PRESSURIZE:
            pressurize_width = event.get_valve_open_time()
            self.pressurize_display.setText(f"{pressurize_width:.2f}")

        elif event.event_type == Event.DEPRESSURIZE:
            depressurize_width = event.get_valve_open_time()
            self.depressurize_display.setText(f"{depressurize_width:.2f}")

        elif event.event_type == Event.PERIOD:
            period_width = event.get_period_width()
            delay_width = event.get_delay_width()
            self.period_display.setText(f"{period_width:.2f}")
            self.delay_display.setText(f"{delay_width:.2f}")
