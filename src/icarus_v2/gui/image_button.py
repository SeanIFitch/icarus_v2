from PySide6.QtWidgets import QAbstractButton
from PySide6.QtGui import QPixmap, QPainter, QFontMetrics
from PySide6.QtCore import Qt, QTimer


class ImageButton(QAbstractButton):
    def __init__(self, picture, button_text, parent=None, cooldown_ms=0):
        super().__init__(parent)
        self.picture = QPixmap(picture)
        self.button_text = button_text
        self.grey = False
        self.cooldown_duration = cooldown_ms
        self.in_cooldown = False

        # Cooldown timer setup
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setSingleShot(True)
        self.cooldown_timer.timeout.connect(self._end_cooldown)

        # Connect signals
        self.pressed.connect(self._grey_out)
        self.released.connect(self._restore)
        self.clicked.connect(self._start_cooldown)

    def _grey_out(self):
        # Temporarily grey out the button
        self.grey = True
        self.update()

    def _restore(self):
        self.grey = False
        self.update()

    def _start_cooldown(self):
        if self.cooldown_duration > 0 and not self.in_cooldown:
            self.in_cooldown = True
            self.cooldown_timer.start(self.cooldown_duration)
            self.update()

    def _end_cooldown(self):
        self.in_cooldown = False
        self.update()

    def mousePressEvent(self, event):
        if self.in_cooldown:
            event.ignore()
        else:
            super().mousePressEvent(event)

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
