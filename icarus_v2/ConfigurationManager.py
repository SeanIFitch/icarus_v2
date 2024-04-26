import json
from copy import deepcopy
from PySide6.QtCore import Signal, QObject


# Responsible for loading and saving settings
class ConfigurationManager(QObject):
    settings_updated = Signal(str)

    def __init__(self, filename = "settings.json") -> None:
        super().__init__()

        # Load application settings
        self.filename = filename
        with open(self.filename, "r") as file:
            # Dictionary
            self.settings = json.load(file)


    def get_settings(self, key):
        return deepcopy(self.settings[key])


    def save_settings(self, key, value):
        self.settings[key] = value

        with open(self.filename, "w") as file:
            json.dump(self.settings, file, indent=4)

        self.settings_updated.emit(key)
