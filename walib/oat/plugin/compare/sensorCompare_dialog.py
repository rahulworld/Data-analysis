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
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog, QMessageBox

import config
import os
from PyQt4 import uic



from .. import databaseManager
from oatlib import sensor
from .. import matplotWidget

FORM_CLASS, _ = uic.loadUiType(os.path.join(config.ui_path, 'sensorCompare.ui'))


class SensorCompare(QDialog, FORM_CLASS):

    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)

        self.db = databaseManager.DatabaseManager()
        self.loaded_sensor = {}

        self.manage_gui()

        try:
            self.load_sensor_list()
        except Exception as e:
            QMessageBox.warning(self, self.tr("Warning"), self.tr('No sensor found!!!'))
            print e


    def manage_gui(self):

        self.loadSensor.clicked.connect(self.load_sensor)
        self.removeSensor.clicked.connect(self.remove_sensor)
        self.checkTime.stateChanged.connect(self.enable_frame)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFixedHeight(500)

    def enable_frame(self, state):
        """
            Toggle frame visibility
        """
        if state == Qt.Checked:
            self.compareFrame.setEnabled(True)
        else:
            self.compareFrame.setEnabled(False)

    def load_sensor_list(self):
        """
            Load sensor list to QComboBox
        """
        sql = "SELECT name FROM freewat_sensors"
        res = self.db.execute_query(sql)
        self.sensorList.clear()

        self.sensorList.addItem("")
        for elem in res:
            self.sensorList.addItem(elem[0])

    def load_sensor(self):
        """
            Load sensor to ComboBox

            Load sensor from Database, and filter to show only a specific date interval
        """
        sensor_name = self.sensorList.currentText()

        if sensor_name in self.loaded_sensor.keys():
            self.popup_message(self.tr("Sensor already added"))
            return

        timezone = "+00:00"
        quality = self.checkQuality.isChecked()

        # Load sensor from sqlite
        oat = sensor.Sensor.from_sqlite(self.db.get_db_path(), sensor_name)
        oat.ts_from_sqlite(self.db.get_db_path())

        if self.checkTime.isChecked():
            # Filter oat data to match the selected period
            begin_pos = self.beginPos.text() + timezone
            end_pos = self.endPos.text() + timezone

            test = oat.ts[oat.ts.index >= begin_pos]
            test = test[test.index < end_pos]
            oat.ts = test

        if len(oat.ts) == 0:
            if self.checkTime.isChecked():
                self.popup_message(self.tr("Sensor has no data in selected interval"))
            else:
                self.popup_message(self.tr("Sensor has no data"))
            return

        # Create the chart
        mat_widget = matplotWidget.MatplotWidget()
        mat_widget.set_data(oat, quality, True)

        self.scrollContent.layout().addWidget(mat_widget)
        self.loaded_sensor[sensor_name] = mat_widget

        self.update_sensor_list(sensor_name)

    def remove_sensor(self):
        """
            remove selected sensor
        """
        name = self.selectedSensor.currentText()

        if name == '':
            return

        self.selectedSensor.removeItem(self.selectedSensor.currentIndex())
        mat_widget = self.loaded_sensor[name]

        self.scrollContent.layout().removeWidget(mat_widget)
        mat_widget.close()
        del self.loaded_sensor[name]

    def update_sensor_list(self, name):
        """
            Add new sensor to sensor list
        """
        self.selectedSensor.addItem(name)

    def popup_message(self, text):
        """
            Popup warning message
        """
        QMessageBox.about(self, self.tr("Warning"), text)
