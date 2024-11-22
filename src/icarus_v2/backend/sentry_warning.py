from time import strftime

class SentryWarning(Warning):
    def __init__(self, error_type, time, info=None):
        self.error_type = error_type
        self.time = time
        self.info = info

    def __str__(self):
        if self.error_type == "Pump Rate High":
            return (
                f"Warning: pump rate at {strftime('%H:%M:%S', self.time)} is "
                f"{self.info["pump_rate"]:.2f}, which is {self.info["rate_percent_increase"]:.2f}% over the expected rate from the "
                "beginning of the experiment. Possible leak.")
        elif self.error_type == "Pressure Decreasing":
            return (
                f"Warning: pressure decreasing at "
                f"{strftime('%H:%M:%S', self.time)}. Possible leak.")
        elif self.error_type == "Pressure Increasing":
            return (
                f"Warning: pressure increasing at "
                f"{strftime('%H:%M:%S', self.time)}. Possible leak.")
        
        return "Unknown Warning"