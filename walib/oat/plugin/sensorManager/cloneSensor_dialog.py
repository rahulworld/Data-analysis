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
from PyQt4.QtCore import QDateTime, Qt
from PyQt4.QtGui import QDialog, QDialogButtonBox, QMessageBox
from PyQt4 import uic

from oat.plugin import databaseManager
import config
import os
import re

FORM_CLASS, _ = uic.loadUiType(os.path.join(config.ui_path, 'cloneSensor.ui'))


class CloneSensor(QDialog, FORM_CLASS):

    def __init__(self, sensor):
        QDialog.__init__(self)
        self.setupUi(self)

        self.oat = sensor

        self.db = databaseManager.DatabaseManager()
        self.manageGui()

    def manageGui(self):
        """
            Gui init
        """
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.clone)
        self.sensorShort.stateChanged.connect(self.enable_frame)

        beg = self.oat.data_availability[0].replace("T", " ")
        end = self.oat.data_availability[1].replace("T", " ")

        if beg[-3] == ':':
            beg = beg[:-6]
            end = end[:-6]
        else:
            beg = beg[:-5]
            end = end[:-5]

        begin_pos = QDateTime.fromString(beg, "yyyy-MM-dd hh:mm:ss")
        end_pos = QDateTime.fromString(end, "yyyy-MM-dd hh:mm:ss")

        self.sensorBegin.setDateTime(begin_pos)
        self.sensorEnd.setDateTime(end_pos)

    def clone(self):
        """
            Clone sensor
        """
        new_name = self.sensorName.text()
        clear_data = self.clearSensorData.isChecked()

        if new_name == "" or new_name[0].isdigit() or not re.match('^[a-zA-Z0-9_]*$', new_name):
            self.popup_error_message(self.tr("Sensor name not valid"))
            return

        new_oat = self.oat.copy()

        if clear_data:

            df = new_oat.ts.ix[:1]
            new_oat.ts = df

        if self.sensorShort.isChecked():

            try:
                timezone = self.sensorTz.value()

                if timezone >= 0:
                    timez = "+" + "%02d:00" % (timezone)
                else:
                    timez = "-" + "%02d:00" % (abs(timezone))

                begin_pos = self.sensorBegin.text().replace(" ", "T") + timez
                end_pos = self.sensorEnd.text().replace(" ", "T") + timez

                test = new_oat.ts[new_oat.ts.index >= begin_pos]
                test = test[test.index < end_pos]
                new_oat.ts = test
                new_oat.tz = timezone

                new_oat.set_data_availability()
            except Exception as e:
                print e
                QMessageBox.about(self, '', self.tr('Please check time interval'))
                return False

        new_oat.name = new_name

        try:
            new_oat.save_to_sqlite(config.db_path)
        except Exception as e:
            self.popup_error_message(str(e))

            reply = QMessageBox.question(self, self.tr('Message'),
                                         self.tr("Sensor {} exist, overwrite?").format(self.oat.name),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.oat.save_to_sqlite(config.db_path, overwrite=True)
            else:
                return

        QMessageBox.about(self, self.tr("Save"), self.tr("Sensor saved"))

    def popup_error_message(self, text):
        """
            Popup a error message

        Args:
            text (str): message to display
        """
        QMessageBox.about(self, self.tr("Error"), text)

    def enable_frame(self, state):

        if state == Qt.Checked:
            self.sensorFrame.setEnabled(True)
        else:
            self.sensorFrame.setEnabled(False)
