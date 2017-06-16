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
import os

from PyQt4 import uic
from PyQt4.QtGui import QDialog, QMessageBox

from oat import config
from oat.plugin import databaseManager
from oat.plugin.multiSensor.loader import multicsv, istsos

FORM_CLASS, _ = uic.loadUiType(os.path.join(config.ui_path, 'multiSensor.ui'))


class CreateMultipleSensor(QDialog, FORM_CLASS):

    def __init__(self, iface):
        QDialog.__init__(self)
        self.setupUi(self)
        self.iface = iface

        self.data_path = None
        self.meta_path = None
        self.file_path = None
        self.selected = None

        self.istsos = istsos.IstsosManager(self)
        self.csv = multicsv.CsvManager(self)

        self.manage_gui()

        self.db = databaseManager.DatabaseManager()

    def manage_gui(self):
        """
            Gui init
        """
        self.multLoad.clicked.connect(self.load_sensors)
        self.multClose.clicked.connect(self.close)

        self.stackedSourceWidget.setCurrentIndex(0)

        self.buttonGroup.buttonClicked.connect(self.toggle_button)

    def popup_error_message(self, text):
        """
            Popup a error message

        Args:
            text (str): message to display
        """
        QMessageBox.about(self, self.tr("Error"), text)

    def toggle_button(self, button):

        self.selected = button.text()

        if self.selected == "File":
            self.stackedSourceWidget.setCurrentIndex(0)
        else:
            self.stackedSourceWidget.setCurrentIndex(1)

    def load_sensors(self):
        """
            Read metadata from csv file and load data
        """

        if self.selected == "IstSOS":
            self.istsos.load_multiple_sensors()
        else:
            self.csv.load_sensors()
