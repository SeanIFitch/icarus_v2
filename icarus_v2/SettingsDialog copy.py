from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from ErrorDialog import open_error_dialog


class SettingsDialog(QDialog):
    def __init__(self, config_loader, parent=None):
        super().__init__(parent)

        self.config_loader = config_loader
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 200, 200)

        layout = QGridLayout()
        self.setLayout(layout)

        # Buttons to apply or discard changes
        buttons = QDialogButtonBox.Apply
        self.buttonBox = QDialogButtonBox(buttons)
        # Connect apply button to accept slot
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

        # Labels
        pump_count_label = QLabel("Pump Count:")
        pressurize_count_label = QLabel("Pressurize Count:")
        depressurize_count_label = QLabel("Depressurize Count:")
        tube_length_label = QLabel("Tube Length (cm):")
        theme_label = QLabel("Theme:")




        # Generate LineEdits
        self.line_edits = {}
        self.timing_settings = deepcopy(self.pulse_generator.settings)
        # Allow only positive floating-point numbers
        positive_validator = QDoubleValidator()
        positive_validator.setBottom(0)
        for key, value in self.timing_settings:
            line_edit = QLineEdit()
            line_edit.setFixedWidth(40)
            line_edit.setAlignment(Qt.AlignRight)
            line_edit.setValidator(positive_validator)
            line_edit.setText(str(value))
            self.line_edits[key] = line_edit

        self.line_edits['pressurize_width'].textChanged.connect(self.set_pressurize_width)
        self.line_edits['depressurize_width'].textChanged.connect(self.set_depressurize_width)
        self.line_edits['period_width'].textChanged.connect(self.set_period_width)
        self.line_edits['delay_width'].textChanged.connect(self.set_delay_width)

        # Set layout
        self.layout = QGridLayout()
        self.layout.addWidget(pressurize_label, 0, 0)
        self.layout.addWidget(depressurize_label, 1, 0)
        self.layout.addWidget(period_label, 2, 0)
        self.layout.addWidget(delay_label, 3, 0)
        self.layout.addWidget(self.pressurize_edit, 0, 1)
        self.layout.addWidget(self.depressurize_edit, 1, 1)
        self.layout.addWidget(self.period_edit, 2, 1)
        self.layout.addWidget(self.delay_edit, 3, 1)

        self.layout.addWidget(self.buttonBox, 4, 0, 4, 1, alignment=Qt.AlignRight)
        self.setLayout(self.layout)


    # Apply changes to PulseGenerator and close the dialog
    # Also does some minor error checking for settings
    def apply(self) -> None:
        error = None
        if self.pressurize_width < 8:
            error = "Pressurize width should be greater than 8ms."
        elif self.depressurize_width < 8:
            error = "Depressurize width should be greater than 8ms."
        elif self.period_width < 3:
            error = "Period width should be greater than 3s."
        elif self.delay_width < 0.05:
            error = "Delay width should be greater than 0.05s."
        elif self.pressurize_width / 1000 >= self.period_width:
            error = "Pressurize width should be less than Period width."
        elif self.depressurize_width / 1000 >= self.period_width:
            error = "Depressurize width should be less than Period width."
        elif self.delay_width >= self.period_width:
            error = "Delay width should be less than Period width."

        if error is not None:
            open_error_dialog(error, QDialogButtonBox.Ok, self)
            # Do not apply changes or close window
            return

        self.pulse_generator.update_settings(self.timing_settings)
        self.close()


    def set_pressurize_width(self, pressurize_width):
        try:
            pressurize_width = float(pressurize_width)
        except:
            return
        self.timing_settings['pressurize_width'] = pressurize_width


    def set_depressurize_width(self, depressurize_width):
        try:
            depressurize_width = float(depressurize_width)
        except:
            return
        self.timing_settings['depressurize_width'] = depressurize_width


    def set_period_width(self, period_width):
        try:
            period_width = float(period_width)
        except:
            return
        self.timing_settings['period_width'] = period_width


    def set_delay_width(self, delay_width):
        try:
            delay_width = float(delay_width)
        except:
            return
        self.timing_settings['delay_width'] = delay_width
