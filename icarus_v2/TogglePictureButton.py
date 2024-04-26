from PySide6.QtWidgets import QAbstractButton
from PySide6.QtGui import QPixmap, QPainter, QColor, QPainter, QFontMetrics, QImage
from PySide6.QtCore import QSize, Qt, Signal

class TogglePictureButton(QAbstractButton):
    checked = Signal()
    unchecked = Signal()

    def __init__(self, picture, check_text, uncheck_text, parent=None):
        super().__init__(parent)
        self.picture = QPixmap(picture)
        self.check_text = check_text
        self.uncheck_text = uncheck_text
        self.check_func = None
        self.uncheck_func = None
        self._size = QSize(90, 90)  # Default size
        self.setCheckable(True)
        self.setChecked(False)  # Initializes the button as unchecked by default
        self.toggled.connect(self._on_toggled)

    def set_check_function(self, func):
        self.check_func = func

    def set_uncheck_function(self, func):
        self.uncheck_func = func

    def _on_toggled(self, checked):
        if checked:
            if self.check_func:
                self.check_func()
            self.checked.emit()
        else:
            if self.uncheck_func:
                self.uncheck_func()
            self.unchecked.emit()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Decrease opacity if checked
        if self.isChecked():
            img = self.picture.toImage()
            img = img.convertToFormat(QImage.Format_ARGB32)
            for x in range(img.width()):
                for y in range(img.height()):
                    color = img.pixelColor(x, y)
                    color.setAlpha(color.alpha() * 0.6)
                    img.setPixelColor(x, y, color)
            pixmap = QPixmap.fromImage(img)
        else:
            pixmap = self.picture

        scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x_offset = (self.width() - scaled_pixmap.width()) / 2
        y_offset = (self.height() - scaled_pixmap.height()) / 2
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)

        # Setting up the font and drawing text
        text = self.uncheck_text if self.isChecked() else self.check_text
        fm = QFontMetrics(painter.font())
        text_width = fm.boundingRect(text).width()
        text_height = fm.height()
        text_x = (self.width() - text_width) / 2
        text_y = y_offset + (scaled_pixmap.height() / 2) + (text_height / 2)
        painter.drawText(text_x, text_y, text)

        painter.end()


    def sizeHint(self):
        return self._size

    def set_size(self, x, y):
        self._size = QSize(x, y)
        self.setMinimumSize(x, y)
        self.setMaximumSize(x, y)
        self.update()
