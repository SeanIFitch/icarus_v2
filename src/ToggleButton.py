from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Signal, Slot


# PushButton subclass which toggles and runs separate functions on check and uncheck
class ToggleButton(QPushButton):
    checked = Signal()
    unchecked = Signal()

    def __init__(self, check_text, uncheck_text=None, check_color=None, uncheck_color=None, parent=None):
        super().__init__(parent)
        self.toggled.connect(self._on_toggled)
        self.check_text = check_text
        self.uncheck_text = uncheck_text
        self.check_color = check_color
        self.uncheck_color = uncheck_color
        self.check_func = None
        self.uncheck_func = None

        if self.check_text is not None:
            self.setText(check_text)
        self.setCheckable(True)
        if uncheck_color is not None:
            self._set_style(self.uncheck_color)

    @Slot(bool)
    def _on_toggled(self, checked):
        if checked:
            if self.uncheck_text is not None:
                self.setText(self.uncheck_text)
            if self.check_color is not None:
                self._set_style(self.check_color)
            if self.check_func:
                self.check_func()
            self.checked.emit()
        else:
            if self.check_text is not None:
                self.setText(self.check_text)
            if self.uncheck_color is not None:
                self._set_style(self.uncheck_color)
            if self.uncheck_func:
                self.uncheck_func()
            self.unchecked.emit()

    def set_checked(self, checked):
        self.blockSignals(True)
        self.setChecked(checked)
        if checked:
            if self.uncheck_text is not None:
                self.setText(self.uncheck_text)
            if self.check_color is not None:
                self._set_style(self.check_color)
        else:
            if self.check_text is not None:
                self.setText(self.check_text)
            if self.uncheck_color is not None:
                self._set_style(self.uncheck_color)
        self.blockSignals(False)

    def set_check_function(self, check_func):
        self.check_func = check_func

    def set_uncheck_function(self, uncheck_func):
        self.uncheck_func = uncheck_func

    def _set_style(self, color):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {color};
            }}
            QPushButton:pressed {{
                background-color: {color};
            }}
        """)
