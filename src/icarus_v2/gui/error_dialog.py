from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QLabel
)


def open_error_dialog(error, buttons = QDialogButtonBox.Ok, parent=None):
    dialog = ErrorDialog(str(error), buttons, parent=parent)
    dialog.show()
    return dialog


class ErrorDialog(QDialog):
    Retry = QDialogButtonBox.Retry
    Cancel = QDialogButtonBox.Cancel

    def __init__(self, message, buttons, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Error")

        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Set default button
        if self.buttonBox.button(QDialogButtonBox.Retry) is not None:
            self.buttonBox.button(QDialogButtonBox.Retry).setDefault(True)
        elif self.buttonBox.button(QDialogButtonBox.Ok) is not None:
            self.buttonBox.button(QDialogButtonBox.Ok).setDefault(True)

        self.layout = QVBoxLayout()
        display_text = QLabel(message)
        self.layout.addWidget(display_text)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
