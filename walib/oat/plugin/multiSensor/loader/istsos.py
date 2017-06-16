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
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QTableWidgetItem

from oat.plugin.createSensor.sosServer_dialog import SosServer

from oat.oatlib import sensor

import requests
from oat.plugin import databaseManager


def move_procedure(from_table, to_table):
    """
        Move rocedure from a table to another
    """
    selected_row = from_table.selectionModel().selectedRows()

    for row in reversed(selected_row):
        index = row.row()
        procedure = from_table.item(index, 0).text()

        row_count = to_table.rowCount()
        to_table.insertRow(row_count)
        to_table.setItem(row_count, 0, QTableWidgetItem(procedure))

        from_table.removeRow(index)


def move_all_procedure(from_table, to_table):
    """
        Move all procedure from a table to another
    """
    row_number = from_table.rowCount()

    for index in reversed(range(0, row_number)):
        procedure = from_table.item(index, 0).text()

        row_count = to_table.rowCount()
        to_table.insertRow(row_count)
        to_table.setItem(row_count, 0, QTableWidgetItem(procedure))

        from_table.removeRow(index)


class IstsosManager(object):

    def __init__(self, gui):
        self.gui = gui

        self.db = databaseManager.DatabaseManager()

        self.op_list = None
        self.selected_op = None
        self.sos_params = {}

        self.manage_gui()

    def manage_gui(self):
        self.gui.sosServerConnect.clicked.connect(self.require_op_list)
        self.gui.sosServerEdit.clicked.connect(self.edit_server)
        self.gui.sosServerNew.clicked.connect(self.new_server)
        self.gui.sosServerDelete.clicked.connect(self.delete_server)

        self.gui.addButton.clicked.connect(self.add_procedure)
        self.gui.removeButton.clicked.connect(self.remove_procedure)

        self.gui.addAllButton.clicked.connect(self.add_all_procedure)
        self.gui.removeAllButton.clicked.connect(self.remove_all_procedure)

        self.update_server_list()

    def require_op_list(self):
        """
            Require procedure list when selecting a different sos server
        """

        tmp_index = self.gui.sosServer.currentIndex()

        if tmp_index == -1:
            return

        index = self.gui.sosServer.itemData(tmp_index)

        if index == '':
            return

        query = "SELECT url, user, passwd FROM server WHERE id=?"
        params = (index,)

        res = self.db.execute_query(query, params)[0]

        service = res[0].split('/')[-1]
        url = '/'.join(res[0].split('/')[:-1])

        self.sos_params = {
            'url': url,
            'service': service,
            'user': res[1],
            'passwd': res[2]
        }

        auth = None

        if self.sos_params['user']:
            auth = (self.sos_params['user'], self.sos_params['passwd'])

        try:
            url = "{}/wa/istsos/services/{}/observedproperties".format(self.sos_params['url'],
                                                                       self.sos_params['service'])
            req = requests.get(url, auth=auth)
        except requests.exceptions.ConnectionError as _:
            self.gui.popup_error_message(self.gui.tr("Problem with server, please check if server is online"))
            return
        except Exception as e:
            self.gui.popup_error_message(self.gui.tr("Unknown Error: {}").format(e))
            return

        if req.status_code != requests.codes.ok:
            print "Error : {}".format(req.status_code)
            req.raise_for_status()
            return

        try:
            self.op_list = req.json()['data']
        except Exception as e:
            print e
            return

        self.gui.sosOp.clear()
        self.gui.sosOp.addItem('')

        for proc in self.op_list:
            self.gui.sosOp.addItem(proc['name'])

        QMessageBox.about(self.gui, self.gui.tr('istSOS connection'), self.gui.tr('Successfully connected to server'))

        self.gui.sosOp.currentIndexChanged.connect(self.write_procedure)

    def write_procedure(self):
        """

        Returns
        -------

        """
        tmp_index = self.gui.sosOp.currentIndex()

        print tmp_index
        if tmp_index == -1:
            return

        index = self.gui.sosOp.itemText(tmp_index)

        self.selected_op = index

        for op in self.op_list:

            if op['name'] == index:
                procedures = op['procedures']

                self.gui.tableProcedure.setRowCount(0)
                self.gui.tableSelected.setRowCount(0)

                self.selected_op = op['definition']

                for proc in procedures:
                    row_count = self.gui.tableProcedure.rowCount()
                    self.gui.tableProcedure.insertRow(row_count)

                    self.gui.tableProcedure.setItem(row_count, 0, QTableWidgetItem(proc))

                break

    def add_all_procedure(self):
        move_all_procedure(self.gui.tableProcedure, self.gui.tableSelected)

    def remove_all_procedure(self):
        move_all_procedure(self.gui.tableSelected, self.gui.tableProcedure)

    def add_procedure(self):
        move_procedure(self.gui.tableProcedure, self.gui.tableSelected)

    def remove_procedure(self):
        move_procedure(self.gui.tableSelected, self.gui.tableProcedure)

    def load_multiple_sensors(self):
        """
            load selected procedure into freewat
        """

        row_number = self.gui.tableSelected.rowCount()

        # prepare requests params
        basic_auth = None
        if self.sos_params['user']:
            basic_auth = (self.sos_params['user'], self.sos_params['passwd'])

        url = "{}/{}".format(self.sos_params['url'], self.sos_params['service'])

        overwrite = self.gui.force.isChecked()
        error = list()

        if self.gui.sosAggFunc.currentText() != '':
            agg_func = self.gui.sosAggFunc.currentText()
            agg_int = self.gui.sosAggInterval.text()
        else:
            agg_func = None
            agg_int = None

        # cycle over selected sensors
        for row in range(0, row_number):

            procedure = self.gui.tableSelected.item(row, 0).text()

            try:
                # create oat_sensor
                tmp_sens = sensor.Sensor.from_istsos(service=url, procedure=procedure,
                                                     observed_property=self.selected_op, basic_auth=basic_auth)
            except Exception as e:
                error.append({'name': procedure, 'error': str(e)})
                continue

            try:
                # load timeseries data
                tmp_sens.ts_from_istsos(procedure=procedure, observed_property=self.selected_op, service=url,
                                        basic_auth=basic_auth, event_time="/".join(tmp_sens.data_availability),
                                        aggregate_function=agg_func, aggregate_interval=agg_int)
            except Exception as e:
                error.append({'name': procedure, 'error': str(e)})
                continue

            try:
                # save into db
                tmp_sens.save_to_sqlite(self.db.get_db_path(), procedure, overwrite=overwrite)
            except Exception as e:
                error.append({'name': procedure, 'error': str(e)})

        # notify user abount errors
        if len(error) != 0:
            message = self.gui.tr("The following sensors report errors:\n\n")

            for err in error:
                message += self.gui.tr("Sensor: {}\nError : {}\n\n").format(err['name'], err['error'])

            self.gui.popup_error_message(message)
        else:
            QMessageBox.about(self.gui, self.gui.tr("Upload done"), self.gui.tr("Sensors loaded"))
            self.clear_ui()

    def new_server(self):
        """
            Sos newServer button listener, open a new Dialog to create a new server configuration'
        """
        self.run_sos_gui()

    def edit_server(self):
        """
            Sos editServer button listener, aoen a new Dialog to edit selected server
        """
        selected = self.gui.sosServer.currentIndex()
        if selected != 0:
            index = self.gui.sosServer.itemData(selected)
            self.run_sos_gui(index)

    def delete_server(self):
        """
            delete selected server
        """
        selected = self.gui.sosServer.currentIndex()
        if selected == 0:
            return

        index = self.gui.sosServer.itemData(selected)

        query = "DELETE FROM server WHERE id=?"
        params = (index,)

        self.db.execute_query(query, params)

        self.update_server_list()

    def run_sos_gui(self, index=None):
        """
            Open sosServer Dialog, Disable current window
        Args:
            index (int): server id if edit
        """
        self.gui.setEnabled(False)
        sos = SosServer(index)

        # Open SOS configuration gui
        sos.show()
        sos.exec_()

        self.gui.setEnabled(True)
        self.update_server_list()

    def update_server_list(self):
        """
            Update sosServer ComboBox value
        """

        query = """SELECT name, id FROM server"""

        try:
            res = self.db.execute_query(query)
        except Exception as e:
            print e
            return

        self.gui.sosServer.clear()
        self.gui.sosServer.addItem('', '')

        for elem in res:
            self.gui.sosServer.addItem(elem[0], elem[1])

    def clear_ui(self):

        self.gui.tableProcedure.setRowCount(0)
        self.gui.tableSelected.setRowCount(0)
