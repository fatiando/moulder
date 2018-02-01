from __future__ import print_function
from future.builtins import super

import os
import sys
import numpy
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy, QMainWindow, QApplication, QAction
from PyQt5.QtWidgets import QMenu, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtWidgets import QSlider, QHBoxLayout, QLabel, QDialog
from PyQt5.QtWidgets import QDialogButtonBox

from figure_canvas import GravityModelCanvas
from interactive import Moulder
from new_dialog import NewModelDialog


class MoulderApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moulder")
        self.setWindowIcon(QIcon.fromTheme('python-logo'))
        self.setGeometry(200, 200, 1024, 800)
        self.init_ui()
        self.set_callbacks()

        self.canvas = Moulder(self, [0, 100, 0, 1000],
                              numpy.linspace(0, 100, 11),
                              numpy.zeros(11),
                              width=5, height=4, dpi=100)
        #self.canvas = GravityModelCanvas(self,
        #                                 width=5, height=4, dpi=100)
        # self.canvas.setFocus()
        self.setCentralWidget(self.canvas)

    def keyPressEvent(self, event):
        keys_dict = {Qt.Key_N: "n", Qt.Key_R: "r",
                     Qt.Key_A: "a", Qt.Key_D: "d",
                     Qt.Key_Escape: "escape"}
        if event.key() in keys_dict.keys():
            self.canvas._key_press_callback(keys_dict[event.key()])

    def closeEvent(self, event):
        event.ignore()
        self._quit_callback()

    def init_ui(self):
        self._define_actions()
        self._configure_menubar()
        self._configure_toolbar()

    def set_callbacks(self):
        self.new_action.triggered.connect(self._new_model_callback)
        self.about_action.triggered.connect(self._about_callback)
        # self.file_menu.triggered.connect(self._file_menu_callback)
        self.quit_action.triggered.connect(self._quit_callback)

    def _define_actions(self):
        self.new_action = QAction(QIcon.fromTheme('document-new'),
                                  '&New model', self)
        self.new_action.setShortcut('Ctrl+N')
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

    def _configure_menubar(self):
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu('File')
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.quit_action)
        self.about_menu = self.menubar.addMenu('About')
        self.about_menu.addAction(self.about_action)

    def _configure_toolbar(self):
        self.toolbar = self.addToolBar("adasd")
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.save_as_action)

    def _about_callback(self):
        QMessageBox.about(self, "About Moulder",
                          "About Moulder\nVersion 0.1")

    def _new_model_callback(self):
        new_model_dialog = NewModelDialog(parent=self)
        new_model_dialog.exec_()
        if new_model_dialog.is_completed():
            self.canvas.x = new_model_dialog.x
            self.canvas.z = new_model_dialog.z
            self.canvas.run()
            self.setCentralWidget(self.canvas)

    def _quit_callback(self):
        answer = QMessageBox.question(self, "Quit",
                                      "Are you sure you want to quit?",
                                      QMessageBox.Yes, QMessageBox.No)
        if answer == QMessageBox.Yes:
            sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Moulder")
    moulder = MoulderApp()
    moulder.show()
    sys.exit(app.exec_())
