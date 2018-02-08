from __future__ import division, absolute_import
from future.builtins import super

from PyQt5.QtWidgets import QSlider


class QDoubleSlider(QSlider):

    def __init__(self, parent, min_value, max_value, step, init_value=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.init_value = init_value
        self.nvalues = int((max_value - min_value)/step)

        true_max_value = min_value + step*self.nvalues
        if true_max_value != max_value:
            self.max_value = true_max_value

        self.setMinimum(self.float_2_int(min_value))
        self.setMaximum(self.float_2_int(max_value))
        if init_value is not None:
            self.setValue(self.float_2_int(init_value))

    def int_2_float(self, value):
        return (self.max_value - self.min_value)*value/self.nvalues + \
               self.min_value

    def float_2_int(self, value):
        return int(
            self.nvalues*(value - self.min_value) /
            (self.max_value - self.min_value))
