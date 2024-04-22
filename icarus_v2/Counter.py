from PySide6.QtCore import Signal, QObject


# Keeps track of and logs valve counts
class Counter(QObject):
    save_settings = Signal(bool)
    update_counts = Signal(dict)


    def __init__(self, settings):
        super().__init__()
        # Counters
        self.counts = {
            "pump": settings["pump"],
            "pressurize": settings["pressurize"],
            "depressurize": settings["depressurize"]
        }


    def increment_count(self, event):
        self.counts[event.get_event_type()] += 1
        self.update_counts.emit(self.counts)

        # Save counts to json every 1000 updates
        if sum(self.counts.values()) % 1000 == 0:
            self.save_settings.emit(True)
