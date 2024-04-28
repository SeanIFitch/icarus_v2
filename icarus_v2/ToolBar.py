from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from SettingsDialog import SettingsDialog


class ToolBar(QToolBar):
    def __init__(self, config_manager, history_plot, parent=None):
        super().__init__(parent=parent)

        self.config_manager = config_manager
        self.setMovable(False)

        # Add a settings button
        settings_action = QAction(QIcon(), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)
        # Add a history reset button
        self.history_reset_action = QAction(QIcon(), "Reset History", self)
        self.addAction(self.history_reset_action)
        self.history_reset_action.triggered.connect(history_plot.reset_history)


    def open_settings(self):
        # Open the settings dialog
        dialog = SettingsDialog(self.config_manager, self.parent())
        dialog.exec()
