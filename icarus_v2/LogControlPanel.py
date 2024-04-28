from PySide6.QtWidgets import (
    QGroupBox,
    QGridLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QInputDialog,
)
from time import time
import os
from PySide6.QtGui import QDoubleValidator, QFont
from PySide6.QtCore import Qt, Signal
from ErrorDialog import open_error_dialog
from bisect import bisect_right
from Event import Event


# Control panel for logs
class LogControlPanel(QGroupBox):
    pressurize_event_signal = Signal(Event)
    depressurize_event_signal = Signal(Event)
    period_event_signal = Signal(Event)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # Time controls
        self.time_edit = QLineEdit(self)
        last_button = QPushButton("Last Event")
        next_button = QPushButton("Next Event")
        self.time_edit.editingFinished.connect(self.select_time)
        last_button.pressed.connect(self.emit_last_event)
        next_button.pressed.connect(self.emit_next_event)

        # Filename display and renaming
        title = QLabel("Viewing Log")
        font = QFont()
        font.setPointSize(21)
        title.setFont(font)
        self.filename_label = QLabel("")
        rename_button = QPushButton("Rename")
        rename_button.clicked.connect(self.rename_file)

        # Set layouts
        title_layout = QVBoxLayout()
        title_layout.addWidget(title)
        title_layout.addWidget(self.filename_label)
        title_layout.setAlignment(title, Qt.AlignHCenter)

        control_layout = QGridLayout()
        control_layout.addWidget(QLabel("Time (s):"), 0, 0)
        control_layout.addWidget(self.time_edit, 0, 1)
        control_layout.addWidget(last_button, 1, 0)
        control_layout.addWidget(next_button, 1, 1)

        layout = QVBoxLayout(self)
        layout.addLayout(title_layout)
        layout.addLayout(control_layout)
        layout.addWidget(rename_button)
        layout.setAlignment(title_layout, Qt.AlignTop)
        layout.setAlignment(control_layout, Qt.AlignCenter)
        layout.setAlignment(rename_button, Qt.AlignBottom)

        self.setFixedSize(194, 321)
        self.setLayout(layout)


    def load_new_file(self, log_reader):
        self.press_index = -1
        self.depress_index = -1
        self.period_index = -1
        self.list = log_reader.events
        self.filename = log_reader.filename
        self.filename_label.setText(os.path.basename(self.filename))
        if len(self.list) > 0:
            upper_bound = self.list[-1].event_time - self.list[0].event_time
        else:
            upper_bound = 0
        self.time_edit.setValidator(QDoubleValidator(0, upper_bound, 2))


    def rename_file(self):
        new_name, ok = QInputDialog.getText(self, "Rename File", "Enter new filename:")
        if ok and new_name:
            # Construct the new filename with the directory path
            new_filename = os.path.join(os.path.dirname(self.filename), new_name)
            
            try:
                os.rename(self.filename, new_filename)  # Rename the file
                self.filename = new_filename  # Update the filename attribute
                self.filename_label.setText(os.path.basename(new_filename))  # Update the label
            except OSError as e:
                open_error_dialog(e)


    def select_time(self):
        try:
            time=float(self.time_edit.text())
        except:
            return
        if len(self.list) == 0:
            return

        initial_time = self.list[0].event_time
        index = max(0, bisect_right(self.list, time, key=lambda x: x.event_time - initial_time) - 1)

        press = None
        depress = None
        period = None
        for i in range(index, -1, -1):
            event = self.list[i]
            if press is None and event.event_type == Event.PRESSURIZE:
                self.press_index = i
                press = event
            elif depress is None and event.event_type == Event.DEPRESSURIZE:
                self.depress_index = i
                depress = event
            elif period is None and event.event_type == Event.PERIOD:
                self.period_index = index
                period = event

            if press is not None and depress is not None and period is not None:
                break

        self.pressurize_event_signal.emit(press)
        self.depressurize_event_signal.emit(depress)
        self.period_event_signal.emit(period)


    def emit_next_event(self):
        index = max(self.press_index, self.depress_index, self.period_index) + 1
        if index >= len(self.list):
            return
        event = self.list[index]

        if event.event_type == Event.PRESSURIZE:
            self.press_index = index
            self.pressurize_event_signal.emit(event)

        elif event.event_type == Event.DEPRESSURIZE:
            self.depress_index = index
            self.depressurize_event_signal.emit(event)
            # Also emit matching PERIOD
            if index + 1 < len(self.list):
                n_event = self.list[index + 1]
                if n_event.event_type == Event.PERIOD and abs(n_event.event_time - event.event_time) < 1:
                    self.period_index = index + 1
                    self.period_event_signal.emit(n_event)

        elif event.event_type == Event.PERIOD:
            self.period_index = index
            self.period_event_signal.emit(event)
            # Also emit matching DEPRESSURIZE
            if index + 1 < len(self.list):
                n_event = self.list[index + 1]
                if n_event.event_type == Event.DEPRESSURIZE and abs(n_event.event_time - event.event_time) < 1:
                    self.depress_index = index + 1
                    self.depressurize_event_signal.emit(n_event)


    def emit_last_event(self):
        index = min(self.press_index, self.depress_index, self.period_index) - 1
        if index < 0:
            return
        event = self.list[index]

        if event.event_type == Event.PRESSURIZE:
            self.press_index = index
            self.pressurize_event_signal.emit(event)

        elif event.event_type == Event.DEPRESSURIZE:
            self.depress_index = index
            self.depressurize_event_signal.emit(event)
            # Also emit matching PERIOD
            if index - 1 >= 0:
                n_event = self.list[index - 1]
                if n_event.event_type == Event.PERIOD and abs(n_event.event_time - event.event_time) < 1:
                    self.period_index = index + 1
                    self.period_event_signal.emit(n_event)

        elif event.event_type == Event.PERIOD:
            self.period_index = index
            self.period_event_signal.emit(event)
            # Also emit matching DEPRESSURIZE
            if index - 1 >= 0:
                n_event = self.list[index - 1]
                if n_event.event_type == Event.DEPRESSURIZE and abs(n_event.event_time - event.event_time) < 1:
                    self.depress_index = index - 1
                    self.depressurize_event_signal.emit(n_event)

