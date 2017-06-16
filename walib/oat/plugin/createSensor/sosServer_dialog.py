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
from PyQt4 import uic
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDialog,QDialogButtonBox

import os

from .. import databaseManager
import config

FORM_CLASS, _ = uic.loadUiType(os.path.join(config.ui_path, 'sosServer.ui'))


class SosServer(QDialog, FORM_CLASS):
    """
        Class to manage the Server configuraton gui
    """

    def __init__(self, server_id=None):
        """
            Args:
                server_id (int): configuration id to update previus values
        """
        QDialog.__init__(self)
        self.server_id = server_id
        self.setupUi(self)
        self.db = None
        self.manage_gui()

    def manage_gui(self):
        self.db = databaseManager.DatabaseManager()
        self.useAuth.stateChanged.connect(self.toggle_auth)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save_listener)

        self.__check_table()

        if self.server_id:
            self.__fill_field()

    def closeEvent(self, event):
        self.db.close()

    def toggle_auth(self, value):
        """
            Toggle auth panel
        """
        if value == 0:
            self.frameAuth.setEnabled(False)
        else:
            self.frameAuth.setEnabled(True)

    def __fill_field(self):
        """
            fill field if edit configuration
        """
        query = "SELECT name, url, user, passwd FROM server WHERE id=?"
        params = (self.server_id,)

        result = self.db.execute_query(query, params)

        if len(result) == 0:
            print "Server not found"
            return

        res = result[0]

        self.serverName.setText(res[0])
        self.serverUrl.setText(res[1])

        if res[2]:
            print "auth params"
            self.useAuth.setCheckState(Qt.Checked)
            self.authUser.setText(res[2])
            self.authPassword.setText(res[3])

    def save_listener(self):
        """
            Save event listener
        """
        params = self.__get_value()

        if self.server_id:
            self.__edit_config(params)
        else:
            self.__save_config(params)

        self.close()

    def __save_config(self, server_params):
        """
            Save params
        """
        query = "INSERT INTO SERVER(name, url, user, passwd) values (?, ?, ?, ?); "

        params = (server_params['name'], server_params['url'], server_params['user'], server_params['password'],)

        try:
            self.db.execute_query(query, params)
        except Exception as e:
            print e

    def __edit_config(self, server_params):
        """
            Update server params
        """
        query = "UPDATE server SET name=?, url=?, user=?, passwd=? WHERE id=?"

        params = (server_params['name'], server_params['url'], server_params['user'], server_params['password'],
                  self.server_id,)

        try:
            self.db.execute_query(query, params)
        except Exception as e:
            print e

    def __get_value(self):

        params = dict()

        params['name'] = self.serverName.text()
        params['url'] = self.serverUrl.text().strip()

        if params['url'][-1] == '/':
            params['url'][-1] = params['url'][:-1]

        if self.useAuth.isChecked():
            params['user'] = self.authUser.text()
            params['password'] = self.authPassword.text()
        else:
            params['user'] = None
            params['password'] = None

        return params

    def __check_table(self):
        """
            Check if table exists, if not create a new one
        """
        query = """CREATE TABLE IF NOT EXISTS server (
                    id Integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    url TEXT NOT NULL,
                    user TEXT,
                    passwd TEXT
                    )
            """

        try:
            self.db.execute_query(query)
        except Exception as e:
            print e
