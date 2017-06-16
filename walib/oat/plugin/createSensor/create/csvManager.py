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
from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import QTableWidgetItem, QFileDialog

from oatlib import sensor


class CsvManager(QObject):
    """
        This class contains all method to manipulate csv data
    """
    exception = pyqtSignal(Exception)
    popupMessage = pyqtSignal(str)

    def __init__(self, gui):
        self.gui = gui
        self.init_data_format()
        self.tmp_sensor = None

    def init_gui(self):

        self.gui.addCsvFile.clicked.connect(self.open_csv_finder)
        self.gui.csvPreview.clicked.connect(self.load_preview)

    def init_data_format(self):
        """
            Add some default choise to dateFormat QComboBox
        """

        self.gui.dateFormat.addItem("", "")
        self.gui.dateFormat.addItem("2015-12-31", "%Y-%m-%d")
        self.gui.dateFormat.addItem("31-12-2015", "%d-%m-%Y")
        self.gui.dateFormat.addItem("12-31-2015", "%m-%d-%Y")

        self.gui.dateFormat.addItem("2015/12/31", "%Y/%m/%d")
        self.gui.dateFormat.addItem("31/12/2015", "%d/%m/%Y")
        self.gui.dateFormat.addItem("12/31/2015", "%m/%d/%Y")

        self.gui.dateFormat.addItem("2015-12-31 23:59:58", "%Y-%m-%d %H:%M:%S")

    def read_data_from_csv(self):
        """
            Method to read data from csv file
        """
        # load data from CSV
        self.gui.oat = self.__load_sensor_data(self.gui.oat)

    def preview_data(self, filename):
        """
            Preview data read first 5 row from file and display inside a textbox
            Args:
                filename (str): path to file to open
        """

        with open(filename) as myfile:
            lines = sum(1 for _ in myfile)

            if lines > 5:
                lines = 5

        # read first x line from the file
        with open(filename) as myfile:
            head = [next(myfile) for x in xrange(lines)]

        self.gui.csvRawPreview.clear()
        for line in head:
            self.gui.csvRawPreview.appendPlainText(line.replace("\n", "").replace("\r", ""))

    def load_preview(self):
        """
            Load preview
        """
        tmp_sensor = self.__load_sensor_data(sensor.Sensor("", "", ""))

        if not tmp_sensor:
            return

        tmp = list(tmp_sensor.ts.head(3).itertuples())

        self.gui.tableCsvPreview.setRowCount(0)

        for var in tmp:

            row_count = self.gui.tableCsvPreview.rowCount()
            self.gui.tableCsvPreview.insertRow(row_count)

            for i in range(len(var)):
                self.gui.tableCsvPreview.setItem(row_count, i, QTableWidgetItem(str(var[i])))

    def open_csv_finder(self):
        """
            Open a file finder
        """
        dialog = QFileDialog()
        filename = dialog.getOpenFileNameAndFilter(self.gui, self.gui.tr("Select input file "), "",
                                                   "CSV (*.csv);; plain (*.txt)")

        if filename[0] == '':
            return

        self.gui.filePath.setText(filename[0])

        self.preview_data(filename[0])

    def load_csv_data(self):
        """
            Load data from CSV file with specific configuration
        """
        if not self.gui.get_sensor_info():
            return False

        try:
            self.gui.oat = self.__load_sensor_data(self.gui.oat)

            if not self.gui.oat:
                return False

            return True
        except Exception as e:
            print e
            return False

    def __load_sensor_data(self, sensor):
        """
            Load data from csv file, read params from gui

        Args:
            sensor (sensor): sensor to load data

        Returns:
            sensor (sensor): sensor with data
        """
        # read csv params
        path = self.gui.filePath.text()

        if path == "":
            self.gui.popup_error_message(self.gui.tr("Please select a valid csv file"))
            return None

        skip_rows = self.gui.skipRows.value()
        date_column = self.gui.dateColumns.text()

        if date_column == "":
            self.gui.popup_error_message(self.gui.tr("Please define a date column!!!"))
            return None

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

        qi_col = self.gui.qiColumn.value()

        no_data_value = self.gui.noData.text()
        if no_data_value != '':
            no_data_value = map(float, no_data_value.split(','))
        else:
            no_data_value = []

        comment = self.gui.comment.text()

        if comment == "":
            comment = '#'

        sep = self.gui.buttonGroup_2.checkedButton().text()

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

        # load data fron CSV
        try:
            sensor.ts_from_csv(path, valuecol=data_column, qualitycol=qi_col, sep=separator, skiprows=skip_rows,
                               strftime=date_format,dayfirst=day_first, timecol=date_column, comment=comment,
                               na_values=no_data_value)
        except Exception as e:
            print e
            if str(e) == '1':
                self.gui.popup_error_message(self.gui.tr("An error occurred: \n Wrong separator"))
            else:
                self.gui.popup_error_message(self.gui.tr("An error occurred:\n {}").format(e))
            return None

        return sensor
