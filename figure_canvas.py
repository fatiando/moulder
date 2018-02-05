from __future__ import print_function
from future.builtins import super

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import QSizePolicy


class GravityModelCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        self._x, self._z = None, None
        self._min_depth, self._max_depth = 0., 35000.

        self.predicted = None
        self.data = None
        self.polygons = None

        self._plotted = False

        FigureCanvasQTAgg.setSizePolicy(self,
                                        QSizePolicy.Expanding,
                                        QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, new_value):
        self._x = new_value

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, new_value):
        self._z = new_value

    @property
    def min_depth(self):
        return self._min_depth

    @min_depth.setter
    def min_depth(self, new_value):
        self._min_depth = new_value

    @property
    def max_depth(self):
        return self._max_depth

    @max_depth.setter
    def max_depth(self, new_value):
        self._max_depth = new_value

    def update_plot(self):
        if self._plotted:
            pass
        else:
            self._figure_setup()

    def _figure_setup(self, **kwargs):
        self.dataax, self.modelax = self.fig.subplots(2, 1, sharex=True)
        if self.data is not None:
            self.data_line, = self.dataax.plot(self.x, self.data, '.k')
        self.dataax.set_ylabel('Gravity anomaly [mGal]')
        self.dataax.set_xlim(self.x.min(), self.x.max())
        self.dataax.set_ylim((-200, 200))
        self.dataax.grid(True)
        self.modelax.set_xlabel('x [m]')
        self.modelax.set_xlim(self.x.min(), self.x.max())
        self.modelax.set_ylim(self.min_depth, self.max_depth)
        self.modelax.grid(True)
        self.modelax.invert_yaxis()
        self.modelax.set_ylabel('z [m]')
        self.fig.subplots_adjust(top=0.95, left=0.1, right=0.95, bottom=0.1,
                                 hspace=0.1)
        self.figure = self.fig
        self.canvas = self.fig.canvas
        self.fig.canvas.draw()
