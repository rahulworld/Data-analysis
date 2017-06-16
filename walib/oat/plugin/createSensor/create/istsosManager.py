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
from PyQt4.QtCore import QDateTime
from PyQt4.QtGui import QMessageBox
import requests


from ..sosServer_dialog import SosServer
from oatlib import sensor


class IstsosManager(object):
    """
        Manage istsos request
    """
    def __init__(self, gui):
        self.gui = gui
        self.sos_params = None
        self.__init_gui()

        self.procedure_list = None

    def __init_gui(self):
        """
            SOS stackedFrame init
        """
        self.gui.sosAggBox.stateChanged.connect(self.toggle_date)
        self.gui.sosServerConnect.clicked.connect(self.require_procedure_list)
        self.gui.sosServerEdit.clicked.connect(self.edit_server)
        self.gui.sosServerNew.clicked.connect(self.new_server)
        self.gui.sosServerDelete.clicked.connect(self.delete_server)

        self.gui.sosTimeFrame.setEnabled(False)

        self.procedure_list = None

        self.update_server_list()

    def require_procedure_list(self):
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

        res = self.gui.db.execute_query(query, params)[0]

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
            url = "{}/wa/istsos/services/{}/procedures/operations/getlist".format(self.sos_params['url'],
                                                                                  self.sos_params['service'])
            req = requests.get(url, auth=auth)
        except requests.exceptions.ConnectionError as e:
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
            self.procedure_list = req.json()['data']
        except Exception as e:
            print e
            return

        self.gui.sosProcedure.clear()
        self.gui.sosProcedure.addItem('')

        for proc in self.procedure_list:
            self.gui.sosProcedure.addItem(proc['name'])

        QMessageBox.about(self.gui, self.gui.tr('istSOS connection'), self.gui.tr('Successfully connected to server'))

        self.gui.sosProcedure.currentIndexChanged.connect(self.require_op)

    def require_op(self):
        """
            Require observed properties for selected procedure
        """
        myproc = None

        name = self.gui.sosProcedure.currentText()

        for proc in self.procedure_list:
            if proc['name'] == name:
                myproc = proc
                break

        if not myproc:
            print "Procedure not found...."
            return

        self.gui.sosSensorOp.clear()
        self.gui.sosSensorOp.addItem('')

        for obs in myproc['observedproperties']:
            self.gui.sosSensorOp.addItem(obs['name'].split('-')[-1])

        # set begin and end position
        samplig_time = myproc['samplingTime']

        begin_text = QDateTime.fromString(samplig_time['beginposition'].replace("T", " ")[:-5], "yyyy-MM-dd hh:mm:ss")

        end_text = QDateTime.fromString(samplig_time['endposition'].replace("T", " ")[:-5], "yyyy-MM-dd hh:mm:ss")

        # set time limit
        self.gui.sosTimeEnd.setMaximumDateTime(end_text)
        self.gui.sosTimeBegin.setMinimumDateTime(begin_text)

        self.gui.sosTimeBegin.setDateTime(begin_text)
        self.gui.sosTimeEnd.setDateTime(end_text)

    def load_istsos_data(self):
        """
            Load data from istSOS server

        Returns:
            True if success
        """
        basic_auth = None
        func = None
        agg_int = None
        interval = None

        if not self.sos_params:
            self.gui.popup_error_message(self.gui.tr("please select a istSOS configuration"))
            return False

        if self.sos_params['user']:
            basic_auth = (self.sos_params['user'], self.sos_params['passwd'])

        op = self.gui.sosSensorOp.currentText().replace("-", ":")  # not the best solution

        if op == 'river:discharge':
            op = 'discharge'

        proc = self.gui.sosProcedure.currentText()

        if proc == '' or op == '':
            self.gui.popup_error_message(self.gui.tr("Missing data, please select a procedure and an obseved property"))
            return False

        if self.gui.sosAggFunc.currentText() != '':
            func = self.gui.sosAggFunc.currentText()
            agg_int = self.gui.sosAggInterval.text()

        if self.gui.sosAggBox.isChecked():
            timezone = self.gui.sosTimezone.value()
            self.tz = timezone

            if timezone >= 0:
                timez = "+" + "%02d" % (timezone)
            else:
                timez = "-" + "%02d" % (abs(timezone))

            interval = list()
            interval.append(self.gui.sosTimeBegin.text().replace(" ", "T") + timez + ":00")
            interval.append(self.gui.sosTimeEnd.text().replace(" ", "T") + timez + ":00")

        try:

            self.gui.oat = sensor.Sensor.from_istsos(service=self.sos_params['url'] + '/' + self.sos_params['service'],
                                                     procedure=proc, observed_property=op, basic_auth=basic_auth)

            self.gui.oat.use = self.gui.sensorUse.isChecked()
            self.gui.oat.statflag = self.gui.sensorStat.currentText()
            self.gui.oat.topscreen = self.gui.sensorTop.value()
            self.gui.oat.bottomscreen = self.gui.sensorBottom.value()

        except Exception as e:
            print e
            self.gui.popup_error_message(self.gui.tr("An error occur: {}").format(e))
            return False

        if not self.gui.oat:
            self.gui.popup_error_message(self.gui.tr("Problem loading sensor, please check input value"))
            return False

        self.gui.fill_from_oat()

        if self.gui.sosAggBox.isChecked():
            self.gui.oat.data_availability = interval

        freq = self.gui.sosSensorFreq.currentText()

        if freq == '':
            freq = None

        try:
            # load data from SOS
            # TODO: move to a background thread?
            self.gui.oat.ts_from_istsos(service=self.sos_params['url'] + '/' + self.sos_params['service'],
                                        procedure=proc, observed_property=op, basic_auth=basic_auth,
                                        event_time="/".join(self.gui.oat.data_availability), aggregate_function=func,
                                        aggregate_interval=agg_int, freq=freq)
        except Exception as e:
            print e
            self.gui.popup_error_message(self.gui.tr("An error occur: {}").format(e))
            return False

        return True

    def toggle_date(self, value):
        """
            Toggle sosTimeFrame for data request

        Args:
            value (int): value
        """
        if value == 0:
            self.gui.sosTimeFrame.setEnabled(False)
        else:
            self.gui.sosTimeFrame.setEnabled(True)

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

        self.gui.db.execute_query(query, params)

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
            res = self.gui.db.execute_query(query)
        except Exception as e:
            print e
            return

        self.gui.sosServer.clear()
        self.gui.sosServer.addItem('', '')

        for elem in res:
            self.gui.sosServer.addItem(elem[0], elem[1])
