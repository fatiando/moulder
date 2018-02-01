from __future__ import division, absolute_import
from future.builtins import super, zip

try:
    import cPickle as pickle
except ImportError:
    import pickle

import os
import sys
import numpy
import matplotlib
from matplotlib import pyplot, widgets, patches
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy, QMainWindow, QApplication, QAction
from PyQt5.QtWidgets import QMenu, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtWidgets import QSlider, QHBoxLayout, QLabel, QDialog
from PyQt5.QtWidgets import QDialogButtonBox

from fatiando import utils
from fatiando.gravmag import talwani
from fatiando.mesher import Polygon


LINE_ARGS = dict(
            linewidth=2, linestyle='-', color='k', marker='o',
            markerfacecolor='k', markersize=5, animated=False, alpha=0.6
            )

class Moulder(FigureCanvasQTAgg):
    """
    Interactive 2D forward modeling using polygons.

    A matplotlib GUI application. Allows drawing and manipulating polygons and
    computes their predicted data automatically. Also permits contaminating the
    data with gaussian pseudo-random error for producing synthetic data sets.

    Uses :mod:`fatiando.gravmag.talwani` for computations.

    *Moulder* objects can be persisted to Python pickle files using the
    :meth:`~fatiando.gravmag.interactive.Moulder.save` method and later
    restored using :meth:`~fatiando.gravmag.interactive.Moulder.load`.

    .. warning::

        Cannot be used with ``%matplotlib inline`` on IPython notebooks because
        the app uses the matplotlib plot window. You can still embed the
        generated model and data figure on notebooks using the
        :meth:`~fatiando.gravmag.interactive.Moulder.plot` method.

    Parameters:

    * area : list = (x1, x2, z1, z2)
        The limits of the model drawing area, in meters.
    * x, z : 1d-arrays
        The x- and z-coordinates of the computation points (places where
        predicted data will be computed). In meters.
    * data : None or 1d-array
        Observed data measured at *x* and *z*. Will plot this with black dots
        along the predicted data.
    * density_range : list = [min, max]
        The minimum and maximum values allowed for the density. Determines the
        limits of the density slider of the application. In kg.m^-3. Defaults
        to [-2000, 2000].
    * kwargs : dict
        Other keyword arguments used to restore the state of the application.
        Used by the :meth:`~fatiando.gravmag.interactive.Moulder.load` method.
        Not intended for general use.

    Examples:

    Make the Moulder object and start the app::

        import numpy as np
        area = (0, 10e3, 0, 5e3)
        # Calculate on 100 points
        x = np.linspace(area[0], area[1], 100)
        z = np.zeros_like(x)
        app = Moulder(area, x, z)
        app.run()
        # This will pop-up a window with the application (like the screenshot
        # below). Start drawing (follow the instruction in the figure title).
        # When satisfied, close the window to resume execution.

    .. image:: ../_static/images/Moulder-screenshot.png
        :alt: Screenshot of the Moulder GUI


    After closing the plot window, you can access the model and data from the
    *Moulder* object::

        app.model  # The drawn model as fatiando.mesher.Polygon
        app.predicted  # 1d-array with the data predicted by the model
        # You can save the predicted data to use later
        app.save_predicted('data.txt')
        # You can also save the application and resume it later
        app.save('application.pkl')
        # Close this session/IPython notebook/etc.
        # To resume drawing later:
        app = Moulder.load('application.pkl')
        app.run()

    """

    # The tolerance range for mouse clicks on vertices. In pixels.
    epsilon = 5
    # App instructions printed in the figure suptitle
    instructions = ' | '.join([
        'n: New polygon', 'd: delete', 'click: select/move', 'esc: cancel'])

    def __init__(self, parent, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self._plotted = False

        self.cmap = pyplot.cm.RdBu_r

        self._x = None
        self._z = None
        self._min_depth = 0
        self._max_depth = 10000

        self.predicted = None
        self.error = None

        self.predicted_line = []
        self.data = None
        self.polygons = []
        self.lines = []
        self.densities = []

    @property
    def plotted(self):
        return self._plotted

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, new_value):
        self._x = numpy.asarray(new_value)

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, new_value):
        self._z = numpy.asarray(new_value)

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

    @property
    def model(self):
        """
        The polygon model drawn as :class:`fatiando.mesher.Polygon` objects.
        """
        m = [Polygon(p.xy, {'density': d}, force_clockwise=True)
             for p, d in zip(self.polygons, self.densities)]
        return m

    def run(self):
        self._figure_setup()
        # Markers for mouse click events
        self._ivert = None
        self._ipoly = None
        self._lastevent = None
        self._drawing = False
        self._add_vertex = False
        self._xy = []
        self._drawing_plot = None
        # Used to blit the model plot and make
        # rendering faster
        self.background = None
        # Connect event callbacks
        self._connect()
        self._update_data()
        self._update_data_plot()
        self.canvas.draw()
        #pyplot.show()

    def _connect(self):
        """
        Connect the matplotlib events to their callback methods.
        """
        # Make the proper callback connections
        self.canvas.mpl_connect('button_press_event',
                                self._button_press_callback)
