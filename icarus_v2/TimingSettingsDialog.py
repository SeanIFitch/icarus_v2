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


# Dialog for changing pulsed mode timings.
# When the LineEdits are used, member variables of this class are changed. 
# Changes are not applied to the real PulseGenerator until Apply is clicked.
class TimingSettingsDialog(QDialog):
    def __init__(self, pulse_generator, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pulsed Mode Timings")
        self.pulse_generator = pulse_generator

        # Buttons to apply or discard changes
        buttons = QDialogButtonBox.Apply
        self.buttonBox = QDialogButtonBox(buttons)
        # Connect apply button to accept slot
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        self.buttonBox.rejected.connect(self.reject)

        # Timing controls
        pressurize_label = QLabel("Pressurize Width (ms):")
        depressurize_label = QLabel("Depressurize Width (ms):")
        period_label = QLabel("Period (s):")
        delay_label = QLabel("Delay (s):")
        self.pressurize_edit = QLineEdit()
        self.depressurize_edit = QLineEdit()
        self.period_edit = QLineEdit()
        self.delay_edit = QLineEdit()
        # View settings
        self.pressurize_edit.setFixedWidth(40)
        self.depressurize_edit.setFixedWidth(40)
        self.period_edit.setFixedWidth(40)
        self.delay_edit.setFixedWidth(40)
        self.pressurize_edit.setAlignment(Qt.AlignRight)
        self.depressurize_edit.setAlignment(Qt.AlignRight)
        self.period_edit.setAlignment(Qt.AlignRight)
        self.delay_edit.setAlignment(Qt.AlignRight)
        # Allow only positive floating-point numbers
        positive_validator = QDoubleValidator()
        positive_validator.setBottom(0)
        self.pressurize_edit.setValidator(positive_validator)
        self.depressurize_edit.setValidator(positive_validator)
        self.period_edit.setValidator(positive_validator)
        self.delay_edit.setValidator(positive_validator)

        # Connect LineEdits
        self.pressurize_width = self.pulse_generator.settings['pressurize_width']
        self.depressurize_width = self.pulse_generator.settings['depressurize_width']
        self.period_width = self.pulse_generator.settings['period_width']
        self.delay_width = self.pulse_generator.settings['delay_width']
        self.pressurize_edit.setText(str(self.pressurize_width))
        self.depressurize_edit.setText(str(self.depressurize_width))
        self.period_edit.setText(str(self.period_width))
        self.delay_edit.setText(str(self.delay_width))
        self.pressurize_edit.textChanged.connect(self.set_pressurize_width)
        self.depressurize_edit.textChanged.connect(self.set_depressurize_width)
        self.period_edit.textChanged.connect(self.set_period_width)
        self.delay_edit.textChanged.connect(self.set_delay_width)

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

        self.pulse_generator.set_pressurize_width(self.pressurize_width)
        self.pulse_generator.set_depressurize_width(self.depressurize_width)
        self.pulse_generator.set_period_width(self.period_width)
        self.pulse_generator.set_delay_width(self.delay_width)
        self.close()


    def set_pressurize_width(self, pressurize_width):
        try:
            pressurize_width = float(pressurize_width)
        except:
            return
        self.pressurize_width = pressurize_width


    def set_depressurize_width(self, depressurize_width):
        try:
            depressurize_width = float(depressurize_width)
        except:
            return
        self.depressurize_width = depressurize_width


    def set_period_width(self, period_width):
        try:
            period_width = float(period_width)
        except:
            return
        self.period_width = period_width


    def set_delay_width(self, delay_width):
        try:
            delay_width = float(delay_width)
        except:
            return
        self.delay_width = delay_width
