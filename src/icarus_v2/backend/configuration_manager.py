import json
from copy import deepcopy
from PySide6.QtCore import Signal, QObject
from icarus_v2.backend.event import Channel


# Responsible for loading and saving settings
class ConfigurationManager(QObject):
    # Signal to let subscribers know that settings[key] was changed
    settings_updated = Signal(str)

    def __init__(self, filename = "settings.json") -> None:
        super().__init__()

        # Load application settings
        self.filename = filename
        with open(self.filename, "r") as file:
            # Dictionary
            self.settings = json.load(file)


    def get_settings(self, key):
        value = deepcopy(self.settings[key])
        # Convert to enum rather than int
        if key == 'plotting_coefficients':
            value = dict([(Channel(int(k)), v) for k,v in value.items()])
        return value


    def save_settings(self, key, value, emit=True):
        # Convert to int rather than enum
        if key == 'plotting_coefficients':
            value = dict([(k.value, v) for k,v in value.items()])
        self.settings[key] = value

        with open(self.filename, "w") as file:
            json.dump(self.settings, file, indent=4)

        if emit:
            self.settings_updated.emit(key)
