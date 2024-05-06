from ConfigurationManager import ConfigurationManager
from MainWindow import MainWindow
from DataHandler import DataHandler
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from path_utils import get_base_directory
import os


# Application entry point
def main():

    # Use XCB platform for Qt
    # Wayland does not render drop shadows or toolbar colors and offsets popups
    os.environ["QT_QPA_PLATFORM"] = "xcb"

    base_dir = get_base_directory()
    config_file_path = os.path.join(base_dir, "settings.json")
    icon_path = os.path.join(base_dir, 'icons', 'wing.png')

    config_manager = ConfigurationManager(config_file_path)

    app = QApplication([])
    app.setWindowIcon(QIcon(icon_path))
    app.setApplicationName("Icarus")

    window = MainWindow(config_manager)
    window.showMaximized()

    data_handler = DataHandler(config_manager)
    window.set_device(data_handler)
    data_handler.start()

    app.exec()


if __name__ == "__main__":
    main()
