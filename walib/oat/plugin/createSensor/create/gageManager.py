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
from PyQt4.QtCore import QObject
from PyQt4.QtGui import QFileDialog


class GageManager(object):
    """
        This class contains all method to manipulate gage data
    """

    def __init__(self, gui):
        self.gui = gui

    def init_gui(self):
        """
        """
        self.gui.gageFile.clicked.connect(self.open_gage_finder)

    def open_gage_finder(self):
        """
            Open a file finder
        """
        dialog = QFileDialog()
        filename = dialog.getOpenFileNameAndFilter(self.gui, self.gui.tr("Select GAGE file "), "", "")

        if filename[0] == '':
            self.gui.popup_error_message(self.gui.tr("Please select a valid file"))
            return

        self.gui.gagePath.setText(filename[0])

    def load_gage_data(self):
        """
            Load data from CSV file with specific configuration
        """
        if not self.gui.get_sensor_info():
            return False

        timezone = self.gui.gageTz.value()

        if timezone >= 0:
            timez = "+" + "%02d:00" % (timezone)
        else:
            timez = "-" + "%02d:00" % (abs(timezone))

        begin_pos = self.gui.gageBegin.text() + timez

        begin_pos = begin_pos.replace(" ", "T")

        gage_path = self.gui.gagePath.text()
        gage_prop = self.gui.gageProperty.currentText()

        try:
            self.gui.oat.ts_from_gagefile(gagefile=gage_path, startdate=begin_pos, property=gage_prop)

            if not self.gui.oat:
                return False
            return True
        except Exception as e:
            print e
            self.gui.popup_error_message(self.gui.tr("An error occurred:\n {}").format(e))
            return False
