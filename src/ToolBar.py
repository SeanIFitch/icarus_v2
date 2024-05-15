from PySide6.QtWidgets import QToolBar, QLabel, QWidget, QSizePolicy
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
        self.connected = False
        self.pressure_signal = None
        settings_action = QAction(QIcon(), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        self.addAction(settings_action)
        self.settings_dialog = None

        # History reset button
        self.history_reset_action = QAction(QIcon(), "Reset History", self)
        self.addAction(self.history_reset_action)

        # Log Loader mode button
        self.change_mode_action = QAction(QIcon(), "Open Logs", self)
        self.change_mode_action.triggered.connect(self.change_log_mode)
        self.addAction(self.change_mode_action)

        # Warning Label
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)
        self.warning_label = QLabel("", self)
        self.warning_label.setStyleSheet("color: orange; font-size: 12pt;") 
        self.addWidget(self.warning_label)


    def open_settings(self):
        # Open the settings dialog
        self.settings_dialog = SettingsDialog(self.config_manager, self.connected, self.pressure_signal, self.parent())
        self.settings_dialog.exec()
        self.settings_dialog = None


    def change_log_mode(self):
        if self.change_mode_action.text() == "Open Logs":
            self.change_mode_action.setText("Close Logs")
            self.set_mode_signal.emit("log")

        elif self.change_mode_action.text() == "Close Logs":
            self.change_mode_action.setText("Open Logs")
            self.set_mode_signal.emit("device")


    def set_pressure_signal(self, pressure_signal):
        self.pressure_signal = pressure_signal
        if self.settings_dialog is not None:
            self.settings_dialog.set_pressure_signal(pressure_signal)

    def set_connected(self, connected):
        self.connected = connected
        if self.settings_dialog is not None:
            self.settings_dialog.set_connected(connected)


    def display_warning(self, warning):
        self.warning_label.setText(warning)
