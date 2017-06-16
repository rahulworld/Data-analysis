# -*- coding: utf-8 -*-
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
from PyQt4.QtGui import QCheckBox, QDialog, QDialogButtonBox, QInputDialog, QLineEdit, QMessageBox
from PyQt4 import uic

import config

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(config.ui_path, 'saveSensorList.ui'))


class SaveSensorList(QDialog, FORM_CLASS):
    """
        Manager to sensor list Dialog
    """
    end = pyqtSignal(str)

    def __init__(self, sensor_list):
        QDialog.__init__(self)
        self.sensors = sensor_list
        self.check_list = []
        self.setupUi(self)
        self.manage_gui()

        self.close_flag = False

    def manage_gui(self):
        self.create_sensor_list()

        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save_sensor)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close_button)

    def closeEvent(self, evnt):

        if not self.close_flag:
            self.end.emit("close")
        super(SaveSensorList, self).closeEvent(evnt)

    def close_button(self):
        self.close_flag = True
        self.end.emit("Cancel")
        self.close()

    def create_sensor_list(self):
        """
            Populate gui with all possible sensor
        """
        for sensor in self.sensors:
            check_box = QCheckBox(sensor.name)
            self.check_list.append(check_box)
            self.groupBox.layout().addWidget(check_box)

    def save_sensor(self):
        """
            Save selected sensor
        """
        for item in self.check_list:
            if item.checkState():
                sensor = self.get_sensor(item.text())
                new_name, status = self.ask_sensor_name(sensor.name)

                if not status:
                    continue

                sensor.name = new_name
                sensor.save_to_sqlite(config.db_path, overwrite=True)

                QMessageBox.about(self, new_name, self.tr("Sensor saved"))

        self.setResult(QDialog.Accepted)
        self.end.emit("save")
        self.close_flag = True
        self.close()

    def ask_sensor_name(self, sensor_name):

        new_name, message = QInputDialog.getText(self, self.tr('Sensor name'), self.tr('Enter a new sensor name:'),
                                                 QLineEdit.Normal, sensor_name)

        if not message:
            reply = QMessageBox.question(self, self.tr('Message'), self.tr("Do you want to save the sensor?"),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                return self.ask_sensor_name(sensor_name)

            return "", False

        return new_name, True

    def get_sensor(self, name):
        """
            return selected sensor
        """
        for elem in self.sensors:
            if elem.name == name:
                return elem
