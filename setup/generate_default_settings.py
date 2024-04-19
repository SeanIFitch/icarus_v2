
import json


# Save settings to a JSON file
def save_settings(filename):
    with open(filename, 'w') as file:
        json.dump(settings, file, indent=4)

# Load settings from a JSON file
def load_settings(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


# This script shouldn't ever have to be run. Just leaving it in here in case there is a need to reset settings.
if __name__ == "__main__":
    counter_settings = {
        "pump_count": 0,
        "pressurize_count": 0,
        "depressurize_count": 0
    }
    timing_settings = {
        "pressurize_width": 10.0,
        "depressurize_width": 10.0,
        "period_width": 5.0,
        "delay_width": 2.0
    }
    settings = {
        "counter": counter_settings,
        "timing_settings": timing_settings,
    }

    filename = "settings.json"
    save_settings(filename)
