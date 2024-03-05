from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel


class ErrorDialog(QDialog):
    Retry = QDialogButtonBox.Retry
    Cancel = QDialogButtonBox.Cancel

    def __init__(self, message, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Error")

        buttons = QDialogButtonBox.Retry | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.buttonBox.button(QDialogButtonBox.Retry).setDefault(True)
        self.layout = QVBoxLayout()
        display_text = QLabel(message)
        self.layout.addWidget(display_text)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
