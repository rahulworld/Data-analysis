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
from PyQt4.QtGui import QDialog, QIcon, QMessageBox, QDialogButtonBox
from PyQt4 import uic

from qgis.core import QgsDataSourceURI, QgsMapLayerRegistry, QgsVectorLayer

import os
import re

from oatlib import sensor

from ..matplotWidget import MatplotWidget

from create import csvManager, rawManager, istsosManager, listfileManager, hobfileManager, gageManager

from .. import databaseManager
import config
import qgisPointListener

FORM_CLASS, _ = uic.loadUiType(os.path.join(config.ui_path, 'createSensor.ui'))


class CreateOatAddTs(QDialog, FORM_CLASS):
    """
        createSensor gui manager
    """

    def __init__(self, iface):
        """
        """
        QDialog.__init__(self)
        # iface qgis interface
        self.iface = iface
        self.setupUi(self)

        self.oldTool = None
        self.sensor_layer = None
        self.oat = None
        self.selected = "istSOS"

        self.stackedPreview.setCurrentIndex(0)
        self.clear_layout(self.chartLayout.layout())
        self.stackedWidget.setCurrentIndex(1)

        self.db = databaseManager.DatabaseManager()

        self.csv = csvManager.CsvManager(self)
        self.istsos = istsosManager.IstsosManager(self)
        self.raw = rawManager.RawManager(self)
        self.listfile = listfileManager.ListfileManager(self)
        self.hobfile = hobfileManager.HobfileManager(self)

        self.gage = gageManager.GageManager(self)

        self.manage_gui()
        self.__load_sensor_to_qgis()

    def closeEvent(self, event):
        """
            Close event listener
        """
        self.db.close()
        self.iface.mapCanvas().setMapTool(self.oldTool)

    def manage_gui(self):
        """
            init gui
            connect signal to slot
        """

        #Csv manager
        self.addCsvFile.clicked.connect(self.open_csv_finder)
        self.csvPreview.clicked.connect(self.load_csv_preview)

        # gage manager
        self.gageFile.clicked.connect(self.open_gage_finder)

        # Connect signal
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.create_sensor)
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.save_sensor)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        # toolButton
        self.toolButton.clicked.connect(self.point_from_map)
        self.buttonGroup.buttonClicked.connect(self.toggle_button)

        # add icon to button
        icon = QIcon(config.icon_path)
        self.toolButton.setIcon(icon)

    def open_csv_finder(self):
        self.csv.open_csv_finder()

    def load_csv_preview(self):
        self.csv.load_preview()

    def open_gage_finder(self):
        self.gage.open_gage_finder()

    def point_from_map(self, button):
        """
            Select station point from map
        Args:
            button (bool): True if button pressed
        """
        if button:  # button pressed
            # Open
            self.oldTool = self.iface.mapCanvas().mapTool()
            mytool = qgisPointListener.QgisPointListener(self.iface.mapCanvas(), self)
            self.iface.mapCanvas().setMapTool(mytool)
        else:
            self.iface.mapCanvas().setMapTool(self.oldTool)

    def create_sensor(self):
        """
            Event listener to OK button
            create sensor and load the data
        """

        self.oat = None

        if self.selected == "CSV":
            # Create sensor and load data from CSV
            if not self.csv.load_csv_data():
                return False
        elif self.selected == "istSOS":
            # Create sensor and load data from SOS
            if not self.istsos.load_istsos_data():
                return False
            self.sensorFrame.setEnabled(True)
        elif self.selected == "Raw":
            # Create sensor and load data from Table
            if not self.raw.load_raw_data():
                return False
        elif self.selected == "listfile":
            if not self.listfile.load_modflow_data():
                return False
        elif self.selected == "hobfile":
            if not self.hobfile.load_hobfile_data():
                return False
        elif self.selected == "gagefile":
            if not self.gage.load_gage_data():
                return False
        else:
            print "Unknown method"
            return False

        if self.oat.ts.empty:
            self.popup_error_message(self.tr("No data Found"))
            return

        # Create preview data chart
        chart = MatplotWidget(toolbar=True)
        chart.set_data(self.oat)
        self.clear_layout(self.chartLayout.layout())
        self.chartLayout.layout().addWidget(chart)

        self.stackedPreview.setCurrentIndex(0)

        return True

    def fill_from_oat(self):
        """
            Fill sensor field from sensor
        """
        self.sensorNameField.setText(self.oat.name)
        self.sensorDescField.clear()
        self.sensorDescField.append(self.oat.desc)
        self.sensorPosLat.setValue(float(self.oat.lat))
        self.sensorPosLon.setValue(float(self.oat.lon))
        self.sensorPosAlt.setValue(float(self.oat.alt))
        self.sensorOpField.setEditText(self.oat.prop)
        self.sensorUomField.setEditText(self.oat.unit)

    def save_sensor(self):
        """
            Create and save sensor to DB,
        """

        # Update or create new sensor
        if not self.oat:
            tmp = self.create_sensor()
            if not tmp:
                return
        else:
            self.update_sensor_info()

        if not self.oat:
            return

        # Check if sensor contains data
        if self.oat.ts.empty:
            self.popup_error_message(self.tr("No observation found"))
            return

        # save sensor to db
        try:
            self.oat.save_to_sqlite(config.db_path)
        except Exception as e:
            print e
            # if exception sensor exists
            reply = QMessageBox.question(self, self.tr('Message'),
                                         self.tr("Sensor {} exist, overwrite?").format(self.oat.name),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.oat.save_to_sqlite(config.db_path, overwrite=True)
            else:
                return

        # Clear
        del self.oat

        # Update qgis canvas

        if self.sensor_layer:
            self.sensor_layer.reload()
            self.iface.mapCanvas().refresh()
        else:
            self.__load_sensor_to_qgis()

        self.oat = None

        QMessageBox.about(self, self.tr("Save"), self.tr("Sensor saved"))

        self.clear_ui()

    def get_sensor_info(self):
        """
            Read sensor from input field
        """

        name = self.sensorNameField.text()
        op = self.sensorOpField.currentText()
        uom = self.sensorUomField.currentText()

        # Check if amandatory data are filled
        if name == "" or name[0].isdigit() or not re.match('^[a-zA-Z0-9_]*$', name):
            self.popup_error_message(self.tr("Sensor name not valid"))
            return False
        if op == "":
            self.popup_error_message(self.tr("Plese define a observed property"))
            return False
        if uom == "":
            self.popup_error_message(self.tr("Plese define a unit of measure"))
            return False

        # Read sensor info from ui

        desc = self.sensorDescField.toPlainText()
        lat = self.sensorPosLat.value()
        lon = self.sensorPosLon.value()
        alt = self.sensorPosAlt.value()

        use = self.sensorUse.isChecked()
        statflag = self.sensorStat.currentText()
        top = self.sensorTop.value()
        bottom = self.sensorBottom.value()

        self.oat = sensor.Sensor(prop=op, unit=uom, lat=lat, lon=lon, tz=0, name=name, desc=desc, alt=alt, use=use,
                                 statflag=statflag,topscreen=top, bottomscreen=bottom)

        return True

    def update_sensor_info(self):
        """
            Update sensor info
        """
        name = self.sensorNameField.text()

        if name[0].isdigit() or not re.match('^[a-zA-Z0-9_]*$', name):
            self.popup_error_message(self.tr("Please define a valid sensor name"))
            return False

        self.oat.name = name
        self.oat.desc = self.sensorDescField.toPlainText()
        self.oat.lat = self.sensorPosLat.value()
        self.oat.lon = self.sensorPosLon.value()
        self.oat.alt = self.sensorPosAlt.value()
        self.oat.prop = self.sensorOpField.currentText()
        self.oat.unit = self.sensorUomField.currentText()

        self.oat.use = self.sensorUse.isChecked()
        self.oat.statflag = self.sensorStat.currentText()
        self.oat.topscreen = self.sensorTop.value()
        self.oat.bottomscreen = self.sensorBottom.value()

    def popup_error_message(self, text):
        """
            Popup a error message

        Args:
            text (str): message to display
        """
        QMessageBox.about(self, self.tr("Error"), text)

    def toggle_button(self, button):
        """
            toggle event listener to input data GroupBox
        Args:
            button (QRadioButton): pressed radio button
        """
        pressed = button.text()

        if self.selected == pressed:
            return

        self.__set_selected_source(pressed)

        self.selected = pressed

    def __set_selected_source(self, pressed):
        """
            Display selected source UI
        """

        if pressed == "istSOS":
            self.sensorFrame.setEnabled(False)
            self.stackedPreview.setCurrentIndex(0)
            self.clear_layout(self.chartLayout.layout())
            self.stackedWidget.setCurrentIndex(1)

        else:
            self.sensorFrame.setEnabled(True)

        if pressed == "CSV":
            self.stackedPreview.setCurrentIndex(1)
            self.stackedWidget.setCurrentIndex(0)

        elif pressed == "Raw":
            self.stackedPreview.setCurrentIndex(2)
            self.stackedWidget.setCurrentIndex(2)

        elif pressed == "listfile":
            self.stackedPreview.setCurrentIndex(0)
            self.stackedWidget.setCurrentIndex(3)

        elif pressed == "hobfile":
            self.stackedPreview.setCurrentIndex(0)
            self.stackedWidget.setCurrentIndex(4)

        elif pressed == "gagefile":
            self.stackedPreview.setCurrentIndex(0)
            self.stackedWidget.setCurrentIndex(5)

    def clear_layout(self, layout):
        """
            Remove everything inside the layout
        Args:
            layout (QLayout): layout to clear
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()

                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def clear_ui(self):
        """
            Clear gui after sensor save
        """
        ####################
        # Clear sensor panel
        ####################
        self.sensorNameField.clear()
        self.sensorDescField.clear()
        self.sensorPosLat.setValue(0)
        self.sensorPosLon.setValue(0)
        self.sensorPosAlt.setValue(0)
        self.sensorOpField.clearEditText()
        self.sensorUomField.clearEditText()
        self.sensorTop.setValue(0)
        self.sensorBottom.setValue(0)

        #################
        # Clear csv panel
        #################
        self.filePath.clear()
        self.skipRows.setValue(0)
        self.dataColumn.setValue(0)
        self.qiColumn.setValue(-1)
        self.dateColumns.clear()
        self.dateFormat.setCurrentIndex(0)
        self.dateFormat.setItemText(0, '')
        self.noData.clear()
        self.comment.clear()
        self.csvRawPreview.clear()

        # clear table csv
        rows = self.tableCsvPreview.rowCount()
        for row in reversed(range(0, rows)):
            self.tableCsvPreview.removeRow(row)

        #################
        # Clear Sos panel
        ################
        self.sosProcedure.setCurrentIndex(0)
        self.sosSensorOp.clear()
        self.sosSensorFreq.setCurrentIndex(0)
        self.sosTimezone.clear()
        self.sosAggFunc.setCurrentIndex(0)
        self.sosAggInterval.clear()
        self.sosAggBox.setCheckState(Qt.Unchecked)

        #################
        # Clear raw panel
        #################
        self.tzRaw.setValue(0)
        self.comboFreqRaw.setCurrentIndex(0)

        # remove row from raw table
        rows = self.rawTable.rowCount()
        for row in reversed(range(0, rows)):
            self.rawTable.removeRow(row)

        ######################
        # Clear listfile panel
        ######################
        self.modPath.clear()
        self.modTz.setValue(0)

        #####################
        # Clear hobfile panel
        #####################
        self.hobInpath.clear()
        self.hobDiscpath.clear()
        self.hobOutpath.clear()
        self.hobStat.clear()
        self.hobName.clear()
        self.hobTz.setValue(0)

        ######################
        # Clear gagefile panel
        ######################
        self.gagePath.clear()
        self.gageTz.setValue(0)

        # Clear chart area
        self.clear_layout(self.chartLayout.layout())

        self.__set_selected_source(self.selected)

    def __load_sensor_to_qgis(self):
        # Create a vector layer loading data from freewat_sensor table (sqlite db)

        layer = QgsMapLayerRegistry.instance().mapLayersByName(config.oat_layer_name)

        db_path = self.db.get_db_path()

        if not db_path:
            return

        if len(layer) > 0:
            self.sensor_layer = layer[0]
            return

        if not self.sensor_layer:
            sql = "SELECT * FROM sqlite_master WHERE name ='freewat_sensors' and type='table'; "

            res = self.db.execute_query(sql)

            if len(res) == 0:
                return

        uri = QgsDataSourceURI()

        uri.setDatabase(self.db.get_db_path())
        schema = ''
        table = 'freewat_sensors'
        geom_column = 'geom'
        uri.setDataSource(schema, table, geom_column)

        display_name = config.oat_layer_name

        # create QGIS layer
        self.sensor_layer = QgsVectorLayer(uri.uri(), display_name, 'spatialite')

        QgsMapLayerRegistry.instance().addMapLayer(self.sensor_layer)
