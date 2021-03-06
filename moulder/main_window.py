from __future__ import print_function, division, absolute_import
from future.builtins import super

import sys
import numpy
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QAction
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QDoubleSpinBox
from PyQt5.QtWidgets import QSlider, QLabel

from .ui import QDoubleSlider, ConfigureMeassurementDialog
from .moulder import Moulder

DENSITY_RANGE = [-2000, 2000]


class MoulderApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moulder")
        self.setWindowIcon(QIcon.fromTheme('python-logo'))
        self.setGeometry(200, 200, 1024, 700)
        self.init_ui()

        widget = QWidget()
        layout = QVBoxLayout()
        self.moulder = Moulder(self, numpy.linspace(0, 100e3, 101),
                               numpy.zeros(101), 0, 10000,
                               density_range=DENSITY_RANGE,
                               width=5, height=4, dpi=100)
        self.moulder.setFocusPolicy(Qt.StrongFocus)
        self.navigation_bar = NavigationToolbar2QT(self.moulder, widget)
        layout.addWidget(self.moulder)
        layout.addWidget(self.navigation_bar)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.set_callbacks()

    def closeEvent(self, event):
        event.ignore()
        self._quit_callback()

    def init_ui(self):
        self._define_actions()
        self._configure_menubar()
        self._configure_main_toolbar()
        self._configure_secondary_toolbar()

    def set_callbacks(self):
        self.configure_action.triggered.connect(
            self._configure_meassurement_callback)
        self.about_action.triggered.connect(self._about_callback)
        self.quit_action.triggered.connect(self._quit_callback)
        self.moulder.polygon_selected.connect(self._change_density_callback)
        self.moulder.drawing_mode.connect(self._drawing_mode_callback)
        self.moulder.add_vertex_mode.connect(self._add_vertex_mode_callback)
        self.new_polygon_action.triggered.connect(self.moulder.new_polygon)
        self.add_vertex_action.triggered.connect(self.moulder.add_vertex)
        self.delete_polygon_action.triggered.connect(
            self.moulder.delete_polygon)
        self.density_slider.valueChanged.connect(
            self._spin_slider_changed_callback)
        self.density_spinbox.valueChanged.connect(
            self._spin_slider_changed_callback)
        self.error_slider.valueChanged.connect(
            self._spin_slider_changed_callback)
        self.error_spinbox.valueChanged.connect(
            self._spin_slider_changed_callback)

    def _add_vertex_mode_callback(self, add_vertex):
        if add_vertex and self.add_vertex_action.isChecked() is False:
            self.add_vertex_action.setChecked(True)
        elif not add_vertex and self.add_vertex_action.isChecked() is True:
            self.add_vertex_action.setChecked(False)

    def _drawing_mode_callback(self, drawing):
        if drawing and self.new_polygon_action.isChecked() is False:
            self.new_polygon_action.setChecked(True)
        elif not drawing and self.new_polygon_action.isChecked() is True:
            self.new_polygon_action.setChecked(False)

    def _define_actions(self):
        self.configure_action = QAction(QIcon.fromTheme('preferences-system'),
                                        '&Configure...', self)
        self.open_action = QAction(QIcon.fromTheme('document-open'),
                                   '&Open model', self)
        self.open_action.setShortcut('Ctrl+O')
        self.save_action = QAction(QIcon.fromTheme('document-save'),
                                   '&Save model', self)
        self.save_action.setShortcut('Ctrl+S')
        self.save_as_action = QAction(QIcon.fromTheme('document-save-as'),
                                      '&Save model as...', self)
        self.save_as_action.setShortcut('Ctrl+Shift+S')
        self.quit_action = QAction(QIcon.fromTheme('application-exit'),
                                   '&Quit', self)
        self.quit_action.setShortcut('Ctrl+Q')
        self.about_action = QAction("&About", self)
        self.new_polygon_action = QAction(QIcon.fromTheme("list-add"),
                                          "&New Polygon", self)
        self.new_polygon_action.setCheckable(True)
        self.add_vertex_action = QAction(QIcon.fromTheme("document-new"),
                                         "&Add Vertex", self)
        self.add_vertex_action.setCheckable(True)
        self.delete_polygon_action = QAction(QIcon.fromTheme("list-remove"),
                                             "&Delete Polygon", self)

    def _configure_menubar(self):
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu('File')
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addAction(self.quit_action)
        self.edit_menu = self.menubar.addMenu('Edit')
        self.edit_menu.addAction(self.new_polygon_action)
        self.edit_menu.addAction(self.add_vertex_action)
        self.edit_menu.addAction(self.delete_polygon_action)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.configure_action)
        self.about_menu = self.menubar.addMenu('About')
        self.about_menu.addAction(self.about_action)

    def _configure_main_toolbar(self):
        self.main_toolbar = self.addToolBar("Main Toolbar")
        self.main_toolbar.addAction(self.open_action)
        self.main_toolbar.addAction(self.save_action)
        self.main_toolbar.addAction(self.save_as_action)
        self.main_toolbar.addAction(self.configure_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.new_polygon_action)
        self.main_toolbar.addAction(self.add_vertex_action)
        self.main_toolbar.addAction(self.delete_polygon_action)

    def _configure_secondary_toolbar(self):
        self.density_slider = QSlider(Qt.Horizontal)
        self.density_slider.setMinimum(DENSITY_RANGE[0])
        self.density_slider.setMaximum(DENSITY_RANGE[1])
        self.density_slider.setValue(0)
        self.density_slider.setTickInterval(
            (DENSITY_RANGE[1] - DENSITY_RANGE[0])/10)
        self.density_slider.setTickPosition(QSlider.TicksBelow)
        self.density_spinbox = QDoubleSpinBox()
        self.density_spinbox.setMinimum(DENSITY_RANGE[0])
        self.density_spinbox.setMaximum(DENSITY_RANGE[1])
        self.density_spinbox.setValue(0)
        self.density_spinbox.setSingleStep(1)

        self.error_slider = QDoubleSlider(Qt.Horizontal, 0, 5, 0.5,
                                          init_value=0)
        self.error_slider.setTickInterval(self.error_slider.float_2_int(0.5))
        self.error_slider.setTickPosition(QSlider.TicksBelow)
        self.error_spinbox = QDoubleSpinBox()
        self.error_spinbox.setMinimum(0)
        self.error_spinbox.setMaximum(5)
        self.error_spinbox.setValue(0)
        self.error_spinbox.setSingleStep(0.1)

        self.secondary_toolbar = self.addToolBar("Secondary Toolbar")
        self.secondary_toolbar.setStyleSheet('QToolBar{spacing:10px;}')
        self.secondary_toolbar.addWidget(QLabel("Density [kg/m^3]:"))
        self.secondary_toolbar.addWidget(self.density_slider)
        self.secondary_toolbar.addWidget(self.density_spinbox)
        self.secondary_toolbar.addSeparator()
        self.secondary_toolbar.addWidget(QLabel("Error:"))
        self.secondary_toolbar.addWidget(self.error_slider)
        self.secondary_toolbar.addWidget(self.error_spinbox)

    def _about_callback(self):
        QMessageBox.about(self, "About Moulder",
                          "About Moulder\nVersion 0.1")

    def _configure_meassurement_callback(self):
        configure_dialog = ConfigureMeassurementDialog(self)
        configure_dialog.exec_()
        if configure_dialog.is_completed():
            self.moulder.set_meassurement_points(configure_dialog.x,
                                                 configure_dialog.z)

    def _spin_slider_changed_callback(self, value):
        sender = self.sender()
        if sender == self.density_slider:
            self.density_spinbox.setValue(value)
            self.moulder.density = value
        elif sender == self.density_spinbox:
            self.density_slider.setValue(value)
            self.moulder.density = value
        elif sender == self.error_slider:
            value = self.error_slider.int_2_float(value)
            self.error_spinbox.setValue(value)
            self.moulder.error = value
        elif sender == self.error_spinbox:
            self.error_slider.setValue(self.error_slider.float_2_int(value))
            self.moulder.error = value

    def _change_density_callback(self, value):
        self.density_spinbox.setValue(value)
        self.density_slider.setValue(value)

    def _quit_callback(self):
        answer = QMessageBox.question(self, "Quit",
                                      "Are you sure you want to quit?",
                                      QMessageBox.Yes, QMessageBox.No)
        if answer == QMessageBox.Yes:
            sys.exit()
