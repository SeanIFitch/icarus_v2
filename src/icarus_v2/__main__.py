from icarus_v2.backend.configuration_manager import ConfigurationManager
from icarus_v2.gui.main_window import MainWindow
from icarus_v2.backend.data_handler import DataHandler
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from icarus_v2.utils.path_utils import get_base_directory
import os
from icarus_v2.qdarktheme.load_style import load_stylesheet

# Application entry point
def main():

    # Use XCB platform for Qt
    # Wayland does not render drop shadows or toolbar colors and offsets popups
    # os.environ["QT_QPA_PLATFORM"] = "xcb"

    base_dir = get_base_directory()
    config_file_path = os.path.join(base_dir, "settings.json")
    icon_path = os.path.join(base_dir, 'resources', 'wing.png')

    config_manager = ConfigurationManager(config_file_path)

    app = QApplication([])
    app.setStyleSheet(load_stylesheet(theme='dark'))
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
