import lzma
import pickle
from Event import Event

# Load events from logs
class LogReader:
    def __init__(self) -> None:
        self.events = None
        self.filename = None


    def read_events(self, filename):
        self.events = []
        self.filename = filename
        file = lzma.open(filename, "rb")  # Open file in read binary mode
        try:
            while True:
                # Deserialize event data using pickle
                event_dict = pickle.load(file)
                event = Event(
                    event_dict['event_type'],
                    event_dict['data'],
                    event_dict['event_index'],
                    event_dict['event_time'],
                    event_dict['step_time']
                )
                self.events.append(event)
        except EOFError:
            pass  # End of file reached
        file.close()
