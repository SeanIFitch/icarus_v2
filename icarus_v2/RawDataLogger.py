import lzma
import pickle
#from datetime import datetime
from PySide6.QtCore import QThread
from time import time

class RawDataLogger(QThread):
    def __init__(self):
        #current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"raw_logs/log_{time()}.xz"
        self.file = lzma.open(filename, "ab")  # Opening file in append binary mode with LZMA compression


    def log_event(self, data):
        # Serialize event data using pickle with a higher protocol for efficiency
        pickle.dump(data, self.file, protocol=pickle.HIGHEST_PROTOCOL)


    def close(self):
        self.file.close()
