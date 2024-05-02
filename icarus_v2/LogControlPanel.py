from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QDialog,
    QFileDialog,
    QSizePolicy,
    QSpacerItem,
    QMessageBox
)
import os
from PySide6.QtGui import QDoubleValidator, QFontMetrics
from PySide6.QtCore import Qt, Signal
from ErrorDialog import open_error_dialog
from bisect import bisect_right
from Event import Event
from LogReader import LogReader
from math import ceil


# Control panel for logs
class LogControlPanel(QGroupBox):
    pressurize_event_signal = Signal(Event)
    depressurize_event_signal = Signal(Event)
    period_event_signal = Signal(Event)
    event_list_signal = Signal(list)
    reset_history_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.log_reader = LogReader()

        # Title
        title = QLabel("Viewing Log")
        title.setStyleSheet("font-size: 28pt;")
        self.filename_label = QLabel(" ")

        # Time controls
        self.time_edit = QLineEdit(self)
        self.last_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.time_edit.editingFinished.connect(self.select_time)
        self.last_button.pressed.connect(self.emit_last_event)
        self.next_button.pressed.connect(self.emit_next_event)

        # File control
        open_button = QPushButton("Open File")
        self.current_button = QPushButton("Open Current")
        self.edit_button = QPushButton("Edit File")
        open_button.clicked.connect(self.open_log)
        self.edit_button.clicked.connect(self.edit_file)

        # Prefer height of buttons on device control panel
        self.last_button.setMaximumHeight(74)
        self.next_button.setMaximumHeight(74)
        self.current_button.setMaximumHeight(74)
        open_button.setMaximumHeight(74)
        self.edit_button.setMaximumHeight(74)
        self.last_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.next_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.current_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        open_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.edit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set layout
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time (s):"))
        time_layout.addWidget(self.time_edit)

        step_layout = QHBoxLayout()
        step_layout.addWidget(self.last_button)
        step_layout.addWidget(self.next_button)

        layout = QVBoxLayout(self)
        layout.addWidget(title, alignment=Qt.AlignHCenter)
        layout.addWidget(self.filename_label)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Preferred, QSizePolicy.Expanding)) # Spacer to separate sections
        layout.addLayout(time_layout)
        layout.addLayout(step_layout)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Preferred, QSizePolicy.Expanding)) # Spacer to separate sections
        layout.addWidget(self.current_button)
        layout.addWidget(open_button)
        layout.addWidget(self.edit_button)

        self.setFixedWidth(287) # Width of device control panel


    def open_log(self):
        file = QFileDialog.getOpenFileName(self, "Open File", "logs", "Log Files (*.xz)")[0]
        # No file selected
        if file == "":
            return
        self.reset_history_signal.emit()
        self.log_reader.read_events(file)

        self.time_edit.setText("")
        self.next_button.setEnabled(True)
        self.last_button.setEnabled(True)
        self.edit_button.setEnabled(True)

        self.press_index = -1
        self.depress_index = -1
        self.period_index = -1

        self.filename = self.log_reader.filename
        self.filename_label.setText(os.path.basename(self.filename))
        # Adjust font size to fit in the view
        for i in range(17, 8, -1):
            self.filename_label.setStyleSheet(f"font-size: {i}px")
            if QFontMetrics(self.filename_label.font()).boundingRect(os.path.basename(self.filename)).width() < self.width() - 25:
                break

        if len(self.log_reader.events) > 0:
            upper_bound = self.log_reader.events[-1].event_time - self.log_reader.events[0].event_time
        else:
            upper_bound = 0
        self.time_edit.setValidator(QDoubleValidator(0, upper_bound, 2))
        self.event_list_signal.emit(self.log_reader.events)


    def edit_file(self):
        self.edit_dialog = QDialog(self)

        self.name_edit = QLineEdit()
        basename = os.path.basename(self.filename)
        self.name_edit.setText(basename)
        extension_length = len(basename.split('.')[-1]) + 1
        self.name_edit.setSelection(0, len(basename) - extension_length)

        button_rename = QPushButton("Rename File")
        button_delete = QPushButton("Delete File")
        button_rename.clicked.connect(self.rename_file)
        button_delete.clicked.connect(self.delete_file)

        layout = QVBoxLayout()
        layout.addWidget(self.name_edit)
        layout.addWidget(button_rename)
        layout.addWidget(button_delete)

        self.edit_dialog.setWindowTitle("Edit File")
        self.edit_dialog.setFixedSize(500, 200)
        self.edit_dialog.setLayout(layout)
        self.edit_dialog.exec_()
        
    def rename_file(self):
        new_name = self.name_edit.text()
        if new_name:
            new_filename = os.path.join(os.path.dirname(self.filename), new_name)
            try:
                os.rename(self.filename, new_filename)  

                # Update logger filename if this is the currently written log
                if self.log_reader.logger is not None:
                    if self.filename == self.log_reader.logger.filename:
                        self.log_reader.logger.filename = new_filename 
                self.filename_label.setText(os.path.basename(new_filename))  # Update the label
                self.filename = new_filename
            except OSError as e:
                open_error_dialog(e)
        self.edit_dialog.close()

    def delete_file(self):
        confirm_dialog = QMessageBox.question(self, "Are you sure?", "This action cannot be undone.", QMessageBox.Yes | QMessageBox.Cancel)
        if confirm_dialog == QMessageBox.Yes:
            try:
                os.remove(self.filename)
                self.filename_label.setText(" ")
                self.next_button.setEnabled(False)
                self.last_button.setEnabled(False)
                self.event_list_signal.emit([])
            except OSError as e:
                open_error_dialog(e)
        self.edit_dialog.close()


    def select_time(self):
        try:
            time=float(self.time_edit.text())
        except:
            return
        if len(self.log_reader.events) == 0:
            return

        initial_time = self.log_reader.events[0].event_time
        index = max(0, bisect_right(self.log_reader.events, time, key=lambda x: x.event_time - initial_time) - 1)

        press = None
        depress = None
        period = None
        for i in range(index, -1, -1):
            event = self.log_reader.events[i]
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
        if index >= len(self.log_reader.events):
            return
        event = self.log_reader.events[index]

        if event.event_type == Event.PRESSURIZE:
            self.press_index = index
            self.pressurize_event_signal.emit(event)

        elif event.event_type == Event.DEPRESSURIZE:
            self.depress_index = index
            self.depressurize_event_signal.emit(event)
            # Also emit matching PERIOD
            if index + 1 < len(self.log_reader.events):
                n_event = self.log_reader.events[index + 1]
                if n_event.event_type == Event.PERIOD and abs(n_event.event_time - event.event_time) < 2:
                    self.period_index = index + 1
                    self.period_event_signal.emit(n_event)

        elif event.event_type == Event.PERIOD:
            self.period_index = index
            self.period_event_signal.emit(event)
            # Also emit matching DEPRESSURIZE
            if index + 1 < len(self.log_reader.events):
                n_event = self.log_reader.events[index + 1]
                if n_event.event_type == Event.DEPRESSURIZE and abs(n_event.event_time - event.event_time) < 2:
                    self.depress_index = index + 1
                    self.depressurize_event_signal.emit(n_event)

        max_time = self.log_reader.events[max(self.press_index, self.depress_index, self.period_index)].event_time
        time = max_time - self.log_reader.events[0].event_time
        self.time_edit.setText(str(ceil(time)))


    def emit_last_event(self):
        index = min(self.press_index, self.depress_index, self.period_index) - 1
        if index < 0:
            return
        event = self.log_reader.events[index]

        if event.event_type == Event.PRESSURIZE:
            self.press_index = index
            self.pressurize_event_signal.emit(event)

        elif event.event_type == Event.DEPRESSURIZE:
            self.depress_index = index
            self.depressurize_event_signal.emit(event)
            # Also emit matching PERIOD
            if index - 1 >= 0:
                n_event = self.log_reader.events[index - 1]
                if n_event.event_type == Event.PERIOD and abs(n_event.event_time - event.event_time) < 2:
                    self.period_index = index - 1
                    self.period_event_signal.emit(n_event)

        elif event.event_type == Event.PERIOD:
            self.period_index = index
            self.period_event_signal.emit(event)
            # Also emit matching DEPRESSURIZE
            if index - 1 >= 0:
                n_event = self.log_reader.events[index - 1]
                if n_event.event_type == Event.DEPRESSURIZE and abs(n_event.event_time - event.event_time) < 1:
                    self.depress_index = index - 1
                    self.depressurize_event_signal.emit(n_event)

        max_time = self.log_reader.events[max(self.press_index, self.depress_index, self.period_index)].event_time
        time = max_time - self.log_reader.events[0].event_time
        self.time_edit.setText(str(ceil(time)))


    # Also reset the log file when panel is hidden
    def hide(self):
        super().hide()
        self.filename_label.setText("")
        self.time_edit.setText("")

        self.next_button.setEnabled(False)
        self.last_button.setEnabled(False)
        self.edit_button.setEnabled(False)