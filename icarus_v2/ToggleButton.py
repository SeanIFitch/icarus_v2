from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Signal, Slot


# PushButton subclass which toggles and runs separate functions on check and uncheck
class ToggleButton(QPushButton):
    checked = Signal()
    unchecked = Signal()


    def __init__(self, check_text, uncheck_text, parent=None):
        super().__init__(parent)
        self.toggled.connect(self._on_toggled)
        self.check_text = check_text
        self.uncheck_text = uncheck_text
        self.check_func = None
        self.uncheck_func = None

        self.setText(check_text)
        self.setCheckable(True)


    @Slot(bool)
    def _on_toggled(self, checked):
        if checked:
            self.setText(self.uncheck_text)
            if self.check_func:
                self.check_func()
            self.checked.emit()
        else:
            self.setText(self.check_text)
            if self.uncheck_func:
                self.uncheck_func()
            self.unchecked.emit()


    def set_checked(self, checked):
        self.blockSignals(True)
        self.setChecked(checked)
        if checked:
            self.setText(self.uncheck_text)
        else:
            self.setText(self.check_text)
        self.blockSignals(False)


    def set_check_function(self, check_func):
        self.check_func = check_func


    def set_uncheck_function(self, uncheck_func):
        self.uncheck_func = uncheck_func
