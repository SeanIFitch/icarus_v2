import importlib
from icarus_v2.backend.configuration_manager import ConfigurationManager
from icarus_v2.gui.main_window import MainWindow
from icarus_v2.backend.data_handler import DataHandler
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from icarus_v2.qdarktheme.load_style import load_stylesheet


# Application entry point
def main():
    app = QApplication([])
    app.setApplicationName("Icarus")
    app.setStyleSheet(load_stylesheet(theme='dark'))

    with importlib.resources.path('icarus_v2.resources', 'wing.png') as icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    # initialize singleton ConfigurationManager
    ConfigurationManager()

    window = MainWindow()
    window.showMaximized()

    data_handler = DataHandler()
    window.set_device(data_handler)
    data_handler.start()

    app.exec()


if __name__ == "__main__":
    main()
