# -*- coding: utf-8 -*-
# ==============================================================================
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
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import pandas as pd
import numpy as np
import os


class Model():
    """ Class to handle a MODFLOW model """

    def __init__(self, name, start, model_type='modflow', length_unit='m', time_unit='sec', working_dir=None, stress_periods=[]):
        """Initialize the model object

        Arguments:
            name (list): the name of the model
            start (str): the model simulation start datetime
            sensors (str): the observed property
            model_type (str): the type of model [allowed values: modflow, seewat]
            length_unit (str): lenth unit of measure
            time_unit (str): time unit of measure
            working_dir (str): path of the working directory
            stress_periods (list): list of oat.model.StressPeriod objects

        """
        allowed_types = ['modflow', 'seewat']
        if not model_type in allowed_types:
            raise ValueError("Allowed types are: %s" % allowed_types)

        allowed_length_units = ['m', 'cm', 'ft', 'undefined']
        if not length_unit in allowed_length_units:
            raise ValueError("Allowed units are: %s" % allowed_length_units)

        allowed_time_units = ['sec', 'min', 'hour', 'day', 'month', 'year', 'undefined']
        if not time_unit in allowed_time_units:
            raise ValueError("Allowed units are: %s" % allowed_time_units)

        if isinstance(start, pd.tslib.Timestamp):
            self.start_datetime = start
        else:
            self.start_datetime = pd.Timestamp(start)

        self.name = name
        self.type = model_type
        self.length_unit = length_unit
        self.time_unit = time_unit
        self.working_dir = working_dir
        if isinstance(start, pd.tslib.Timestamp):
            self.start_datetime = start
        else:
            self.start_datetime = pd.Timestamp(start)
        self.stress_periods = []

    @classmethod
    def from_sqlite(cls, working_dir, model_name):
        """Create the Model class from sqlite

        Args:
            working_dir (str): path of the working directory
            model_name (list): the model name
        """
        try:
            from pyspatialite import dbapi2 as db
        except ImportError:
            raise ImportError('<pyspatialite> package not installed')

        source = os.path.join(working_dir, "%s.sqlite" % model_name)
        con = db.connect(source)
        con.enable_load_extension(True)
        cur = con.cursor()

        modeltableName = 'modeltable_' + model_name

        sql = "SELECT name, type, length_unit, time_unit, working_dir FROM ? WHERE name=?"
        res = cur.execute(sql, (modeltableName, model_name)).fetchone()
        con.close()
        return cls(name=res[0], start='1970-01-01T12:00:00Z', model_type=res[1], length_unit=res[2], time_unit=res[3], working_dir=res[4])

        #ADD STRESS PERIODS FROM SQLITE

    def to_UCODE_data_in(self, filename):
        """write UCODE Observation_Data Input Block

        """

        #calculate nrows
        nrows = 0
        for s in self.series:
            nrows += s.ts.index.size

        f = open(filename, 'w')
        f.write('BEGIN OBSERVATION_DATA TABLE')
        f.write('NROW=%s NCOL=6 COLUMNLABELS' % nrows)
        f.write('ObsName GroupName ObsValue Statistic StatFlag PlotSymbol')
        for s in self.series:
            name = s.name[:10] if len(s.name) > 10 else s.name
            for i in range(1, len(s.ts.index)):
                oname = '%s%s' % (name, name)
                f.write(
                        '{:20s} {:10s} {:10s} {:1s} {:5s} {:1s}'.format(
                            '%s%s' % (name,)
                            )
                )
        f.write('')
        f.write('')
        f.write('')
        f.write('')
        f.write('END OBSERVATION_DATA')
        """
        BEGIN OBSERVATION_DATA TABLE
        #StatFlag designation here overrides value from the
        #Observation_Groups input block
        NROW=8 NCOL=6 COLUMNLABELS
        obsname obsvalue statistic statflag equation
        GROUPNAME

        BEGIN Observation_Data Table
          NROW=2451 NCOL=6 COLUMNLABELS
          ObsName GroupName ObsValue Statistic StatFlag PlotSymbol

        f.write('hello\n')
        """
        f.close()



#self.cmbState.addItems(['Steady State', 'Transient'])

class StressPeriod():
    """ Class to handle stress periods """

    def __init__(self, period, length, steps, multiplier, state, startdate = None, sensors=[]):
        """
        Stress period initialization

        Arguments:
            period (str): the name of the model
            length (str): the model simulation start datetime
            steps (str): the observed property
            multiplier (str): the type of model [allowed values: modflow, seewat]
            state (str): lenth unit of measure
            startdate (str): time unit of measure
            sensors (str): path of the working directory

        """

        allowed_state = ['Steady State', 'Transient']
        if not state in allowed_state:
            raise ValueError("allowed values are: %s" % ",".join(allowed_state))

        self.period = int(period)
        self.length = float(length)
        self.time_steps = int(steps)
        self.multiplier = float(multiplier)
        self.time_unit = 'sec'
        self.state = state
        if isinstance(startdate, pd.tslib.Timestamp):
            self.start_datetime = startdate
        else:
            self.start_datetime = pd.Timestamp(startdate)

        frequency = '%s%s' % ((self.length / self.time_steps), self.time_unit)
        self.range = pd.date_range(startdate, periods=self.time_steps, freq=frequency)

        self.sensors = []

    def add_sensor(self, sensorObj):
        """ """
        pass
        #sensorObj.ts


