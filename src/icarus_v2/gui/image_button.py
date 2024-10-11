from PySide6.QtWidgets import QAbstractButton
from PySide6.QtGui import QPixmap, QPainter, QPainter, QFontMetrics
from PySide6.QtCore import Qt


class ImageButton(QAbstractButton):
    def __init__(self, picture, button_text, parent=None):
        super().__init__(parent)
        self.picture = QPixmap(picture)
        self.button_text = button_text
        self.grey = False
        self.pressed.connect(self._grey_out)
        self.released.connect(self._restore)


    def _grey_out(self):
        # Temporarily grey out the button
        self.grey = True
        self.update()


    def _restore(self):
        self.grey = False
        self.update()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        scaled_pixmap = self.picture.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x_offset = (self.width() - scaled_pixmap.width()) / 2
        y_offset = (self.height() - scaled_pixmap.height()) / 2
        if self.grey:
            painter.setOpacity(0.6)
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        painter.setOpacity(1)

        # Setting up the font and drawing text
        text = self.button_text
        fm = QFontMetrics(painter.font())
        text_width = fm.boundingRect(text).width()
        text_height = fm.height()
        text_x = (self.width() - text_width) / 2
        text_y = y_offset + (scaled_pixmap.height() / 2) + (text_height / 2)
        painter.drawText(text_x, text_y, text)

        painter.end()
