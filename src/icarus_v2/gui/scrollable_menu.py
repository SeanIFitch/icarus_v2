from PySide6.QtWidgets import QWidget, QMenu, QScrollArea, QVBoxLayout, QWidgetAction, QLabel
from PySide6.QtCore import Qt, QSize, QPointF, QRectF
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QColor


class ScrollableMenu(QMenu):
    def __init__(self, max_messages=100, parent=None):
        super().__init__(parent)

        self.max_messages = max_messages
        self.messages = 0

        # Custom widget to hold the menu actions
        self.container_widget = QWidget()
        self.layout = QVBoxLayout(self.container_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignTop)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.container_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Setting the size of the scroll area
        self.scroll_area.setFixedWidth(900)
        self.scroll_area.setFixedHeight(300)

        # Add the scroll area to the menu
        scroll_area_widget_action = QWidgetAction(self)
        scroll_area_widget_action.setDefaultWidget(self.scroll_area)
        self.addAction(scroll_area_widget_action)

    def add_message(self, message, color):
        label = WrappedLabel(message, color, self)
        label.setStyleSheet("text-align: left")

        # Check if we're scrolled to the top before adding the new message
        scroll_bar = self.scroll_area.verticalScrollBar()
        at_top = scroll_bar.value() <= 5  # Consider "at top" if within 5 pixels

        # Insert the new message at the top
        self.layout.insertWidget(0, label, alignment=Qt.AlignTop)

        self.messages += 1

        # Remove the oldest message if we've exceeded the maximum
        if self.messages > self.max_messages:
            item = self.layout.takeAt(self.layout.count() - 1)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            self.messages -= 1

        # Scroll to the top only if we were already at the top
        if at_top:
            self.scroll_area.verticalScrollBar().setValue(0)
        else:
            # Adjust scroll position to keep the view stable
            new_value = scroll_bar.value() + label.sizeHint().height()
            scroll_bar.setValue(new_value)


class WrappedLabel(QLabel):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setTextFormat(Qt.PlainText)
        self.color = color

        self.setMinimumWidth(880)  # Adjust as needed
        self.setMaximumWidth(880)  # Adjust as needed
        self.line_indent = 20  # Space for the arrow

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        leading = metrics.leading()
        height = 0
        width = self.width() - self.line_indent  # Adjust width for indent

        for line in self.text().split('\n'):
            if not line:
                height += leading
            is_first_line = True
            while line:
                if is_first_line:
                    indent = 0
                else:
                    indent = self.line_indent
                    # Draw the arrow for wrapped lines
                    painter.setPen(QColor(100, 100, 100))  # Gray color for the arrow
                    painter.drawText(QRectF(2, height, indent - 2, metrics.height()), Qt.AlignLeft | Qt.AlignVCenter,
                                     "↪")

                line = metrics.elidedText(line, Qt.ElideNone, width)
                line_width = metrics.horizontalAdvance(line)
                if line_width <= width:
                    painter.setPen(QColor(self.color))
                    painter.drawText(QPointF(indent, height + metrics.ascent()), line)
                    height += metrics.height()
                    break
                i = len(line)
                while i > 0:
                    i -= 1
                    if metrics.horizontalAdvance(line[:i]) <= width:
                        painter.setPen(QColor(self.color))  # Black color for the text
                        painter.drawText(QPointF(indent, height + metrics.ascent()), line[:i])
                        height += metrics.height()
                        line = line[i:].lstrip()
                        is_first_line = False
                        break
        painter.end()

    def sizeHint(self):
        width = self.width() - self.line_indent
        metrics = QFontMetrics(self.font())
        height = 0
        for line in self.text().split('\n'):
            if not line:
                height += metrics.leading()
            else:
                height += metrics.height() * ((metrics.horizontalAdvance(line) + width - 1) // width)
        return QSize(self.width(), height)