#        self.canvas.mpl_connect('key_press_event',
#                                self._key_press_callback)
        self.canvas.mpl_connect('button_release_event',
                                self._button_release_callback)
        self.canvas.mpl_connect('motion_notify_event',
                                self._mouse_move_callback)

    def _figure_setup(self, **kwargs):
        """
        Setup the plot figure with labels, titles, ticks, etc.

        Sets the *canvas*, *dataax*, *modelax*, *polygons* and *lines*
        attributes.

        Parameters:

        * kwargs : dict
            Keyword arguments passed to ``pyplot.subplots``.

        """
        sharex = kwargs.get('sharex')
        if not sharex:
            kwargs['sharex'] = True
        axes = self.fig.subplots(2, 1, **kwargs)
        ax1, ax2 = axes
        ax1.set_ylabel('Gravity anomaly (mGal)')
        ax2.set_xlabel('x (m)', labelpad=-10)
        ax1.set_xlim(self.x.min(), self.x.max())
        ax1.set_ylim((-200, 200))
        ax1.grid(True)
        ax2.set_ylim(self.min_depth, self.max_depth)
        ax2.grid(True)
        ax2.invert_yaxis()
        ax2.set_ylabel('z (m)')
        #self.fig.subplots_adjust(top=0.95, left=0.1, right=0.95, bottom=0.06,
        #                         hspace=0.1)
        self.canvas = self.fig.canvas
        self.dataax = axes[0]
        self.modelax = axes[1]
        self.fig.canvas.draw()

    def _density2color(self, density):
        """
        Map density values to colors using the given *cmap* attribute.

        Parameters:

        * density : 1d-array
            The density values of the model polygons

        Returns

        * colors : 1d-array
            The colors mapped to each density value (returned by a matplotlib
            colormap object.

        """
        dmin, dmax = self.density_range
        return self.cmap((density - dmin)/(dmax - dmin))

    def _make_polygon(self, vertices, density):
        """
        Create a polygon for drawing.

        Polygons are matplitlib.patches.Polygon objects for the fill and
        matplotlib.lines.Line2D for the contour.

        Parameters:

        * vertices : list of [x, z]
            List of the [x, z]  coordinate pairs of each vertex of the polygon
        * density : float
            The density of the polygon (used to set the color)

        Returns:

        * polygon, line
            The matplotlib Polygon and Line2D objects

        """
        poly = patches.Polygon(vertices, animated=False, alpha=0.9,
                               color=self._density2color(density))
        x, y = list(zip(*poly.xy))
        line = Line2D(x, y, **self.line_args)
        return poly, line

    def _update_data(self):
        """
        Recalculate the predicted data (optionally with random error)
        """
        self.predicted = talwani.gz(self.x, self.z, self.model)
        if self.error > 0:
            self.predicted = utils.contaminate(self.predicted, self.error)

    def _update_data_plot(self):
        """
        Update the predicted data plot in the *dataax*.

        Adjusts the xlim of the axes to fit the data.
        """
        self.predicted_line.set_ydata(self.predicted)
        vmin = 1.2*min(self.predicted.min(), self.dmin)
        vmax = 1.2*max(self.predicted.max(), self.dmax)
        self.dataax.set_ylim(vmin, vmax)
        self.dataax.grid(True)
        self.canvas.draw()

    def _set_error_callback(self, value):
        """
        Callback when error slider is edited
        """
        self.error = value
        self._update_data()
        self._update_data_plot()

    def _set_density_callback(self, value):
        """
        Callback when density slider is edited
        """
        if self._ipoly is not None:
            self.densities[self._ipoly] = value
            self.polygons[self._ipoly].set_color(self._density2color(value))
            self._update_data()
            self._update_data_plot()
            self.canvas.draw()

    def _get_polygon_vertice_id(self, event):
        """
        Find out which vertex of which polygon the event happened in.

        If the click was inside a polygon (not on a vertex), identify that
        polygon.

        Returns:

        * p, v : int, int
            p: the index of the polygon the event happened in or None if
            outside all polygons.
            v: the index of the polygon vertex that was clicked or None if the
            click was not on a vertex.

        """
        distances = []
        indices = []
        for poly in self.polygons:
            x, y = poly.get_transform().transform(poly.xy).T
            d = numpy.sqrt((x - event.x)**2 + (y - event.y)**2)
            distances.append(d.min())
            indices.append(numpy.argmin(d))
        p = numpy.argmin(distances)
        if distances[p] >= self.epsilon:
            # Check if the event was inside a polygon
            x, y = event.x, event.y
            p, v = None, None
            for i, poly in enumerate(self.polygons):
                if poly.contains_point([x, y]):
                    p = i
                    break
        else:
            v = indices[p]
            last = len(self.polygons[p].xy) - 1
            if v == 0 or v == last:
                v = [0, last]
        return p, v

    def _add_new_vertex(self, event):
        """
        Add new vertex to polygon
        """
        vertices = self.polygons[self._ipoly].get_xy()
        x, y = vertices[:, 0], vertices[:, 1]
        # Compute the angle between the vectors to each pair of
        # vertices corresponding to each line segment of the polygon
        x1, y1 = x[:-1], y[:-1]
        x2, y2 = numpy.roll(x1, -1), numpy.roll(y1, -1)
        u = numpy.vstack((x1 - event.xdata, y1 - event.ydata)).T
        v = numpy.vstack((x2 - event.xdata, y2 - event.ydata)).T
        angle = numpy.arccos(numpy.sum(u*v, 1) /
                             numpy.sqrt(numpy.sum(u**2, 1)) /
                             numpy.sqrt(numpy.sum(v**2, 1)))
        position = angle.argmax() + 1
        x = numpy.hstack((x[:position], event.xdata, x[position:]))
        y = numpy.hstack((y[:position], event.ydata, y[position:]))
        new_vertices = numpy.vstack((x, y)).T
        return new_vertices

    def _button_press_callback(self, event):
        """
        What actions to perform when a mouse button is clicked
        """
        if event.inaxes != self.modelax:
            return
        if event.button == 1 and not self._drawing and self.polygons:
            self._lastevent = event
            if not self._add_vertex:
                for line, poly in zip(self.lines, self.polygons):
                    poly.set_animated(False)
                    line.set_animated(False)
                    line.set_color([0, 0, 0, 0])
                self.canvas.draw()
                # Find out if a click happened on a vertice
                # and which vertice of which polygon
                self._ipoly, self._ivert = self._get_polygon_vertice_id(event)
                if self._ipoly is not None:
                    self.density_slider.set_val(self.densities[self._ipoly])
                    self.polygons[self._ipoly].set_animated(True)
                    self.lines[self._ipoly].set_animated(True)
                    self.lines[self._ipoly].set_color([0, 1, 0, 0])
                    self.canvas.draw()
                    self.background = self.canvas.copy_from_bbox(
                        self.modelax.bbox)
                    self.modelax.draw_artist(self.polygons[self._ipoly])
                    self.modelax.draw_artist(self.lines[self._ipoly])
                    self.canvas.blit(self.modelax.bbox)
            else:
                # If a polygon is selected, we will add a new vertex by
                # removing the polygon and inserting a new one with the extra
                # vertex.
                if self._ipoly is not None:
                    vertices = self._add_new_vertex(event)
                    density = self.densities[self._ipoly]
                    polygon, line = self._make_polygon(vertices, density)
                    self.polygons[self._ipoly].remove()
                    self.lines[self._ipoly].remove()
                    self.polygons.pop(self._ipoly)
                    self.lines.pop(self._ipoly)
                    self.polygons.insert(self._ipoly, polygon)
                    self.lines.insert(self._ipoly, line)
                    self.modelax.add_patch(polygon)
                    self.modelax.add_line(line)
                    self.lines[self._ipoly].set_color([0, 1, 0, 0])
                    self.canvas.draw()
                    self._update_data()
                    self._update_data_plot()
        elif self._drawing:
            if event.button == 1:
                self._xy.append([event.xdata, event.ydata])
                self._drawing_plot.set_data(list(zip(*self._xy)))
                self.canvas.restore_region(self.background)
                self.modelax.draw_artist(self._drawing_plot)
                self.canvas.blit(self.modelax.bbox)
            elif event.button == 3:
                if len(self._xy) >= 3:
                    density = self.density_slider.val
                    poly, line = self._make_polygon(self._xy, density)
                    self.polygons.append(poly)
                    self.lines.append(line)
                    self.densities.append(density)
                    self.modelax.add_patch(poly)
                    self.modelax.add_line(line)
                    self._drawing_plot.remove()
                    self._drawing_plot = None
                    self._xy = None
                    self._drawing = False
                    self._ipoly = len(self.polygons) - 1
                    self.lines[self._ipoly].set_color([0, 1, 0, 0])
                    self.dataax.set_title(self.instructions)
                    self.canvas.draw()
                    self._update_data()
                    self._update_data_plot()

    def _button_release_callback(self, event):
        """
        Reset place markers on mouse button release
        """
        if event.inaxes != self.modelax:
            return
        if event.button != 1:
            return
        if self._add_vertex:
            self._add_vertex = False
        if self._ivert is None and self._ipoly is None:
            return
        self.background = None
        for line, poly in zip(self.lines, self.polygons):
            poly.set_animated(False)
            line.set_animated(False)
        self.canvas.draw()
        self._ivert = None
        # self._ipoly is only released when clicking outside
        # the polygons
        self._lastevent = None
        self._update_data()
        self._update_data_plot()

    def key_press_callback(self, event_key):
        """
        What to do when a key is pressed on the keyboard.
        """
        if event_key == 'd':
            if self._drawing and self._xy:
                self._xy.pop()
                if self._xy:
                    self._drawing_plot.set_data(list(zip(*self._xy)))
                else:
                    self._drawing_plot.set_data([], [])
                self.canvas.restore_region(self.background)
                self.modelax.draw_artist(self._drawing_plot)
                self.canvas.blit(self.modelax.bbox)
            elif self._ivert is not None:
                poly = self.polygons[self._ipoly]
                line = self.lines[self._ipoly]
                if len(poly.xy) > 4:
                    verts = numpy.atleast_1d(self._ivert)
                    poly.xy = numpy.array([xy for i, xy in enumerate(poly.xy)
                                           if i not in verts])
                    line.set_data(list(zip(*poly.xy)))
                    self._update_data()
                    self._update_data_plot()
                    self.canvas.restore_region(self.background)
                    self.modelax.draw_artist(poly)
                    self.modelax.draw_artist(line)
                    self.canvas.blit(self.modelax.bbox)
                    self._ivert = None
            elif self._ipoly is not None:
                self.polygons[self._ipoly].remove()
                self.lines[self._ipoly].remove()
                self.polygons.pop(self._ipoly)
                self.lines.pop(self._ipoly)
                self.densities.pop(self._ipoly)
                self._ipoly = None
                self.canvas.draw()
                self._update_data()
                self._update_data_plot()
        elif event_key == 'n':
            self._ivert = None
            self._ipoly = None
            for line, poly in zip(self.lines, self.polygons):
                poly.set_animated(False)
                line.set_animated(False)
                line.set_color([0, 0, 0, 0])
            self.canvas.draw()
            self.background = self.canvas.copy_from_bbox(self.modelax.bbox)
            self._drawing = True
            self._xy = []
            self._drawing_plot = Line2D([], [], **self.line_args)
            self._drawing_plot.set_animated(True)
            self.modelax.add_line(self._drawing_plot)
            self.dataax.set_title(' | '.join([
                'left click: set vertice', 'right click: finish',
                'esc: cancel']))
            self.canvas.draw()
        elif event_key == 'escape':
            if self._add_vertex:
                self._add_vertex = False
            else:
                self._drawing = False
                self._xy = []
                if self._drawing_plot is not None:
                    self._drawing_plot.remove()
                    self._drawing_plot = None
                for line, poly in zip(self.lines, self.polygons):
                    poly.set_animated(False)
                    line.set_animated(False)
                    line.set_color([0, 0, 0, 0])
            self.canvas.draw()
        elif event_key == 'r':
            self.modelax.set_xlim(self.area[:2])
            self.modelax.set_ylim(self.area[2:])
            self._update_data_plot()
        elif event_key == 'a':
            self._add_vertex = not self._add_vertex

    def _mouse_move_callback(self, event):
        """
        Handle things when the mouse move.
        """
        if event.inaxes != self.modelax:
            return
        if event.button != 1:
            return
        if self._ivert is None and self._ipoly is None:
            return
        if self._add_vertex:
            return
        x, y = event.xdata, event.ydata
        p = self._ipoly
        v = self._ivert
        if self._ivert is not None:
            self.polygons[p].xy[v] = x, y
        else:
            dx = x - self._lastevent.xdata
            dy = y - self._lastevent.ydata
            self.polygons[p].xy[:, 0] += dx
            self.polygons[p].xy[:, 1] += dy
        self.lines[p].set_data(list(zip(*self.polygons[p].xy)))
        self._lastevent = event
        self.canvas.restore_region(self.background)
        self.modelax.draw_artist(self.polygons[p])
        self.modelax.draw_artist(self.lines[p])
        self.canvas.blit(self.modelax.bbox)
