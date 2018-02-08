from __future__ import absolute_import
import sys
from PyQt5.QtWidgets import QApplication

from .main_window import MoulderApp


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Moulder")
    moulder_app = MoulderApp()
    moulder_app.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
