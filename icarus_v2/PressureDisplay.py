from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel
)


# Panel for pressure
class PressureDisplay(QGroupBox):
    def __init__(self):
        super().__init__()

        # Displays
        self.target_display = QLabel("0")
        self.sample_display = QLabel("0")

        # Labels
        main_label = QLabel("Pressure(kbar):")
        target_label = QLabel("Target:")
        sample_label = QLabel("Sample:")

        # Set main layout
        layout = QGridLayout()
        layout.addWidget(main_label, 0, 0)
        layout.addWidget(target_label, 1, 0)
        layout.addWidget(sample_label, 2, 0)
        layout.addWidget(self.target_display, 1, 1)
        layout.addWidget(self.sample_display, 2, 1)

        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)


    def update_target_pressure(self, target_pressure):
        self.target_display.setText(f"{target_pressure:.3f}")


    def update_sample_pressure(self, sample_pressure):
        self.sample_display.setText(f"{sample_pressure:.3f}")
