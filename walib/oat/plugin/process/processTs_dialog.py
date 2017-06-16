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
from PyQt4.QtGui import QDialog, QFileDialog, QInputDialog, QMessageBox, QPlainTextEdit
from PyQt4 import uic
from qgis.core import QgsDataSourceURI, QgsMapLayerRegistry, QgsVectorLayer


from saveSensorList_dialog import SaveSensorList as SensList
from oat.plugin import databaseManager

from oat.oatlib import sensor
from oat.plugin.matplotWidget import MatplotWidget
import config
import imagePlayer
import processThread

import os
import copy

FORM_CLASS, _ = uic.loadUiType(os.path.join(config.ui_path, 'process.ui'))


class ProcessTs(QDialog, FORM_CLASS):

    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)

        self.result = {
            'type': None
        }

        self.db = databaseManager.DatabaseManager()
        self.history = None
        self.player = None
        self.base_thread = None
        self.oat = None
        self.thread = None

        self.manage_gui()

        self.__load_sensor_to_qgis()

    def manage_gui(self):
        """
            Connect all required signal
        """
        # Connect all signal
        self.loadButton.clicked.connect(self.load_sensor)
        self.executeFilter.clicked.connect(self.run_filter)
        self.saveFilter.clicked.connect(self.save_result)
        self.comboFilter.currentIndexChanged.connect(self.change_stacked_filter)
        self.sensorList.currentIndexChanged.connect(self.hide_filter)
        self.dvalueTime.stateChanged.connect(self.enable_dval_frame)
        self.qualityTime.stateChanged.connect(self.enable_quality_frame)
        self.qualityUseval.stateChanged.connect(self.enable_quality_val_frame)
        self.dvalueUse.stateChanged.connect(self.enable_value_val_frame)
        self.intTime.stateChanged.connect(self.enable_int_frame)
        self.statisticsTime.stateChanged.connect(self.enable_statistics_frame)

        self.hEvtTime.stateChanged.connect(self.h_evt_toggle)
        self.hIndexTime.stateChanged.connect(self.h_index_toggle)

        self.stackedWidget.setCurrentIndex(0)
        try:
            self.load_sensor_list()
        except Exception as _:
            QMessageBox.warning(self, "Warning", 'No sensor found!!!')
            return

    def h_evt_toggle(self, state):
        if state == Qt.Checked:
            self.hEvtPanel.setEnabled(True)
        else:
            self.hEvtPanel.setEnabled(False)

    def h_index_toggle(self, state):
        if state == Qt.Checked:
            self.hIndexPanel.setEnabled(True)
        else:
            self.hIndexPanel.setEnabled(False)

    def closeEvent(self, event):
        self.db.close()

    def load_sensor_list(self):
        """
            Add sensor name to ComboBox
        """
        query = "SELECT * FROM freewat_sensors"
        res = self.db.execute_query(query)

        self.clear_ui()

        self.db.close()

        self.sensorList.clear()
        self.compareSensor.clear()
        self.subSensor.clear()

        for elem in res:
            self.sensorList.addItem(elem[1])
            self.compareSensor.addItem(elem[1])
            self.subSensor.addItem(elem[1])

    def load_sensor(self):
        """
            Load selected sensor from DB
        """
        self.clear_ui()
        sensor_name = self.sensorList.currentText()

        self.oat = self.get_sensor_from_db(sensor_name)

        self.result = {
            'type': None
        }

        if self.oat.data_availability != [None, None]:

            begin_text = QDateTime.fromString(self.oat.data_availability[0].replace('T', ' ')[:-5],
                                              "yyyy-MM-dd hh:mm:ss")
            end_text = QDateTime.fromString(self.oat.data_availability[1].replace('T', ' ')[:-5], "yyyy-MM-dd hh:mm:ss")

            self.set_date(self.statisticsBegin, self.statisticsEnd, begin_text, end_text)
            self.set_date(self.intBegin, self.intEnd, begin_text, end_text)
            self.set_date(self.dvalueBegin, self.dvalueEnd, begin_text, end_text)
            self.set_date(self.qualityBegin, self.qualityEnd, begin_text, end_text)
            self.set_date(self.hIndexBegin, self.hIndexEnd, begin_text, end_text)
            self.set_date(self.hEvtBegin, self.hEvtEnd, begin_text, end_text)

        self.filterFrame.setEnabled(True)
        self.stackedWidget.setEnabled(True)
        self.draw_preview_chart()

    def set_date(self, widget_begin, widget_end, begin, end):
        """
            Set begin and end position to date widget
        """

        widget_begin.setDateTime(begin)
        widget_end.setDateTime(end)

    def get_sensor_from_db(self, name):
        """
            read sensor and sensor data from db
        """
        oat = sensor.Sensor.from_sqlite(config.db_path, name)

        oat.ts_from_sqlite(config.db_path)

        return oat

    def draw_preview_chart(self):
        """
            Draw preview chart
        """
        chart = MatplotWidget()
        chart.set_data(self.oat)

        self.clear_layout(self.dataPreview)
        self.dataPreview.addWidget(chart)

    def draw_chart(self, data=None, quality=False):
        """
            Draw chart
        """
        data = data if data else self.oat
        chart_big = MatplotWidget(toolbar=True)
        chart_big.set_data(data, True)

        self.clear_layout(self.resultFrame.layout())
        self.resultFrame.layout().addWidget(chart_big)

    def draw_multiple_chart(self, data, quality=False):
        """
            Draw multiple chart into same figure
        """
        chart_big = MatplotWidget(toolbar=True)
        chart_big.set_multiple_data(data, quality)

        self.clear_layout(self.resultFrame.layout())
        self.resultFrame.layout().addWidget(chart_big)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def change_stacked_filter(self, index):
        """
            Stacked comboBox listener
            load selected filter gui
        """
        self.clear_layout(self.resultFrame.layout())
        self.stackedWidget.setCurrentIndex(index)

        if self.result['type'] == 'sensor':
            self.oat = self.result['data']

        self.draw_preview_chart()

    def hide_filter(self):
        self.clear_layout(self.resultFrame.layout())
        self.clear_layout(self.dataPreview)

        self.historyBox.clear()

        self.filterFrame.setEnabled(False)

    def run_filter(self):
        """
            execute button listener, execute the selected filter
        """
        self.add_loading()

        sel_filter = self.comboFilter.currentText()
        self.base_thread = processThread.Thread()

        print sel_filter

        if sel_filter == "digital filter":
            self.thread = processThread.DigitalThread(self)
        elif sel_filter == "exceedance":
            self.thread = processThread.ExceedanceThread(self)
        elif sel_filter == "hydro events":
            self.thread = processThread.HydroEventsThread(self)
        elif sel_filter == "hydro indices":
            self.thread = processThread.HydroIndicesThread(self)
        elif sel_filter == "quality":
            self.thread = processThread.QualityStatThread(self)
        elif sel_filter == "resample":
            self.thread = processThread.ResampleThread(self)
        elif sel_filter == "data values":
            self.thread = processThread.DataValuesThread(self)
        elif sel_filter == "hydro separation":
            self.thread = processThread.HydroGraphSepThread(self)
        elif sel_filter == "integrate":
            self.thread = processThread.IntegrateThread(self)
        elif sel_filter == "compare":
            self.thread = processThread.CompareThread(self)
        elif sel_filter == "subtract":
            self.thread = processThread.SubtractThread(self)
        elif sel_filter == "fill":
            self.thread = processThread.FillThread(self)
        elif sel_filter == "statistics":
            self.thread = processThread.StatisticsThread(self)
        elif sel_filter == "hargreaves":
            self.thread = processThread.HargreavesEToThread(self)
        else:
            print "no method found"
            self.remove_loading()
            return

        # run processing thread on background
        self.thread.moveToThread(self.base_thread)
        self.thread.end.connect(self.print_result)
        self.thread.exception.connect(self.print_exception)
        self.thread.debug.connect(self.print_debug)
        self.base_thread.started.connect(self.thread.run)
        self.base_thread.start()

    def save_result(self):
        """
            Save elaboration
            overwrite previous sensor or create new one
        """

        res_type = self.result['type']

        flag = False

        if res_type == "sensor":
            self.oat = self.result['data']
            flag = self.save_sensor()
        elif res_type == "sensor list":
            self.save_sensor_list()
            return
        elif res_type == "dict":
            flag = self.save_dict()
        elif res_type == "dict list":
            flag = self.save_dict_list()
        else:
            print "Undef type"

        if not flag:
            return

        self.historyBox.clear()

        self.load_sensor_list()

    def save_sensor(self):
        """
            save single sensor,
            create a new one or overwrite existing one
        """
        if self.overFilter.isChecked():
            self.oat.save_to_sqlite(config.db_path, overwrite=True)
            return True
        else:
            new_sensor = copy.deepcopy(self.oat)

            new_name, ok = QInputDialog.getText(self, self.tr('Sensor name'), self.tr('Enter a new sensor name:'))

            new_sensor.name = new_name
            if not ok:
                return False
            try:
                new_sensor.save_to_sqlite(config.db_path)
            except IOError as _:
                QMessageBox.about(self, "Error", "Sensor name already exists...")
                return False
            return True

    def enable_dval_frame(self, value):

        if value == Qt.Checked:
            self.dvalueFrame.setEnabled(True)
        else:
            self.dvalueFrame.setEnabled(False)

    def enable_quality_frame(self, value):

        if value == Qt.Checked:
            self.qualityFrame.setEnabled(True)
        else:
            self.qualityFrame.setEnabled(False)

    def enable_int_frame(self, value):

        if value == Qt.Checked:
            self.intFrame.setEnabled(True)
        else:
            self.intFrame.setEnabled(False)

    def enable_quality_val_frame(self, value):

        if value == Qt.Checked:
            self.qualityValFrame.setEnabled(True)
        else:
            self.qualityValFrame.setEnabled(False)

    def enable_value_val_frame(self, value):

        if value == Qt.Checked:
            self.dvalueFrameVal.setEnabled(True)
        else:
            self.dvalueFrameVal.setEnabled(False)

    def enable_statistics_frame(self, value):

        if value == Qt.Checked:
            self.statisticsFrame.setEnabled(True)
        else:
            self.statisticsFrame.setEnabled(False)

    def save_sensor_list(self):
        """
            Save sensor list
            Open a dialog to save desired sensor
        """

        sensor_list = self.result['data']

        self.setEnabled(False)
        gui_sensor_list = SensList(sensor_list)

        gui_sensor_list.end.connect(self.sensor_list_listener)

        gui_sensor_list.show()
        gui_sensor_list.exec_()

    def sensor_list_listener(self, message):

        self.setEnabled(True)

        if message == "save" or message == "close":
            self.historyBox.clear()
            self.load_sensor_list()

    def save_dict(self):
        """
            Save dictionary to file
        """
        data = self.result['data']
        tmp = ""
        for key in data.keys():
            tmp += "{} {}\n".format(key, data[key])

        return self.save_to_file(tmp)

    def save_dict_list(self):
        """
            Save list of dict to file
        """
        data = self.result['data']

        tmp = ""
        for elem in data:
            for key in elem.keys():
                tmp += "{} : {}    ".format(key, elem[key])
            tmp += "\n"

        return self.save_to_file(tmp)

    def clear_ui(self):
        """
            Clear gui
        """
        self.clear_layout(self.resultFrame.layout())
        self.clear_layout(self.dataPreview)
        self.oat = None

    def save_to_file(self, message):
        """
            Save data elaboration to file
        """
        dialog = QFileDialog()

        filename = dialog.getSaveFileName(self, self.tr("Select output file"), "", "TXT (*.txt)")

        if filename == '' or filename[-1] == '/':
            return False

        with open(filename, "w") as save_file:
            save_file.write(message)

        return True

    def add_loading(self):
        """
            Add loading git when processing
        """
        self.clear_layout(self.resultFrame.layout())
        self.player = imagePlayer.ImagePlayerWidget(config.gif_path)

        self.resultFrame.layout().addWidget(self.player)

    def remove_loading(self):
        """
            remove loading gui after processing end or exception
        """
        self.player.close()
        self.clear_layout(self.resultFrame.layout())

