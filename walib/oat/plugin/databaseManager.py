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
from pyspatialite import dbapi2 as db
import freewat.freewat_utils as futils

import config
import os


def get_model_name():
    """
        get model name
    Returns
    -------

    """
    layers = futils.getVectorLayerNames()
    for layer in layers:
        if 'modeltable_' in layer:
            return layer.replace('modeltable_', '')


class DatabaseManager(object):
    """
        Class to manage db
    """

    def __init__(self, path=None):

        self.conn = None
        try:
            self.model_name = get_model_name()
            pathfile, _ = futils.getModelInfoByName(self.model_name)
            self.path = os.path.join(pathfile, self.model_name + ".sqlite")

            config.db_path = self.path
        except Exception as e:
            print e
            self.path = path
            pass

    def get_db_path(self):
        """
            return db path
        """
        return self.path

    def execute_query(self, query, params=None):
        """
            Execute query
        """
        self.conn = db.connect(self.path)

        try:
            if params:
                res = self.conn.execute(query, params).fetchall()
            else:
                res = self.conn.execute(query).fetchall()
        except Exception as e:
            print "Exception"
            raise e

        self.conn.commit()
        self.conn.close()
        self.conn = None

        return res

    def commit(self):
        if self.conn:
            self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
