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
from PyQt4.QtGui import QFileDialog
from PyQt4.QtCore import *


class HobfileManager(object):
    """
        This class contains all method to interact Hobfile
    """

    def __init__(self, gui):
        self.gui = gui
        self.init_gui()

    def init_gui(self):
        """
            init modflow ui
        """
        self.gui.hobInfile.clicked.connect(self.__open_in_finder)
        self.gui.hobOutfile.clicked.connect(self.__open_out_finder)
        self.gui.hobDiscfile.clicked.connect(self.__open_disc_finder)

    def load_hobfile_data(self):
        """
            Load modflow data
        """

        # Compose begin_pos
        timezone = self.gui.hobTz.value()

        if timezone >= 0:
            timez = "+" + "%02d:00" % (timezone)
        else:
            timez = "-" + "%02d:00" % (abs(timezone))

        begin_pos = self.gui.hobStartDate.text() + timez
        # get params from gui
        hob_name = self.gui.hobName.text()
        hob_out = self.gui.hobOutpath.text()
        hob_stat = self.gui.hobStat.text()
        hob_path = self.gui.hobInpath.text()
        disc_path = self.gui.hobDiscpath.text()

        if hob_name == '':
            self.gui.popup_error_message(self.gui.tr("Please insert a valid name"))
            return

        if hob_path == '':
            self.gui.popup_error_message(self.gui.tr("Please insert a valid input file"))
            return

        if disc_path == '':
            self.gui.popup_error_message(self.gui.tr("Please insert a valid disc file"))
            return

        if not self.gui.get_sensor_info():
            return False

        try:
            self.gui.oat.ts_from_hobfile(hob_path, begin_pos, hob_name, disc_path, outhob=hob_out, stat=hob_stat)
            return True
        except Exception as e:
            print e
            self.gui.popup_error_message(self.gui.tr("Error occur: \n {}").format(e))
            return False

    def __open_in_finder(self):
        self.open_finder(self.gui.hobInpath, self.gui.tr("Select listing file"), "All Files (*.*)")

    def __open_out_finder(self):
        self.open_finder(self.gui.hobOutpath, self.gui.tr("Select hob_out file"), "All Files (*.*)")

    def __open_disc_finder(self):
        self.open_finder(self.gui.hobDiscpath, self.gui.tr("Select disc file"), "All Files (*.*)")

    def open_finder(self, field, text, extension):
        """
            Open a file finder

            Args:
                field (QLineEdit): field where write the path
                text (str): Text to display
                extension (str): allowed file extension
        """
        dialog = QFileDialog()
        filename = dialog.getOpenFileNameAndFilter(self.gui, text, "", extension)

        if filename[0] == '':
            return

        field.setText(filename[0])
