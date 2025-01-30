from time import strftime

class SentryError(RuntimeError):
    def __init__(self, error_type, time, info=None):
        self.error_type = error_type
        self.time = time
        self.info = info

    def __str__(self):
        if self.error_type == "Pump Rate High":
            return (
                f"Error: {len(self.info["recent_pump_times"])} pump strokes occurred within {self.info['pump_window']} seconds.")
        elif self.error_type == "Pressure Decreasing":
            return (
                f"Error: pressure decreased {self.info["num_pressure_decreases"]} times in a row at "
                f"{strftime('%H:%M:%S', self.time)}. Likely leak")
        
        return "Unknown Error"