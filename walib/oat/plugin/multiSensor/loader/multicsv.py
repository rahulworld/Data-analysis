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
from PyQt4.QtGui import QTableWidgetItem
from qgis.gui import QgsGenericProjectionSelector

import csv

from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QMessageBox

from qgis.core import *

import os

from oat.oatlib import sensor
from oat.plugin import databaseManager


class CsvManager(object):

    def __init__(self, gui):

        self.gui = gui

        self.meta_path = None
        self.data_path = None
        self.file_path = None

        self.db = databaseManager.DatabaseManager()

        self.manage_gui()

    def manage_gui(self):
        pass

        self.gui.metaBtn.clicked.connect(self.open_csv_finder)
        self.gui.dataBtn.clicked.connect(self.open_sensors_data_dir)
        self.gui.crsButton.clicked.connect(self.select_crs)

        self.gui.csvPreview.clicked.connect(self.load_preview)

        self.gui.dateFormat.addItem("", "")
        self.gui.dateFormat.addItem("2015-12-31", "%Y-%m-%d")
        self.gui.dateFormat.addItem("31-12-2015", "%d-%m-%Y")
        self.gui.dateFormat.addItem("12-31-2015", "%m-%d-%Y")

        self.gui.dateFormat.addItem("2015/12/31", "%Y/%m/%d")
        self.gui.dateFormat.addItem("31/12/2015", "%d/%m/%Y")
        self.gui.dateFormat.addItem("12/31/2015", "%m/%d/%Y")

        self.gui.dateFormat.addItem("2015-12-31 23:59:58", "%Y-%m-%d %H:%M:%S")

    def select_crs(self):
        """
            Open Qgis CRS selector
        """
        proj_selector = QgsGenericProjectionSelector()
        proj_selector.exec_()
        proj = proj_selector.selectedAuthId()

        self.gui.crsValue.setText(proj)

    def open_csv_finder(self):
        """
            Open a file finder
        """
        dialog = QFileDialog()

        source = self.gui.sourceGroup.checkedButton().text().lower()

        if source == 'csv':
            tmp = "CSV (*.csv)"
        elif source == 'shp':
            tmp = "SHP (*.shp)"
        else:
            return

        filename = dialog.getOpenFileNameAndFilter(self.gui, self.gui.tr("Select input file"), "", tmp)

        if filename[0] == '':
            return

        self.gui.metaPath.setText(filename[0])
        self.meta_path = filename[0]

    def open_sensors_data_dir(self):
        """
            Open a QDialog to select the folder that contains the csv data
            Create a raw preview of the data
        """
        dirname = QFileDialog.getExistingDirectory(self.gui, self.gui.tr("Select Directory"))

        if dirname == '':
            return

        self.gui.dataPath.setText(dirname)
        self.data_path = dirname

        self.gui.dataStructureWidget.setEnabled(True)

        # Generate data preview
        file_list = [f for f in os.listdir(self.data_path) if os.path.isfile(os.path.join(self.data_path, f))]
        test = file_list[0]

        self.file_path = os.path.join(self.data_path, test)

        self.csv_preview_area(self.file_path)

    def load_sensors(self):

        if not self.meta_path:
            self.gui.popup_error_message(self.gui.tr("Please select a metadata file path"))
            return

        if not self.data_path:
            self.gui.popup_error_message(self.gui.tr("Please select a data folder"))
            return

        try:
            meta_list = self.read_metadata()
        except Exception as e:
            print e
            self.gui.popup_error_message(self.gui.tr("Error reading metadata file"))
            return

        if len(meta_list) == 0:
            self.gui.popup_error_message(self.gui.tr("No sensor found inside metadata file"))
            return

        if self.gui.force.checkState() == Qt.Checked:
            force = True
        else:
            force = False

        error = []

        for sens in meta_list:
            # create sensor object read from metadata file
            try:
                tmp_sensor = sensor.Sensor(sens['name'], sens['prop'], sens['unit'], sens['lat'], sens['lon'],
                                           sens['altitude'], desc=sens.get('desc', ''), freq=sens.get('freq', ''),
                                           tz=sens.get('tz', 0), statflag=sens.get('statflag', ''),
                                           use=sens.get('use'), topscreen=sens.get('topscreen', 0),
                                           bottomscreen=sens.get('bottomscreen', 0))
            except Exception as e:
                print e
                mess = self.gui.tr("Mandatory fileds are missing (name / prop / unit / lat / lon / altitude )")
                error.append({'name': sens['name'], 'error': mess})
                continue

            data_path = os.path.join(self.data_path, sens['name'] + ".csv")

            # Load sensor data
            if os.path.isfile(data_path):
                try:
                    tmp_sensor = self.__load_sensor_data(tmp_sensor, data_path)
                except Exception as e:
                    error.append({'name': sens['name'], 'error': str(e)})
                    continue
                # Save sensor to db
                try:
                    tmp_sensor.save_to_sqlite(self.db.get_db_path(), overwrite=force)
                except Exception as e:
                    error.append({'name': sens['name'], 'error': str(e)})
                    print "Error: {}".format(e)
            else:
                error.append({'name': sens['name'], 'error': sens['name'] + ".csv is missing"})

        if len(error) != 0:
            message = self.gui.tr("The following sensors report errors:\n\n")

            for err in error:
                message += self.gui.tr("Sensor: {}\nError : {}\n\n").format(err['name'], err['error'])

            self.gui.popup_error_message(message)
        else:
            QMessageBox.about(self.gui, self.gui.tr("Upload done"), self.gui.tr("Sensors loaded"))
            self.clear_ui()

    def clear_ui(self):
        """
            Clear the UI
        """
        self.gui.metaPath.clear()
        self.gui.dataPath.clear()

        self.gui.csvPreviewArea.clear()

        rows = self.gui.tableCsvPreview.rowCount()
        for row in reversed(range(0, rows)):
            self.gui.tableCsvPreview.removeRow(row)

        self.data_path = None
        self.meta_path = None

    def read_metadata(self):
        """
            Read metadata from selected source (.csv / .shp)
        """

        meta_list = []
        source = self.gui.sourceGroup.checkedButton().text().lower()

        if self.gui.crsValue.text() == '':
            source_crs = QgsCoordinateReferenceSystem('EPSG:4326')
        else:
            source_crs = QgsCoordinateReferenceSystem(self.gui.crsValue.text())

        target = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(source_crs, target)

        if source == 'csv':
            # read from selected csv file
            with open(self.meta_path) as csvfile:
                reader_elem = csv.DictReader(csvfile, delimiter=',')

                for row in reader_elem:

                    # cast point
                    new_point = transform.transform(QgsPoint(float(row['lon']), float(row['lat'])))

                    # cast datatype
                    row['unit'] = row['unit'].decode('utf8')
                    row['lat'] = new_point[1]
                    row['lon'] = new_point[0]
                    row['altitude'] = float(row['altitude'])
                    row['topscreen'] = float(row['topscreen']) if row.get('topscreen') else 0
                    row['bottomscreen'] = float(row['bottomscreen']) if row.get('bottomscreen') else 0

                    if row.get('use'):

                        if row['use'] in ['true', '1', "t", "True", "TRUE", 1]:
                            row['use'] = True
                        else:
                            row['use'] = False
                    else:
                        row['use'] = True

                    meta_list.append(row)

        elif source == "shp":
            # read data from selected shp file
            vlayer = QgsVectorLayer(self.meta_path, "tmp", "ogr")

            for feat in vlayer.getFeatures():

                point = feat.geometry().asPoint()

                statflag = feat.attribute('statflag')
                freq = feat.attribute('freq')

                new_point = transform.transform(QgsPoint(float(point.x()), float(point.y())))

                tmp = {
                    'name': feat.attribute('name'),
                    'desc': feat.attribute('desc'),
                    'prop': feat.attribute('prop'),
                    'unit': feat.attribute('unit'),
                    'lat': new_point[1],
                    'lon': new_point[0],
                    'altitude': float(feat.attribute('altitude')),
                    'freq': freq if str(freq) != 'NULL' else None,
                    'topscreen': float(feat.attribute('topscreen')),
                    'bottomscreen': float(feat.attribute('btmscreen')),
                    'statflag': statflag if str(statflag) != 'NULL' else None
                }

                if feat.attribute('use') in ['false', '0', 'f', 'False', 0, 'FALSE']:
                    tmp['use'] = False
                else:
                    tmp['use'] = True

                meta_list.append(tmp)

        else:
            print "unknown source"

        return meta_list

    def csv_preview_area(self, file_path):
        """
            Load a raw preview of data
        """
        with open(file_path) as myfile:
            lines = sum(1 for _ in myfile)

            lines = lines if lines < 5 else 5

        # read first x line from the file
        with open(file_path) as myfile:
            head = [next(myfile) for _ in xrange(lines)]

        self.gui.csvPreviewArea.clear()
        for line in head:
            self.gui.csvPreviewArea.appendPlainText(line.replace("\n", "").replace("\r", ""))  # remove all cr

    def load_preview(self):
        """
            Load preview
        """

        if self.data_path == '':
            self.gui.popup_error_message(self.gui.tr("Please select a valid data folder"))
            return

        tmp_sensor = sensor.Sensor("", "", "")
        try:
            tmp_sensor = self.__load_sensor_data(tmp_sensor, self.file_path)
        except Exception as e:
            print e
            return

        if not tmp_sensor:
            self.gui.popup_error_message(self.gui.tr("Please check input values"))
            return

        tmp = list(tmp_sensor.ts.head(3).itertuples())
        self.gui.tableCsvPreview.setRowCount(0)

        for var in tmp:

            row_count = self.gui.tableCsvPreview.rowCount()
            self.gui.tableCsvPreview.insertRow(row_count)

            for i in range(len(var)):
                self.gui.tableCsvPreview.setItem(row_count, i, QTableWidgetItem(str(var[i])))

    def __load_sensor_data(self, oat_sensor, path):
        """
                Load data from csv file, read params from gui
            Args:
                oat_sensor (Sensor): sensor to load data
            Returns:
                sensor (Sensor): sensor with data
        """

        if path == '':
            self.gui.popup_error_message(self.gui.tr('Please select a valid csv file'))
            raise Exception('Please select a valid csv file')

        skip_rows = self.gui.skipRows.value()
        date_column = self.gui.dateColumns.text()

        if date_column == "":
            self.gui.popup_error_message(self.gui.tr("Please define a date column!!!"))
            raise Exception('please define a date column')

        date_column = map(int, date_column.split(','))

        data_column = self.gui.dataColumn.value()
        day_first = self.gui.dayFirstBox.isChecked()

        date_text = self.gui.dateFormat.currentText()
        date_index = self.gui.dateFormat.findText(date_text)

        if date_index == -1:
            date_format = str(date_text)
            if '%' not in date_text:
                tmp = date_text.replace('2015', '%Y').replace('15', '%y').replace('31', '%d').replace('12', '%m')
                date_format = tmp.replace('23', "%H").replace('59', '%M').replace('58', '%S')
        else:
            date_format = self.gui.dateFormat.itemData(date_index)

        # date_format = self.dateFormat.currentText()
        qi_col = self.gui.qiColumn.value()

        no_data_value = self.gui.noData.text()
        if no_data_value != '':
            no_data_value = map(float, no_data_value.split(','))
        else:
            no_data_value = []

        comment = self.gui.comment.text()

        if comment == "":
            comment = '#'

        sep = self.gui.sepGroup.checkedButton().text()

        if sep == "Semicolon":
            separator = ';'
        elif sep == "Tab":
            separator = "\t*"
        elif sep == "Space":
            separator = "\s*"
        else:
            separator = ','

        if date_format == "":
            date_format = None

        # load data from CSV
        try:
            oat_sensor.ts_from_csv(path, valuecol=data_column, qualitycol=qi_col, sep=separator, skiprows=skip_rows,
                                   strftime=date_format, dayfirst=day_first, timecol=date_column, comment=comment,
                                   na_values=no_data_value)
        except Exception as e:
            print e

            if str(e) == '1':
                self.gui.popup_error_message(self.gui.tr("An error occured: \n Wrong separator"))
            else:
                self.gui.popup_error_message(self.gui.tr("An error occurred:\n {}").format(e))
            raise Exception("An error occurred, please check input values")

        return oat_sensor
