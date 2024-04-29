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

        # Font size
        main_label.setStyleSheet("font-size: 24px;")
        target_label.setStyleSheet("font-size: 20px;")
        sample_label.setStyleSheet("font-size: 20px;")
        self.target_display.setStyleSheet("font-size: 36px;")
        self.sample_display.setStyleSheet("font-size: 36px;")

        # Set main layout
        layout = QGridLayout()
        layout.addWidget(main_label, 0, 0, 1, 0)
        layout.addWidget(target_label, 1, 0)
        layout.addWidget(sample_label, 2, 0)
        layout.addWidget(self.target_display, 1, 1)
        layout.addWidget(self.sample_display, 2, 1)

        self.setFixedWidth(194)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)


    def update_pressure(self, event):
        target_pressure = event.get_target_pressure()
        sample_pressure = event.get_sample_pressure()
        self.target_display.setText(f"{target_pressure:.3f}")
        self.sample_display.setText(f"{sample_pressure:.3f}")


    def reset(self):
        self.target_display.setText("0.000")
        self.sample_display.setText("0.000")
