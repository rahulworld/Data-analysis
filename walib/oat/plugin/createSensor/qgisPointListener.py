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
from qgis.gui import QgsMapTool
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform


class QgisPointListener(QgsMapTool):
    """
        Canvas click event listener
    """

    def __init__(self, canvas, gui):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.gui = gui

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        pass

    def canvasReleaseEvent(self, event):
        """
            Get coordinates when mouse click release
        """
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)

        source = QgsCoordinateReferenceSystem(self.canvas.mapRenderer().destinationCrs().authid())
        target = QgsCoordinateReferenceSystem('EPSG:4326')

        transform = QgsCoordinateTransform(source, target)

        new_point = transform.transform(point)

        self.gui.sensorPosLon.setValue(new_point[0])
        self.gui.sensorPosLat.setValue(new_point[1])

    def activate(self):
        pass

    def deactivate(self):
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
