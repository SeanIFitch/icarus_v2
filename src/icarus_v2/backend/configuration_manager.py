import json
import os
import importlib
import threading
from copy import deepcopy
from PySide6.QtCore import Signal, QObject, QStandardPaths, QMetaObject, Q_ARG, Qt
from icarus_v2.backend.event import Channel


# Responsible for loading and saving settings
# Thread-safe singleton
class ConfigurationManager(QObject):
    _instance = None
    _lock = threading.Lock()  # Lock for thread safety
    FILENAME = "settings.json"
    # Signal to let subscribers know that settings[key] was changed
    settings_updated = Signal(str)

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            super().__init__()
            self._initialize()

    def _initialize(self):
        self.initialized = True

        # Get the application configuration path
        self.config_path = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        os.makedirs(self.config_path, exist_ok=True)  # Create the directory if it doesn't exist

        self.filename = os.path.join(self.config_path, self.FILENAME)

        # Load application settings
        if not os.path.isfile(self.filename):
            self.settings = self.get_default_settings()
            self.save_settings()  # Save default settings to the config file
        else:
            with open(self.filename, "r") as file:
                # Dictionary
                self.settings = json.load(file)

    def get_settings(self, key):
        with self._lock:
            # Get default value if not defined
            if key not in self.settings:
                default = self.get_default_settings()
                self.settings[key] = default[key]

            value = deepcopy(self.settings[key])

            # Convert to enum rather than int
            if key == 'plotting_coefficients':
                value = {Channel(int(k)): v for k, v in value.items()}

        return value

    def save_settings(self, key=None, value=None, emit=True):
        with self._lock:
            if key is not None and value is not None:
                # Convert to int rather than enum
                if key == 'plotting_coefficients':
                    value = {k.value: v for k, v in value.items()}
                self.settings[key] = value

            with open(self.filename, "w") as file:
                json.dump(self.settings, file, indent=4)

        if emit and key is not None:
            # Emit in a thread-safe way
            QMetaObject.invokeMethod(self, "settings_updated", Qt.QueuedConnection, Q_ARG(str, key))

    @staticmethod
    def get_default_settings():
        # Load default settings from icarus_v2.resources
        with importlib.resources.path('icarus_v2.resources', 'default_settings.json') as path:
            with open(path, 'r') as file:
                settings = json.load(file)
        return settings
