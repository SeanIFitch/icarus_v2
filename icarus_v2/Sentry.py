
class Sentry:
    def __init__(self):
        pass


    # Shutdown if there is a sudden loss of pressure
    # Indicates massive leak
    def check_pressure(self):
        pass


    # Check pump rate
    # Too high indicates a leak
    def check_pump_rate(self):
        pass


    # Shutdown if pumping on startup when valves are open
    def check_pumping_pressure(self):
        pass


    # Warn if pressure continues to increase after a valve event
    # Indicates leaky pressurize valve
    def check_increasing_pressure(self):
        pass


    # Warn if pressure continues to decrease after a valve event
    # Indicates leaky depressurize valve
    def check_decreasing_pressure(self):
        pass