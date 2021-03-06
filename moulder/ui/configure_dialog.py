from __future__ import print_function, absolute_import
from future.builtins import super

import numpy
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QMessageBox, QLabel
from PyQt5.QtWidgets import QDialog, QPushButton, QRadioButton
from PyQt5.QtWidgets import QGridLayout, QLineEdit


class ConfigureMeassurementDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setModal(False)
        self.setWindowTitle("Configure Meassurement Points")
        self._completed = False
        self._init_ui()

        self.regular_grid_btn.toggled.connect(self._radio_button_callback)
        self.custom_grid_btn.toggled.connect(self._radio_button_callback)
        self.cancel_btn.clicked.connect(self._button_pushed_callback)
        self.apply_btn.clicked.connect(self._button_pushed_callback)

    @property
    def x(self):
        if self.regular_grid_btn.isChecked():
            entries = self._read_regular_grid_entries()
            if entries:
                x1, x2, step, z = entries[:]
                return numpy.arange(x1, x2 + step/2, step, dtype=numpy.float64)
            else:
                return None
        elif self.custom_grid_btn.isChecked():
            # Need to be completed
            pass

    @property
    def z(self):
        """
        Returns z array with meassurement points' heights.
        These heights respect the z->DOWN coordinate system
        """
        if self.regular_grid_btn.isChecked():
            entries = self._read_regular_grid_entries()
            if entries:
                x1, x2, step, z = entries[:]
                return -z*numpy.ones_like(self.x)
            else:
                return None
        elif self.custom_grid_btn.isChecked():
            # Need to be completed
            pass

    def is_completed(self):
        return self._completed

    def _init_ui(self):
        self.regular_grid_btn = QRadioButton("Regular grid (in meters)")
        self.regular_grid_btn.setChecked(True)
        self.custom_grid_btn = QRadioButton("Custom grid")
        self.from_input = QLineEdit()
        self.to_input = QLineEdit()
        self.step_input = QLineEdit()
        self.height_input = QLineEdit()
        self.apply_btn = QPushButton("Apply Changes")
        self.cancel_btn = QPushButton("Cancel")
        self.apply_btn.setDefault(True)

        bold_font = QFont()
        bold_font.setBold(True)

        layout = QVBoxLayout()
        layout.addWidget(self.regular_grid_btn)

        grid = QGridLayout()
        grid.setContentsMargins(25, 0, 0, 0)
        grid.addWidget(QLabel("From:"), 0, 0)
        grid.addWidget(self.from_input, 0, 1)
        grid.addWidget(QLabel("To:"), 0, 2)
        grid.addWidget(self.to_input, 0, 3)
        grid.addWidget(QLabel("Step:"), 0, 4)
        grid.addWidget(self.step_input, 0, 5)
        grid.addWidget(QLabel("Meassurement Height:"), 1, 0)
        grid.addWidget(self.height_input, 1, 1, 1, 5)
        layout.addLayout(grid)

        layout.addWidget(self.custom_grid_btn)

        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignRight)
        hbox.addWidget(self.cancel_btn)
        hbox.addWidget(self.apply_btn)
        layout.addLayout(hbox)

        self.setLayout(layout)

    def _button_pushed_callback(self):
        sender_text = self.sender().text()
        if sender_text == "Cancel":
            self.close()
        elif sender_text == "Apply Changes":
            filled_entries = self._check_filled_entries()
            if filled_entries:
                self._completed = True
                self.close()
            else:
                QMessageBox.warning(self, "Warning",
                                    "Some entries are not properly " +
                                    "completed or are incomplete.")

    def _radio_button_callback(self):
        regular_grid_lines = [self.from_input, self.to_input,
                              self.step_input, self.height_input]
        if self.sender().text() == "Custom grid":
            for line_edit in regular_grid_lines:
                line_edit.setDisabled(True)
        else:
            for line_edit in regular_grid_lines:
                line_edit.setEnabled(True)

    def _check_filled_entries(self):
        if self.regular_grid_btn.isChecked():
            entries = self._read_regular_grid_entries()
            if entries:
                return True
            else:
                # Show messagebox with warning for not completed entries
                pass
        elif self.custom_grid_btn.isChecked():
            # Needed to be completed
            return False

    def _read_regular_grid_entries(self):
        x1, x2 = self.from_input.text(), self.to_input.text()
        step = self.step_input.text()
        z = self.height_input.text()
        try:
            x1, x2, step = float(x1), float(x2), float(step)
            z = float(z)
        except ValueError:
            return False
        return x1, x2, step, z
