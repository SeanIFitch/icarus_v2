import lzma
import pickle
from icarus_v2.backend.event import Event
from icarus_v2.backend.sentry_error import SentryError


# Load events from logs
class LogReader:
    def __init__(self, tool_bar=None,) -> None:
        self.events = None
        self.filename = None
        self.logger = None
        self.log_coefficients = None
        self.tool_bar=tool_bar

    def set_logger(self, logger):
        self.logger = logger

    def read_events(self, filename):
        self.log_coefficients = None
        self.events = []
        self.filename = filename

        # If reading current log file, write to disk first
        if self.logger is not None and self.logger.filename is not None and self.filename == self.logger.filename:
            self.logger.flush()

        file = lzma.open(filename, "rb")  # Open file in read binary mode
        try:
            while True:
                # Deserialize event data using pickle
                event_dict = pickle.load(file)
                if "plotting_coefficients" in event_dict.keys():
                    self.log_coefficients = event_dict["plotting_coefficients"]
                elif "error_type" in event_dict.keys():
                    event = event_dict['class_type'](event_dict['error_type'],event_dict['event_time'],event_dict['data'])
                    color="orange"
                    if(type(event) == SentryError):
                        color = "red"

                    self.tool_bar.display_warning("LOG: "+str(event),color)
                else:
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
