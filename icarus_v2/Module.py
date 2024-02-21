class Module:
    def __init__(self, buffer_reader) -> None:
        self.buffer_reader = buffer_reader

    def read(self):
        while(True):
            data = self.buffer_reader.read()
            print(data)
