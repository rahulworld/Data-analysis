# -*- coding: utf-8 -*-
# ==============================================================================
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
import sys
import os

# add oat module to PYTHONPATH
sys.path.append(os.path.dirname(__file__))

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QAction, QMenu

from plugin.createSensor import createSensor_dialog as createOat
from plugin.process import processTs_dialog as processTs
from plugin.sensorManager import sensorManager_dialog as sensorOat
from plugin.compare import sensorCompare_dialog as compareOat
from plugin.multiSensor import createMultipleSensor_dialog as multipleOat

freewat = None


def create_oat_menu(free):
    # globat to "share" to all file
    global freewat
    # pointer to freewat menu
    freewat = free

    # Create AOT submenu on FREEWAT menu
    freewat.menu.oat = QMenu(QCoreApplication.translate("FREEWAT", "OAT"))
    freewat.menu.addMenu(freewat.menu.oat)

    # Create OAT action
    action_oat_add_ts = QAction("Add Time series", freewat.iface.mainWindow())
    action_oat_add_ts.triggered.connect(run_oat_add)

    action_oat_add_multiple = QAction("Add multiple sensors", freewat.iface.mainWindow())
    action_oat_add_multiple.triggered.connect(run_oat_add_multiple)

    action_oat_process = QAction("Process time series", freewat.iface.mainWindow())
    action_oat_process.triggered.connect(run_oat_process)

    action_oat_sensor_manager = QAction("Manage sensor", freewat.iface.mainWindow())
    action_oat_sensor_manager.triggered.connect(run_oat_sensor_manager)

    action_oat_sensor_compare = QAction("Compare sensor", freewat.iface.mainWindow())
    action_oat_sensor_compare.triggered.connect(run_oat_sensor_compare)

    # add action to OAT submenu
    freewat.menu.oat.addAction(action_oat_add_ts)
    freewat.menu.oat.addAction(action_oat_add_multiple)
    freewat.menu.oat.addAction(action_oat_process)
    freewat.menu.oat.addAction(action_oat_sensor_manager)
    freewat.menu.oat.addAction(action_oat_sensor_compare)

####################################
### Action listener
####################################


def run_oat_process():
    """ Run action that open the processing gui"""
    oat_process = processTs.ProcessTs(freewat.iface)
    # show the dialog
    oat_process.show()
    # Run the dialog event loop
    oat_process.exec_()


def run_oat_sensor_manager():
    """ Run action that open the oat add timeseries gui"""
    oat_manager = sensorOat.SensorManager(freewat.iface)
    # show the dialog
    oat_manager.show()
    # Run the dialog event loop
    oat_manager.exec_()


def run_oat_sensor_compare():
    """ Run action that open the oat add timeseries gui"""
    oat_compare = compareOat.SensorCompare(freewat.iface)
    # show the dialog
    oat_compare.show()
    # Run the dialog event loop
    oat_compare.exec_()


def run_oat_add():
    """ Run action that open the oat add timeseries gui"""
    oat_add = createOat.CreateOatAddTs(freewat.iface)
    # show the dialog
    oat_add.show()
    # Run the dialog event loop
    oat_add.exec_()


def run_oat_add_multiple():
    """ Run action that open the oat add timeseries gui"""
    oat_multiple = multipleOat.CreateMultipleSensor(freewat.iface)
    # show the dialog
    oat_multiple.show()
    # Run the dialog event loop
    oat_multiple.exec_()

if __name__ == '__main__':
   create_oat_menu()