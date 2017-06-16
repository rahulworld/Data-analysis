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
# from PyQt4.QtCore import *
from PyQt4.QtCore import QDateTime, Qt
from PyQt4.QtGui import QDialog, QFileDialog, QMessageBox
from PyQt4 import uic
from qgis.core import QgsDataSourceURI, QgsVectorLayer, QgsMapLayerRegistry
import qgis.utils

import os

from .. import databaseManager
import config
import cloneSensor_dialog as cloneSensor
from oat.oatlib import sensor
from ..matplotWidget import MatplotWidget

FORM_CLASS, _ = uic.loadUiType(os.path.join(config.ui_path, 'sensorManager.ui'))


class SensorManager(QDialog, FORM_CLASS):
    """
        Sensor manager
    """

    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)
        self.attr_table = None
        self.attr_layer = None
        self.sensor_layer = None
        self.oat = None

        self.qgs_version = 21200

        self.db = databaseManager.DatabaseManager()
        self.manage_gui()

    def manage_gui(self):
        """
            add event listener to buttons
        """

        self.deleteSensorBtn.clicked.connect(self.delete_sensor)
        self.loadSensorBtn.clicked.connect(self.open_attribute_table)
        self.updateSensorBtn.clicked.connect(self.update_sensor)
        self.qgisBtn.clicked.connect(self.see_on_qgis)
        self.cloneSensorBtn.clicked.connect(self.clone_sensor)
        self.saveSensorBtn.clicked.connect(self.save_to_csv)
        self.sensorList.currentIndexChanged.connect(self.load_sensor)

        try:
            self.load_sensor_list()
            self.__load_sensor_to_qgis()
        except Exception as e:
            QMessageBox.warning(self, self.tr("Warning"), self.tr('No sensor found!!!'))
            print e

    def delete_sensor(self):
        """
            delete sensor button listener
        """
        sensor_name = self.sensorList.currentText()

        if sensor_name == "":
            return

        if not self.confirm_delete():
            return

        tmp = sensor.Sensor.from_sqlite(config.db_path, sensor_name)
        tmp.delete_from_sqlite(config.db_path)

        self.load_sensor_list()
        self.clear_all()

    def confirm_delete(self):
        """
            Open a confirm dialog before deleting sensor
        """
        reply = QMessageBox.question(self, self.tr("Message"), self.tr("Are you sure to delete sensor ?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            return True
        return False

    def save_to_csv(self):
        """
            Save sensor to csv file
        """
        dialog = QFileDialog()
        filename = dialog.getSaveFileName(self, self.tr("Select output file "), "", "csv (*.csv)")

        # on cancel or exit
        if not filename:
            return

        if filename[0] == '':
            self.popup_error_message(self.tr("Plese select a valid file"))
            return

        self.oat.save_to_csv(filename)

        QMessageBox.about(self, self.tr("Save"), self.tr("Sensor saved to CSV"))

    def clone_sensor(self):
        """
            Open new dialog to clone the selected sensor
        """

        if not self.oat:
            return

        self.setEnabled(False)
        gui_sensor_list = cloneSensor.CloneSensor(self.oat)

        gui_sensor_list.show()
        gui_sensor_list.exec_()

        self.load_sensor_list()

        self.setEnabled(True)

    def load_sensor(self):
        """
            Load selected sensor
        """
        sensor_name = self.sensorList.currentText()

        if sensor_name == '':
            self.oat = None
            return

        # Load sensor info
        self.oat = sensor.Sensor.from_sqlite(config.db_path, sensor_name)
        self.oat.ts_from_sqlite(config.db_path)

        self.sensorFrame.setEnabled(True)
        self.qgisBtn.setEnabled(True)

        if self.attr_layer:
            if self.version >= self.qgs_version:
                self.attr_table.close()

            self.clear_layout(self.editFrame.layout())
            del self.attr_table
            QgsMapLayerRegistry.instance().removeMapLayer(self.attr_layer.id())
            self.attr_layer = None

        self.fill_field()

    def fill_field(self):
        """
            Fill field with sensor info
        """

        self.clear_layout(self.editFrame.layout())

        self.nameBox.setText(self.oat.name)
        self.descBox.clear()
        self.descBox.appendPlainText(self.oat.desc)
        self.latBox.setValue(self.oat.lat)
        self.lonBox.setValue(self.oat.lon)
        self.freqBox.setText(self.oat.freq)

        if not self.oat.alt:
            self.altBox.setValue(0)
        else:
            self.altBox.setValue(self.oat.alt)

        if not self.oat.tz:
            self.tzBox.setValue(0)
        else:
            if ":" in self.oat.tz:
                self.tzBox.setValue(int(self.oat.tz.split(':')[0]))
            else:
                self.tzBox.setValue(int(self.oat.tz))

        self.opBox.setText(self.oat.prop)
        self.uomBox.setText(self.oat.unit)

        if self.oat.bottomscreen:
            self.bottomScreenBox.setValue(self.oat.bottomscreen)
        else:
            self.bottomScreenBox.setValue(0.0)

        if self.oat.topscreen:
            self.topScreenBox.setValue(self.oat.topscreen)
        else:
            self.topScreenBox.setValue(0.0)

        if self.oat.use > 0:
            self.useBox.setCheckState(Qt.Checked)

        self.statBox.setText(self.oat.statflag)

        if not self.oat.ts.empty:
            chart = MatplotWidget(toolbar=True)
            chart.set_data(self.oat, qi=True)

            self.clear_layout(self.dataPreview)
            self.dataPreview.addWidget(chart)

        if self.oat.data_availability[0]:
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

            self.beginPositionBox.setDateTime(begin_pos)
            self.endPositionBox.setDateTime(end_pos)

    def open_attribute_table(self):
        """
            Open Qgis Attribute table
        """

        if not self.oat:
            return

        if self.attr_layer:
            self.clear_layout(self.editFrame.layout())
            if self.attr_table:
                self.attr_table.close()
                del self.attr_table

            self.attr_layer = None

        uri = QgsDataSourceURI()
        uri.setDatabase(config.db_path)
        schema = ''
        table = self.oat.name
        uri.setDataSource(schema, table, '')

        display_name = self.oat.name

        # create layer from sqlite
        self.attr_layer = QgsVectorLayer(uri.uri(), display_name, 'spatialite')

        self.version = qgis.utils.QGis.QGIS_VERSION_INT

        self.attr_table = self.iface.showAttributeTable(self.attr_layer)

        # not working for Qgis 2.8 an 2.10
        if self.version >= self.qgs_version:
            # cast from QDialog to QWidget
            self.attr_table.setWindowFlags(Qt.Widget)
            # add table content to sensorManager Gui
            self.editFrame.layout().addWidget(self.attr_table)

    def load_sensor_list(self):
        """
            Fill ComboBox with sensor name
        """

        self.sensorList.currentIndexChanged.disconnect(self.load_sensor)

        query = "SELECT * FROM freewat_sensors"
        res = self.db.execute_query(query)

        self.db.close()
        self.sensorList.clear()

        self.sensorList.addItem("", "")
        for elem in res:
            self.sensorList.addItem(elem[1], elem[0])

        self.sensorList.currentIndexChanged.connect(self.load_sensor)

    def clear_layout(self, layout):
        """
            remove all element inside selected layout
        Parameters
        ----------
        layout: selected layout

        Returns
        -------

        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def clear_all(self):
        """
            clear interface
        """
        self.clear_layout(self.dataPreview)
        self.nameBox.clear()
        self.descBox.clear()
        self.latBox.setValue(0.0)
        self.lonBox.setValue(0.0)
        self.altBox.setValue(0.0)
        self.opBox.clear()
        self.uomBox.clear()
        self.tzBox.setValue(0)
        self.freqBox.clear()
        self.bottomScreenBox.setValue(0.0)
        self.topScreenBox.setValue(0.0)
        self.useBox.setCheckState(Qt.Unchecked)
        self.statBox.clear()

    def update_sensor(self):
        """
            Update sensor data
        """

        if not self.oat:
            self.popup_error_message(self.tr("Please select a sensor"))
            return

        self.oat.desc = self.descBox.toPlainText()
        self.oat.lat = self.latBox.value()
        self.oat.lon = self.lonBox.value()
        self.oat.alt = self.altBox.value()
        self.oat.prop = self.opBox.text()
        self.oat.unit = self.uomBox.text()
        self.oat.tz = self.tzBox.value()
        self.oat.freq = self.freqBox.text()
        self.oat.topscreen = self.topScreenBox.value()
        self.oat.bottomscreen = self.bottomScreenBox.value()
        self.oat.use = self.useBox.isChecked()
        self.oat.statflag = self.statBox.text()

        try:
            self.oat.save_to_sqlite(config.db_path, overwrite=True)
        except Exception as e:
            self.popup_error_message(self.tr("Exception occour: {}").format(e))
            return

        QMessageBox.about(self, self.tr("Save"), self.tr("Sensor saved"))

    def see_on_qgis(self):
        """
            show selected feature on QGIS
        """
        # get freewat sensor layer
        layer = QgsMapLayerRegistry.instance().mapLayersByName(config.oat_layer_name)[0]

        for feature in layer.getFeatures():
            if feature.attribute('name') == self.oat.name:
                layer.setSelectedFeatures([feature.id()])
                break

    def popup_error_message(self, text):
        """
            Popup a error message

        Args:
            text (str): message to display
        """
        QMessageBox.about(self, self.tr("Error"), text)

    def __load_sensor_to_qgis(self):
        """
            Add a vector layer into qgis with all the oat sensors
        """
        # Create a vector layer loading data from freewat_sensor table (sqlite db)
        layer = QgsMapLayerRegistry.instance().mapLayersByName(config.oat_layer_name)

        db_path = self.db.get_db_path()

        if not db_path:
            return

        if len(layer) > 0:
            return

        uri = QgsDataSourceURI()
        uri.setDatabase(db_path)
        schema = ''
        table = 'freewat_sensors'
        geom_column = 'geom'
        uri.setDataSource(schema, table, geom_column)

        display_name = config.oat_layer_name

        # create QGIS layer
        self.sensor_layer = QgsVectorLayer(uri.uri(), display_name, 'spatialite')
        QgsMapLayerRegistry.instance().addMapLayer(self.sensor_layer)
