from ConfigurationManager import ConfigurationManager
from MainWindow import MainWindow
from DataHandler import DataHandler
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import os


# Application entry point
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(base_dir, "..", "settings.json")
    icon_path = os.path.join(base_dir, '..', 'icons', 'wing.png')

    config_manager = ConfigurationManager(config_file_path)

    app = QApplication([])
    app.setWindowIcon(QIcon(icon_path))
    window = MainWindow(config_manager)
    window.showMaximized()

    data_handler = DataHandler(config_manager)
    window.set_device(data_handler)
    data_handler.start()

    app.exec()


if __name__ == "__main__":
    main()
