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
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QFileDialog


class ListfileManager(object):
    """
        This class contains all method to manipulate csv data
    """
    exception = pyqtSignal(Exception)
    popupMessage = pyqtSignal(str)

    def __init__(self, gui):
        self.gui = gui
        self.init_gui()

    def init_gui(self):
        """
            init modflow ui
        """
        self.gui.modFile.clicked.connect(self.open_finder)

    def load_modflow_data(self):
        """
            Load modflow data
        """
        path = self.gui.modPath.text()
        cumulative = self.gui.modCum.isChecked()
        prop = self.gui.modProp.currentText()
        inout = self.gui.modInout.currentText()

        timezone = self.gui.modTz.value()

        if timezone >= 0:
            timez = "+" + "%02d:00" % (timezone)
        else:
            timez = "-" + "%02d:00" % (abs(timezone))
        begin_pos = self.gui.modStartPos.text() + timez

        if not self.gui.get_sensor_info():
            return False

        try:
            self.gui.oat.ts_from_listfile(path, startdate=begin_pos, cum=cumulative, prop=prop, inout=inout)
            return True
        except Exception as e:
            self.gui.popup_error_message(self.gui.tr("Error occur: \n {}").format(e))
            return False

    def open_finder(self):
        """
            Open a file finder
        """
        dialog = QFileDialog()
        filename = dialog.getOpenFileNameAndFilter(self.gui, self.gui.tr("Select listing file"), "", "")

        if filename[0] == '':
            self.gui.popup_error_message(self.gui.tr("Please select a valid file"))
            return

        self.gui.modPath.setText(filename[0])
