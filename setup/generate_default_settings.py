import json

TARGET = 0          # Analog CH0: target pressure 
DEPRE_LOW = 1       # Analog CH1: depressurization valve lower sensor
DEPRE_UP = 2        # Analog CH2: depressurization valve upper sensor
PRE_LOW = 3         # Analog CH3: pressurization valve lower sensor
PRE_UP = 4          # Analog CH4: pressurization valve upper sensor
HI_PRE_ORIG = 5     # Analog CH5: high pressure transducer at the origin
HI_PRE_SAMPLE = 6   # Analog CH6: high pressure transducer at the sample
PUMP = 7            # Digital CH0: high pressure pump (Active low / pumping on False)
DEPRE_VALVE = 8     # Digital CH1: depressurize valve (Active low / open on False)
PRE_VALVE = 9       # Digital CH2: pressurize valve (Active low / open on False)
LOG = 10            # Digital CH4: log (Active low / logging on False)


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
    counter = {
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
    hide_valve_sensors = False

    '''
    # Dataq: volts = value_read * range / 32768     # range = 10
    # Low pressure sensor: psi = volts * 20
    # High pressure sensor: psi = volts * 10000
    # kBar: kbar = psi / 14503.7738
    # Target: multiply by 400

    v: volts, p: psi, k: kBar
    v = a * 10 / 32768
    k = p / 14503

    High pressure
    p = v * 10000
    v = p / 10000
    p / 10000 = a * 10 / 32768
    p = a * 10 * 10000 / 32768
    p = k * 14503.7738
    k * 14503.7738 = a * 10 * 10000 / 32768
    k = a * 10 * 10000 / (32768 * 14503.7738)

    Target
    p = v * 20
    v = p / 20
    p / 20 = a * 10 / 32768
    p = a * 10 * 20 / 32768
    p = k * 14503.7738
    k * 14503.7738 = a * 10 * 20 / 32768
    k = a * 10 * 20 / (32768 * 14503.7738)
    target = 400 * k
    target / 400 = k
    target / 400 = a * 10 * 20 / (32768 * 14503.7738)
    target = a * 10 * 20 * 400 / (32768 * 14503.7738)
    '''
    coefficients = {
        TARGET:         10 * 20 * 400 / (32768 * 14503.7738),
        DEPRE_LOW:      0.00015,      # Arbitrary for visibility
        DEPRE_UP:       0.00015,      # Arbitrary for visibility
        PRE_LOW:        0.00015,      # Arbitrary for visibility
        PRE_UP:         0.00015,      # Arbitrary for visibility
        HI_PRE_ORIG:    10 * 10000 / (32768 * 14503.7738),
        HI_PRE_SAMPLE:  10 * 10000 / (32768 * 14503.7738),
        DEPRE_VALVE:    2.8,    # Arbitrary for visibility
        PRE_VALVE:      2.85,    # Arbitrary for visibility
    }

    # Legacy
    #tube = 100.0
    #theme = "System Default"

    settings = {
        "timing_settings": timing_settings,
        "counter_settings": counter,
        "plotting_coefficients": coefficients,
        "hide_valve_sensors": hide_valve_sensors
        #"tube_length": tube,
        #"theme": theme
    }


    filename = "settings.json"
    save_settings(filename)
