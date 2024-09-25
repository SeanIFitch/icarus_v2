from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QSizePolicy
)
from icarus_v2.backend.event import Channel


# Panel for pressure
class PressureDisplay(QGroupBox):
    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.coefficients = self.config_manager.get_settings("plotting_coefficients")
        self.config_manager.settings_updated.connect(self.update_settings)

        # Displays
        self.target_display = QLabel("0.000")
        self.origin_display = QLabel("0.000")

        # Labels
        main_label = QLabel("Pressure(kbar):")
        target_label = QLabel("Target:")
        origin_label = QLabel("Origin:")

        # Set main layout
        layout = QGridLayout()
        layout.addWidget(main_label, 0, 0, 1, 0)
        layout.addWidget(target_label, 1, 0)
        layout.addWidget(origin_label, 2, 0)
        layout.addWidget(self.target_display, 1, 1)
        layout.addWidget(self.origin_display, 2, 1)

        self.setStyleSheet("font-size: 28pt;")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setLayout(layout)


    def update_pressure(self, event):
        target_pressure = event.get_target_pressure() * self.coefficients[Channel.TARGET]
        origin_pressure = event.get_origin_pressure() * self.coefficients[Channel.HI_PRE_ORIG]
        self.target_display.setText(f"{target_pressure:.3f}")
        self.origin_display.setText(f"{origin_pressure:.3f}")


    def reset(self):
        self.target_display.setText("0.000")
        self.origin_display.setText("0.000")

    def update_settings(self, key):
        if key == "plotting_coefficients":
            self.coefficients = self.config_manager.get_settings(key)
