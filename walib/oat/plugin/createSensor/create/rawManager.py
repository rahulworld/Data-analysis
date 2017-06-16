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
from PyQt4.QtGui import QTableWidgetItem
from PyQt4.QtCore import QDateTime

import isodate
import numpy as np


class RawManager(object):
    """
        Class to manage raw data
    """
    def __init__(self, gui):
        self.gui = gui
        self.__init_gui()

    def __init_gui(self):
        """
        """
        self.gui.rawTable.setColumnWidth(0, 160)
        self.gui.rawTable.setColumnWidth(1, 90)
        self.gui.rawTable.setColumnWidth(2, 90)

        self.gui.deleteRaw.clicked.connect(self.delete_row)
        self.gui.addNewRaw.clicked.connect(self.add_new_row)
        self.gui.clearRaw.clicked.connect(self.delete_all_row)
        self.gui.rawEditData.clicked.connect(self.return_to_edit)

        values = [
            {'show': '', 'value': ''},
            {'show': '5Min', 'value': 'PT5M'},
            {'show': '10Min', 'value': 'PT10M'},
            {'show': '20Min', 'value': 'PT20M'},
            {'show': '30Min', 'value': 'PT30M'},
            {'show': '1Hour', 'value': 'PT1H'},
            {'show': '2Hour', 'value': 'PT2H'},
            {'show': '6Hour', 'value': 'PT6H'},
            {'show': '12Hour', 'value': 'PT12H'},
            {'show': '1Day', 'value': 'PT24H'}
        ]

        for val in values:
            self.gui.comboFreqRaw.addItem(val['show'], val['value'])

    def return_to_edit(self):
        self.gui.stackedPreview.setCurrentIndex(2)
        self.gui.stackedWidget.setCurrentIndex(2)

    def add_new_row(self):
        """
            Add a new row to the table
        """

        row_count = self.gui.rawTable.rowCount()

        frequency = self.gui.comboFreqRaw.itemData(self.gui.comboFreqRaw.currentIndex())

        if frequency == '':
            self.gui.rawTable.insertRow(row_count)
            self.gui.rawTable.setItem(row_count, 0, QTableWidgetItem(''))
            return

        if row_count != 0:
            # read last date from table
            last_pos = self.gui.rawTable.item(row_count - 1, 0)
            last_date = QDateTime.fromString(last_pos.text(), "yyyy-MM-dd hh:mm:ss")
            seconds = isodate.parse_duration(frequency).total_seconds()
            begin_pos = last_date.addSecs(seconds)
        else:
            last_date = self.gui.rawBeginPos.dateTime()
            begin_pos = last_date

        if begin_pos > self.gui.rawEndPos.dateTime():
            return

        self.gui.rawTable.insertRow(row_count)
        begin_str = begin_pos.toString("yyyy-MM-dd hh:mm:ss")
        self.gui.rawTable.setItem(row_count, 0, QTableWidgetItem(begin_str))
        self.gui.rawTable.setItem(row_count, 1, QTableWidgetItem('0'))
        self.gui.rawTable.setItem(row_count, 2, QTableWidgetItem('100'))

    def delete_row(self):
        """
            Delete selected row from table
        """
        test = self.gui.rawTable.selectionModel()

        rows = test.selectedRows()

        for row in reversed(rows):
            self.gui.rawTable.removeRow(row.row())

    def delete_all_row(self):
        """
            Delete all raw from table
        """
        rows = self.gui.rawTable.rowCount()
        for row in reversed(range(0, rows)):
            self.gui.rawTable.removeRow(row)

    def load_raw_data(self):
        """
            Read raw data from table
        """
        if not self.gui.get_sensor_info():
                return False

        table = self.gui.rawTable
        row_number = table.rowCount()

        if row_number < 1:
            self.gui.popup_error_message(self.gui.tr("Please define at least 1 measure"))
            return False

        data = {
            'time': [],
            'data': [],
            'quality': []
        }

        tz = self.gui.tzRaw.value()

        self.gui.oat.tz = tz

        if tz >= 0:
            timezone = "+" + "%02d" % (tz)
        else:
            timezone = "-" + "%02d" % (abs(tz))

        timezone += ":00"
        begin_pos = None
        end_pos = None

        for i in range(0, row_number):

            try:
                date = np.datetime64(table.item(i, 0).text() + timezone)
            except:
                self.gui.popup_error_message(self.gui.tr("Please define a correct date"))
                return False

            value = self.__get_value(table.item(i, 1))
            qi = self.__get_value(table.item(i, 2))

            if not qi:
                qi = 0

            if i == 0:
                begin_pos = table.item(i, 0).text() + timezone
            if i == (row_number - 1):
                end_pos = table.item(i, 0).text() + timezone

            data['time'].append(date)
            data['data'].append(value)
            data['quality'].append(qi)

        self.gui.oat.data_availability = [begin_pos.replace(" ", "T"), end_pos.replace(" ", "T")]

        try:
            self.gui.oat.ts_from_dict(data)
        except Exception as e:
            self.gui.popup_error_message(self.gui.tr("Error occur: \n {}").format(e))
            return False
        return True

    def __get_value(self, element):
        """
            return value, if wrong or not available return None
        """
        try:
            return float(element.text())
        except ValueError:
            return None
        except AttributeError:
            return None