from PySide6.QtWidgets import QToolBar, QFileDialog
from PySide6.QtGui import QIcon, QAction
from SettingsDialog import SettingsDialog
from PySide6.QtCore import Signal


class ToolBar(QToolBar):
    set_mode_signal = Signal(str)


    def __init__(self, config_manager, parent=None):
        super().__init__(parent=parent)

        self.config_manager = config_manager
        self.setMovable(False)

        # Settings button
        settings_action = QAction(QIcon(), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)

        # History reset button
        self.history_reset_action = QAction(QIcon(), "Reset History", self)
        self.addAction(self.history_reset_action)

        # Log Loader mode button
        self.change_mode_action = QAction(QIcon(), "Load Log", self)
        self.change_mode_action.triggered.connect(self.change_log_mode)
        self.addAction(self.change_mode_action)


    def open_settings(self):
        # Open the settings dialog
        dialog = SettingsDialog(self.config_manager, self.parent())
        dialog.exec()


    def change_log_mode(self):
        if self.change_mode_action.text() == "Load Log":
            self.change_mode_action.setText("Close Logs")
            self.set_mode_signal.emit("log")

        elif self.change_mode_action.text() == "Close Logs":
            self.change_mode_action.setText("Load Log")
            self.set_mode_signal.emit("device")
