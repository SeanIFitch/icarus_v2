import json


class ConfigurationManager:
    def __init__(self, filename = "settings.json") -> None:
        # Load application settings
        self.filename = filename
        with open(self.filename, "r") as file:
            # Dictionary
            self.settings = json.load(file)


    def get_settings(self, key):
        return self.settings[key]


    def save_settings(self, key, value):
        self.settings[key] = value

        with open(self.filename, "w") as file:
            json.dump(self.settings, file, indent=4)
