from PySide6.QtCore import Signal, QObject
from Event import Event


# Keeps track of and logs valve counts
class Counter(QObject):
    save_settings = Signal(bool)
    update_counts = Signal(dict)


    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        self.config_manager.settings_updated.connect(self.update_settings)
        self.counts = config_manager.get_settings("counter_settings")


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
            # Do not emit so that this does not call self.update_settings
            self.config_manager.save_settings("counter_settings", self.counts, emit=False)


    def update_settings(self, key):
        if key == 'counter_settings':
            self.counts = self.config_manager.get_settings(key)
        self.update_counts.emit(self.counts)