####################################
# Filter
####################################

    def print_result(self, result, history):
        """
            Print processing result
        """
        self.result = result
        self.history = history

        message = "Filter " + self.history['process'] + "    params: "
        for param in self.history['params'].keys():
            message += " " + param + " : " + str(self.history['params'][param]) + " |"

        self.historyBox.appendPlainText(message)

        if result['type'] == "sensor":
            self.draw_chart(self.result['data'])

        elif result['type'] == "sensor list":
            self.draw_multiple_chart(self.result['data'])

        elif result['type'] == "dict list":
            field = QPlainTextEdit()
            field.setReadOnly(True)
            for elem in self.result['data']:
                tmp = ""
                for key in elem.keys():
                    tmp += key + " : " + str(elem[key]) + " "
                field.appendPlainText(tmp)

            self.clear_layout(self.resultFrame.layout())
            self.resultFrame.layout().addWidget(field)

        elif result['type'] == "dict":
            field = QPlainTextEdit()
            field.setReadOnly(True)
            data = self.result['data']
            for key in data.keys():
                field.appendPlainText(key + " : " + str(data[key]))

            self.clear_layout(self.resultFrame.layout())
            self.resultFrame.layout().addWidget(field)
        else:
            print "undefined result"

        self.base_thread.quit()

    def print_exception(self, e):
        """
            Display a dialog with exception
        """
        self.remove_loading()

        txt = self.tr("Exception occurred: \n {}").format(e)
        QMessageBox.warning(self, self.tr("Error"), txt)

        self.base_thread.quit()

    def print_debug(self, message):
        """
            Print debug message
        """
        print message

    def __load_sensor_to_qgis(self):
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