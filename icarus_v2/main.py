from MainWindow import MainWindow
from DataHandler import DataHandler
from PySide6.QtWidgets import QApplication


# Application entry point
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()

    try:
        data_handler = DataHandler("settings.json")
        window.set_device(data_handler)
    except:
        print("failed to connect")
    window.init_loader()

    app.exec()
