# -*- coding: utf-8 -*-
# ===============================================================================
#
#
# Copyright (c) 2015 IST-SUPSI (www.supsi.ch/ist)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# ===============================================================================
from PyQt4.QtGui import *

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

if matplotlib.__version__ >= '1.5.0':
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
else:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar


class MatplotWidget(QWidget):
    """
        Class to plot data inside a QWidget
    """
    def __init__(self, parent=None, toolbar=False):
        """
        """
        super(MatplotWidget, self).__init__(parent)

        self.figure, self.axes = plt.subplots(nrows=1, ncols=1)
        self.canvas = FigureCanvasQTAgg(self.figure)

        self.figure.subplots_adjust(right=0.85)
        self.figure.subplots_adjust(left=0.1)
        self.figure.subplots_adjust(bottom=0.3)

        self.axes1 = self.axes.twinx()
        self.axes1.set_ylabel('quality')

        self.axes.locator_params(nbins=5)
        self.axes1.locator_params(nbins=5)

        self.vbox = QVBoxLayout(self)

        if toolbar:
            self.toolbar = NavigationToolbar(self.canvas, self)
            self.vbox.addWidget(self.toolbar)

        self.vbox.addWidget(self.canvas)

    def set_data(self, data, qi=False, min_size=False):
        """
            draw data to canvas

        Args:
            data (sensor) : sensor containing data
            qi (bool): if true plot quality
            min_size (bool): force to set min size to chart
        """

        self.figure.suptitle(data.name, fontsize=12)
        self.axes.set_ylabel(data.unit, fontsize=12)
        self.axes.set_xlabel('')

        ax = data.plot(quality=qi, axis=self.axes, qaxis=self.axes1)

        n = 5
        ticks = ax.xaxis.get_ticklocs()
        ticklabels = [l.get_text() for l in ax.xaxis.get_ticklabels()]
        ax.xaxis.set_ticks(ticks[::n])
        ax.xaxis.set_ticklabels(ticklabels[::n])

        if min_size:
            size = self.canvas.size()
            size.setHeight(size.height() / 2)

            self.canvas.setMinimumSize(size)

    def set_multiple_data(self, data, qi=False):
        """
            Plot multiple data source to chart

        Args:
            data (list): list of sensor to plot
            qi (bool): if true plot quality
        """

        colors = ['b', 'g', 'm', 'lime', 'orange', 'gray', 'salmon', 'tomato']

        ax = None
        labels = []
        for idx, evt in enumerate(data):
            if len(evt.ts) == 0:
                continue
            color = colors[idx % len(colors)]
            ax = evt.plot(quality=qi, data_color=color, axis=self.axes, qaxis=self.axes1)
            labels.append(evt.name)

        lines, _ = ax.get_legend_handles_labels()

        ax.legend(lines, labels, loc='best')

        plt.legend(loc="upper left", bbox_to_anchor=[0, 1], ncol=2, shadow=True, title="Legend", fancybox=True)

        if not ax:
            n = 5
            ticks = ax.xaxis.get_ticklocs()
            ticklabels = [l.get_text() for l in ax.xaxis.get_ticklabels()]
            ax.xaxis.set_ticks(ticks[::n])
            ax.xaxis.set_ticklabels(ticklabels[::n])
