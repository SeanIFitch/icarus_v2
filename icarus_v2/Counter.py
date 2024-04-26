from PySide6.QtCore import Signal, QObject
from Event import Event


# Keeps track of and logs valve counts
class Counter(QObject):
    save_settings = Signal(bool)
    update_counts = Signal(dict)


    def __init__(self, settings):
        super().__init__()
        # Counters
        self.counts = {
            "pump_count": settings["pump_count"],
            "pressurize_count": settings["pressurize_count"],
            "depressurize_count": settings["depressurize_count"]
        }


    def increment_count(self, event):
        if event.event_type == Event.PUMP:
            self.counts["pump_count"] += 1
        elif event.event_type == Event.PRESSURIZE:
            self.counts["pressurize_count"] += 1
        elif event.event_type == Event.DEPRESSURIZE:
            self.counts["depressurize_count"] += 1

        self.update_counts.emit(self.counts)

        # Save counts to json every 1000 updates
        if sum(self.counts.values()) % 1000 == 0:
            self.save_settings.emit(True)
