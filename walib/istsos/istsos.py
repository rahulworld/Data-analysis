# -*- coding: utf-8 -*-
# =============================================================================
#
# Authors: Massimiliano Cannata, Milan Antonovic
#
# Copyright (c) 2016 IST-SUPSI (www.supsi.ch/ist)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#
# =============================================================================
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

from walib import resource, utils, databaseManager, configManager
import sys
import os
import xml.etree.ElementTree as ET
import urllib2
from walib.oat.oatlib import method

import pandas as pd
import numpy as np
import json


try:
    from oatlib import oat_algorithms as oa
except:
    import oat_algorithms as oa



result1 = {
            "type": None,
            "data": None
            }


class waIstsos(resource.waResourceAdmin):
    def __init__(self, waEnviron):
        resource.waResourceAdmin.__init__(self, waEnviron)
        pass

class waStatus(waIstsos):
    """
    Class to execute /istsos/operations/serverstatus
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)
        pass

    def executeGet(self):
        """
        Execute GET request investigating set-up services

        @note: This method creates a C{self.data} object in the form of a
        list of dictionaries as below:

        >>> template = {
                "service" : None,
                "offerings" : None,
                "procedures" : None,
                "observedProperties" : None,
                "featuresOfInterest" : None,
                "getCapabilities" : None,
                "describeSensor" : None,
                "getObservations" : None,
                "registerSensor" : None,
                "insertObservation" : None,
                "getFeatureOfInterest" : None,
                "availability" : "up"
            }
        """
        services = utils.getServiceList(
            self.waconf.paths["services"],
            listonly=True)

        if self.user and not self.user.isAdmin():
            servicesAllowed = []
            for item in services:
                if self.user.allowedService(item):
                    servicesAllowed.append(item)
            services = servicesAllowed

        data = []
        for service in services:
            srv = {}
            srv["service"] = service

            # get service configuration
            defaultcfgpath = os.path.join(
                self.waconf.paths["services"],
                "default.cfg")

            servicecfgpath = "%s.cfg" % os.path.join(
                self.waconf.paths["services"],
                service, service)

            config = configManager.waServiceConfig(
                defaultcfgpath, servicecfgpath)

            # test if service is active (check answer to GetCapabilities)
            if config.serviceurl["default"] is True:
                urlget = config.serviceurl["url"] + "/" + service
            else:
                urlget = config.serviceurl["url"]

            request = ("?request=getCapabilities&"
                       "section=serviceidentification&service=SOS")

            srv["availability"] = utils.verifyxmlservice(
                urlget+request, self.waEnviron)

            # test if connection is valid
            connection = config.get("connection")

            try:
                servicedb = databaseManager.PgDB(
                    connection['user'],
                    connection['password'],
                    connection['dbname'],
                    connection['host'],
                    connection['port']
                )
                srv["database"] = "active"

            except:
                srv["database"] = "not connectable"
                srv["offerings"] = None
                srv["procedures"] = None
                srv["observedProperties"] = None
                srv["featuresOfInterest"] = None

            try:
                #count offerings
                srv["offerings"] = len(
                    utils.getOfferingNamesList(servicedb, service))
            except:
                srv["offerings"] = None

            try:
                #count procedures
                srv["procedures"] = len(
                    utils.getProcedureNamesList(
                        servicedb, service, offering=None))
            except:
                srv["procedures"] = None

            try:
                #count observed properties
                srv["observedProperties"] = len(
                    utils.getObsPropNamesList(
                        servicedb, service, offering=None))
            except:
                srv["observedProperties"] = None

            try:
                #count features of interest
                srv["featuresOfInterest"] = len(
                    utils.getFoiNamesList(servicedb, service, offering=None))
            except:
                srv["featuresOfInterest"] = None

            #get available requests
            requests_ON = config.parameters["requests"].split(",")
            for operation in [
                    "getcapabilities", "describesensor", "getobservation",
                    "getfeatureofinterest", "insertobservation",
                    "registersensor"]:

                if operation in requests_ON:
                    srv[operation] = True
                else:
                    srv[operation] = False
            data.append(srv)

        self.setData(data)
        self.setMessage("Serverstatus request successfully executed")


class waLog(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)
        pass


class waAbout(waIstsos):

    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executeGet(self):
        from istsoslib import sos_version
        data = {}
        data["istsos_version"] = str(sos_version.version)
        data["latest_istsos_version"] = ""
        data["latest_istsos_changelog"] = ""
        data["download_url"] = "https://sourceforge.net/projects/istsos"
        data["istsos_message"] = "updates not found"
        data["istsos_update"] = False
        self.setData(data)
        self.setMessage("istSOS \"About\" information successfully retrived")

class Resample1():
    """ Resample time serie frequency"""
    def __init__(self, freq='1H', how=None, fill=None, limit=None, how_quality=None):
        """ Initialize

        Args:
            freq (str): Offset Aliases sting (A=year,M=month,W=week,D=day,H=hour,T=minute,S=second; e.g.: 1H10T)
            how (str): sampling method ('mean','max','min',first','last','median','sum'), default is 'mean'
            fill (str): if not null it defines the method for filling no-data ('bfill'= backward fill or ‘ffill’=forward fill), default=None
            limit (int): if not null defines the maximum numbers of allowed consecutive no-data valuas to be filled
            how_quality (str): sampling method ('mean','max','min',first','last','median','sum') for observation quality index (default is like 'how')
        """
        self.freq = freq
        self.how = how
        self.fill = fill
        self.limit = limit
        self.how_quality = False

    def execute1(self, dataframe):
        """  Resample the data """
        
        # temp_oat = set()
        df = dataframe
        if self.how_quality:
            temp_oat = df.resample(rule=self.freq,how={'data': self.how, 'quality': self.how_quality},fill_method=self.fill, limit=self.limit)
        else:
            temp_oat = df.resample(rule=self.freq,how=self.how,fill_method=self.fill, limit=self.limit)

        return temp_oat
class Statistics():
    """ compute base statistics: count, min, max, mean, std, 25%, 50% 75 percentile"""

    def __init__(self, data=True, quality=False, tbounds=[None, None]):
        """ Initialize the class

        Args:
            data (bool): if True compute statistics of data (default is True)
            quality (bool): if True compute statistics of quality (default is False)
            tbounds (list): a list or tuple of string (iso856) with upper and lower time limits for statistic calculation.
                            bounds are closed bounds (t0 >= t <= t1)
        """
        self.quality = quality
        self.data = data
        self.tbounds = tbounds
    def execute(self, dataframe):
        """ Compute statistics """
        df=dataframe
        self.elab = {}

        if self.tbounds == [None, None] or self.tbounds is None:
            if self.data is True and self.quality is False:
                self.elab['data'] = df['data'].describe().to_dict()
            elif self.data is True and self.quality is True:
                self.elab['data'] = df.describe().to_dict()
            elif self.data is False and self.quality is True:
                self.elab['data'] = df['quality'].describe().to_dict()
            else:
                raise Exception("data and quality cannot be both False")
        else:
            if self.data is True and self.quality is False:
                self.elab['data'] = df.ix[self.tbounds[0]:self.tbounds[1]]['data'].describe().to_dict()
            elif self.data is True and self.quality is True:
                self.elab['data'] = df.ix[self.tbounds[0]:self.tbounds[1]].describe().to_dict()
            elif self.data is False and self.quality is True:
                self.elab['data'] = df.ix[self.tbounds[0]:self.tbounds[1]]['quality'].describe().to_dict()
            else:
                raise Exception("data and quality cannot be both False")
        # resdat = 'dict'
        resdata= self.elab
        return resdata

class Statisticsmethod(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    """
        Execute hydro graph separator
    """
    def executePost(self):
        import datetime
        from datetime import datetime
        import time
        index1=self.json['index1']
        values1=self.json['values1']
        qua=self.json['qual']

        data = self.json['dataSta']
        quality = self.json['quaSta']
        timeSta = self.json['timeSta']
        beginSta = self.json['beginSta']
        endSta = self.json['endSta']
        timezoneSta = self.json['timezoneSta']

        data1 = {'date': index1, 'data':values1, 'quality':qua}
        df = pd.DataFrame(data1,columns = ['date','data','quality'])
        df['date'] = pd.to_datetime(df['date'])
        df.index = df['date']
        del df['date']

        # data1 = {'date': ['2014-05-01 18:47:05.069722', '2014-05-01 18:47:05.119994', '2014-05-02 18:47:05.178768', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.280592', '2014-05-03 18:47:05.332662', '2014-05-03 18:47:05.385109', '2014-05-04 18:47:05.436523', '2014-05-04 18:47:05.486877'],'data': [34, 25, 26, 15, 15, 14, 26, 25, 62, 41],'quality': [200, 200, 200, 200, 200, 200, 200, 200, 200, 200]}
        # #data1 = {'date': index1, 'value':values1}
        # df = pd.DataFrame(data1,columns = ['date','data','quality'])
        # df['date'] = pd.to_datetime(df['date'])
        # df.index = df['date']
        # # df.data=df['value']
        # del df['date']
        tbounds = [None, None]
        if timeSta:
            timezone = ''
            if timezone >= 0:
                timez = "+" + "%02d:00" % (timezone)
            else:
                timez = "-" + "%02d:00" % (abs(timezone))
            begin_pos = '' + timez
            end_pos = '' + timez
            tbounds = [begin_pos, end_pos]

        stat=Statistics(data=data, quality=quality, tbounds=tbounds)
        st=stat.execute(df)
        self.setData(st['data'])
        self.setMessage("Statistics is successfully working")

class resamplingData(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        res = {}
        from pandas import read_csv
        from pandas import datetime
        from datetime import datetime
        import pandas as pd
        import time
        # import json
        freq=self.json['freq']
        how=self.json['sampling']
        fill=self.json['fill']
        limit=self.json['limit']
        quality=self.json['Quality']
        index1=self.json['index1']
        values1=self.json['values1']
        if freq=="":
            freq='1H'

        if fill == '':
            fill = None

        if limit == -1:
            limit = None

        # self.result = self.gui.oat.process(method.Resample(freq=freq, how=how, fill=fill, limit=limit,
        #                                                    how_quality=quality), detailedresult=True)
        # rea=method.Resample(freq=freq, how=how, fill=fill, limit=limit,how_quality=quality)
        # res['resulth']=rea.execute(self,df,detailedresult=True)
        # res=process(method.Resample(freq=freq, how=how, fill=fill,
        #     limit=limit, how_quality=quality), detailedresult=True)
        # aonao = pd.DataFrame({'AO':AO, 'NAO':NAO})
        # data1 = {'date': ['2014-05-01 18:47:05.069722', '2014-05-01 18:47:05.119994', '2014-05-02 18:47:05.178768', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.280592', '2014-05-03 18:47:05.332662', '2014-05-03 18:47:05.385109', '2014-05-04 18:47:05.436523', '2014-05-04 18:47:05.486877'],'value': [34, 25, 26, 15, 15, 14, 26, 25, 62, 41]}
        data1 = {'date': index1, 'value':values1}
        df = pd.DataFrame(data1,columns = ['date','value'])
        df['date'] = pd.to_datetime(df['date'])
        df.index = df['date']
        del df['date']

        resample=Resample1(freq=freq, how=how, fill=fill, limit=int(limit), how_quality=quality)
        resdata=resample.execute1(df)

        values = np.array(resdata['value'])
        times = resdata.index
        times_string =[]
        for i in times:
            times_string.append(str(i))

        def convert_to_timestamp(a):
            dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
            return int(time.mktime(dt.timetuple()))

        times_timestamp = map(convert_to_timestamp, times_string)

        data4 = []
        for i in range(len(times_string)):
            a = [times_timestamp[i], values[i]]
            data4.append(a)

        # dictionary = {'data': data4}

        self.setData(data4)
        self.setMessage("resampling is successfully working")

class Exceedance():
    """ """
    def __init__(self, values=None, perc=None, etu='days', under=False):
        """ Exceedance probability calculation

        Args:
            values (list): list of excedance values to calculate the excedance probability
            perc (list): list of exceedance probability to calculate the excedance values
            etu (string): excedance time unit, allowed ['seconds','minutes','hours','days','years'], default='days'
            under (bool): caluclate the probability for which values are exceeded (False) or are not exceeded (“True”)

        Returns:
            A list of (values,probability,time) tuples, output excedance time is returned according specified *etu* value
        """
        if values and not isinstance(values, (list, tuple)):
            raise TypeError("values must be a list")
        if not perc and isinstance(perc, (list, tuple)):
            raise TypeError("perc must be a list")
        if values is None and perc is None:
            raise IOError("one of values or perc list are required")

        if not etu in ['seconds', 'minutes', 'hours', 'days', 'years']:
            raise TypeError("etu accpted values are: 'seconds','minutes','hours','days','years'")

        self.values = values
        self.perc = perc
        self.etu = etu
        self.under = under
        self.prob = []
        self.time_f = []

    def execute1(self, dataframe):
        df = dataframe
        try:
            import scipy.stats as sp
        except:
            raise ImportError("scipy module is required for this method")

        if df.index.freq:
            freq = df.index.freq.delta.total_seconds()
        else:
            freq = (df.index[1] - df.index[0]).seconds
        # freq=600

        if self.etu == 'seconds':
            res = freq
        elif self.etu == 'minutes':
            res = freq / 60
        elif self.etu == 'hours':
            res = freq / 3600
        elif self.etu == 'days':
            res = freq / (3600 * 24)
        elif self.etu == 'years':
            res = freq / (365 * 3600 * 24)
        data = df["data"].dropna().values
        result1['type'] = "dict list"
        if self.values:
            for v in self.values:
                perc = sp.percentileofscore(data, v)
                if not self.under:
                    perc = 100 - perc
                self.prob.append(perc)
                self.time_f.append(df.size * res * (perc / 100))
            temp = np.column_stack([np.array(self.values), np.array(self.prob), np.array(self.time_f)])
        elif self.perc:
            self.vals = np.array(np.percentile(a=data, q=self.perc, axis=None))
            temp = np.column_stack([np.array(self.perc), np.array(self.vals)])
        result1['data'] = []
        for elem in temp:
            #print(elem)
            if len(elem) > 2:
                result1['data'].append({"value": elem[0], "percentage": elem[1], "frequency": elem[2]})
            else:
                result1['data'].append({"percentage": 100 - elem[0], "value": elem[1]})

        result1['type'] = 'dict list'
        result2 = json.dumps(result1)
        # print(result2)
        return result1['data']


class ExceedanceData(waIstsos):
    """
        Run exceedance filter
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        res={}
        val = self.json['exceevalues']
        if len(val) != 0:
            values = map(float, val.split(','))
        else:
            values = None

        perc = self.json['exceeperc']

        if len(perc) != 0:
            perc = map(float, perc.split(','))
        else:
            perc = None

        etu = self.json['etu']
        under = self.json['exceeunder']
        index1=self.json['index1']
        value1=self.json['values1']

        data1 = {'date': index1, 'data':value1}
        df = pd.DataFrame(data1,columns = ['date','data'])
        df['date'] = pd.to_datetime(df['date'])
        df.index = df['date']
        del df['date']

        exeedance=Exceedance(perc=perc, values=values, etu=etu, under=under)
        res['exceedance']=exeedance.execute1(df)
        self.setData(res['exceedance'])
        self.setMessage("exceedance is successfully working")



# class DigitalFilter():
#     """ """

#     def __init__(self, fs, lowcut, highcut=0.0, order=5, btype='lowpass'):
#         """bandpass Butterworth filter

#         Args:
#             lowcut (float): low cutoff frequency
#             highcut (float): high cutoff frequency
#             fs (float): sampling frequency
#             order (int): the filter order
#             btype (str): band type, one of ['lowpass', 'highpass', 'bandpass', 'bandstop']

#         Returns:
#             A new OAT object with filitered data
#         """
#         super(DigitalFilter, self).__init__()

#         self.lowcut = lowcut
#         self.highcut = highcut
#         self.fs = fs
#         self.order = order
#         self.btype = btype

#     def execute(self, oat, detailedresult=False):
#         """ Apply bandpass Butterworth filter to an OAT object """
#         try:
#             from scipy.signal import butter, lfilter, lfilter_zi
#         except:
#             raise ImportError("scipy.signal module is required for this method")

#         nyq = 0.5 * self.fs
#         low = self.lowcut / nyq
#         high = self.highcut / nyq
#         b, a = butter(self.order, [low, high], btype=self.btype)
#         #y = lfilter(b, a, oat.ts['data'])
#         zi = lfilter_zi(b, a)
#         y, zo = lfilter(b, a, oat.ts['data'], zi=zi * oat.ts['data'][0])

#         #copy oat and return the modified copy
#         temp_oat = oat.copy()
#         temp_oat.ts['data'] = y

#         self.result['type'] = "sensor"
#         self.result['data'] = temp_oat

#         return self.returnResult(detailedresult)



class regularization(waIstsos):

    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executeGet(self):
        ############################
        #     Resampling Code
        ############################
        # from pandas import read_csv
        # from pandas import datetime
        # from datetime import datetime
        # import pandas as pd
        # import json
        # data = {'date': ['2014-05-01 18:47:05.069722', '2014-05-01 18:47:05.119994', '2014-05-02 18:47:05.178768', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.280592', '2014-05-03 18:47:05.332662', '2014-05-03 18:47:05.385109', '2014-05-04 18:47:05.436523', '2014-05-04 18:47:05.486877'],'values': [34, 25, 26, 15, 15, 14, 26, 25, 62, 41]}
        # df = pd.DataFrame(data, columns = ['date', 'values'])
        # df['date'] = pd.to_datetime(df['date'])
        # df.index = df['date']
        # del df['date']
        # resdata=df.resample('D', how='sum').to_json()
        # parsed_json=json.loads(resdata)
        # json_data = '{"103": {"class": "V", "Name": "Samiya", "Roll_n": 12}, "102": {"class": "V", "Name": "David", "Roll_no": 8}, "101": {"class": "V", "Name": "Rohit", "Roll_no": 7}}'
        # parsed_json=json.loads(json_data)
        # print(parsed_json['103']['class'])
        # data = {}
        # data["istsos_version"] = ""
        # data["latest_istsos_version"] = ""
        # data["latest_istsos_changelog"] = ""
        # data["download_url"] = "https://sourceforge.net/projects/istsos"
        # data["istsos_message"] = "updates not found"
        # data["istsos_update"] = False
        ############################
        #     Regularisation Code
        ############################
        import pandas as pd
        from dateutil.parser import parse as parse_time
        times = ['2011-01-01 00:00:00', '2011-01-01 00:53:00', '2011-01-01 02:00:00']
        times = [parse_time(t) for t in times]
        x = pd.DataFrame([1.1, 2.3, 5.2], index=pd.DatetimeIndex(times))
        x.asfreq(pd.datetools.Hour(), method='pad')
        self.setData(x)
        self.setMessage("this is regularisation successfully")


class HydroGraphSep():
    """ Class to assign constant weight values """

    def __init__(self, mode, alpha=0.98, bfl_max=0.50):
        """Perform hydrogram separation

        Args:
            mode (str): the method for hydrograph separation.
            Alleowed modes are:
            * TPDF: Two Parameter Digital Filter (Eckhardt, K., 2005. How to Construct Recursive Digital Filters
              for Baseflow Separation. Hydrological Processes, 19(2):507-515).
            * SPDF: Single Parameter Digital Filter (Nathan, R.J. and T.A. McMahon, 1990. Evaluation of Automated
              Techniques for Baseflow and Recession Analysis. Water Resources Research, 26(7):1465-1473).

        Returns:
            a tuple of two oat.Sensor objects (baseflow,runoff)
        """
        if not mode in ['TPDF', 'SPDF']:
            raise ValueError("stat parameter shall be one of: 'VAR','SD','CV','WT','SQRWT'")

        self.mode = mode
        self.alpha = alpha
        self.bfl_max = bfl_max

    def execute(self, dataframe):
        """ Compute statistics """
        df=dataframe

        """ apply selected mode for hysep """

        #if 'use' in oat.ts.columns:
            #del oat.ts['use']

        flux = df
        base = df

        #print (base.ts.ix[0]['data'])

        base['quality'] = np.zeros(base['quality'].size)
        base['data'] = np.zeros(base['data'].size)
        runoff = base
        base.ix[0, 'data'] = flux.ix[0, 'data']

        #print (len(flux.ts.index))

        if self.mode == 'TPDF':
            a = (1 - self.bfl_max) * self.alpha
            b = (1 - self.alpha) * self.bfl_max
            c = (1 - self.alpha * self.bfl_max)
            for i in range(1, len(flux.index)):
                #base.ts.ix[i]['data'] = ((1 - self.bfl_max) * self.alpha * base.ts.ix[i - 1]['data']
                    #+ (1 - self.alpha) * self.bfl_max * flux.ts.ix[i]['data']) / (1 - self.alpha * self.bfl_max)
                base.ix[i, 'data'] = (a * base.ix[i - 1, 'data']
                    + b * flux.ix[i, 'data']) / c
                if base.ix[i, 'data'] > flux.ix[i, 'data']:
                    base.ix[i, 'data'] = flux.ix[i, 'data']
                runoff.ix[i, 'data'] = flux.ix[i, 'data'] - base.ix[i, 'data']

        elif self.mode == 'SPDF':
            a = (1 + self.alpha) / 2
            for i in range(1, len(flux.index)):
                #runoff.ts.ix[i]['data'] = (self.alpha * runoff.ts.ix[i - 1]['data']
                    #+ ((1 + self.alpha) / 2) * (flux.ts.ix[i]['data'] - flux.ts.ix[i - 1]['data']))
                runoff.ix[i, 'data'] = (self.alpha * runoff.ix[i - 1, 'data']
                    + a * (flux.ix[i, 'data'] - flux.ix[i - 1, 'data']))
                if runoff.ix[i, 'data'] < 0:
                    runoff.ix[i, 'data'] = 0
                if runoff.ix[i, 'data'] > flux.ix[i, 'data']:
                    runoff.ix[i, 'data'] = flux.ix[i, 'data']
                base.ix[i, 'data'] = flux.ix[i, 'data'] - runoff.ix[i, 'data']

        base.name = "{}_base".format('base')
        runoff.name = "{}_runoff".format('runoff')

#         self.result['type'] = "sensor list"
#         self.result['data'] = [base, runoff]
#         return self.returnResult(detailedresult)
        return base

class HSMethod(waIstsos):
    """
        Run HargreavesETo method
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        import pandas as pd
        import numpy as np
        import datetime
        from datetime import datetime
        import time
        index1=self.json['index1']
        values1=self.json['values1']
        qua=self.json['qual']
        # mode = self.json['hsmode']
        # alpha =self.json['hsalpha']
        # bfl = self.json['hsbfl']
        
        mode = 'TPDF'
        alpha = 0.98
        bfl = 0.50

        data1 = {'date': index1, 'data':values1, 'quality':qua}
        df = pd.DataFrame(data1,columns = ['date','data','quality'])
        df['date'] = pd.to_datetime(df['date'])
        df.index = df['date']
        del df['date']
        
        HS=HydroGraphSep(mode, alpha=alpha, bfl_max=bfl)
        resdata=HS.execute(df)

        values = np.array(resdata['data'])
        times = resdata.index
        times_string =[]
        for i in times:
            times_string.append(str(i))

        def convert_to_timestamp(a):
            dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
            return int(time.mktime(dt.timetuple()))

        times_timestamp = map(convert_to_timestamp, times_string)

        data4 = []
        for i in range(len(times_string)):
            a = [times_timestamp[i], values[i]]
            data4.append(a)

        # dictionary = {'data': data4}

        self.setData(data4)
        self.setMessage("resampling is successfully working")


class Fill():
    """ """
    def __init__(self, fill=None, limit=None):
        """Different methods for No data filling

        Args:
            fill (str): if not null it defines the method for filling no-data optional are:
                * 'bfill' = backward fill
                * ‘ffill’ = forward fill
                * 'time' = interpolate proportional to time distance
                * 'spline' = use spline interpolation
                * 'linear' = linear interpolation
                * 'quadratic'= quadratic interpolation
                * 'cubic'= cucbic interpolation
            limit (int): if method is ffill or bfill when not null defines the maximum numbers of allowed consecutive no-data valuas to be filled
        """
        self.fill = fill
        self.limit = limit
    def execute(self, dataframe):
        df=dataframe
        """ Fill no-data"""

        if self.fill in ['bfill', 'ffill']:
            temp_oat1 = df.fillna(method=self.fill, limit=self.limit)
        if self.fill in ['time', 'spline', 'polynomial', 'linear', 'quadratic', 'cubic']:
            temp_oat1 = df.interpolate(method=self.fill, limit=self.limit)
        return temp_oat1

class fillMethod(waIstsos):
    """
        Run HargreavesETo method
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        import pandas as pd
        import numpy as np
        import datetime
        from datetime import datetime
        import time
        index1=self.json['index1']
        values1=self.json['values1']
        qua=self.json['qual']
        fill = self.json['fillMethod1']
        limit = self.json['fillConsucutive1']
        if limit=='-1':
            limit=None
        else:
            limit=int(limit)

        data1 = {'date': index1, 'data':values1, 'quality':qua}
        df = pd.DataFrame(data1,columns = ['date','data','quality'])
        df['date'] = pd.to_datetime(df['date'])
        df.index = df['date']
        del df['date']
        
        fill1=Fill(fill, limit)
        resdata=fill1.execute(df)

        values = np.array(resdata['data'])
        times = resdata.index
        times_string =[]
        for i in times:
            times_string.append(str(i))

        def convert_to_timestamp(a):
            dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
            return int(time.mktime(dt.timetuple()))

        times_timestamp = map(convert_to_timestamp, times_string)

        data4 = []
        for i in range(len(times_string)):
            a = [times_timestamp[i], values[i]]
            data4.append(a)

        # dictionary = {'data': data4}

        self.setData(data4)
        self.setMessage("resampling is successfully working")

class HargreavesETo1():
    """ """
    def __init__(self):
        self.prob = []
        self.time_f = []
    def execute1(self, dataframe):
        """ execute method """
        df = dataframe
        temp_oat = df.groupby(pd.TimeGrouper(freq='D')).agg({'data': lambda x: (0.0023 * (x.mean() + 17.8) * (x.max() - x.min()) ** 0.5),'quality': np.min})
        return temp_oat

class Hargreaves(waIstsos):
    """
        Run HargreavesETo method
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        import pandas as pd
        import numpy as np
        import datetime
        from datetime import datetime
        import time
        # from pandas import read_csv
        # from pandas import datetime
        # from datetime import datetime
        # import pandas as pd
        # import time
        index1=self.json['index1']
        values1=self.json['values1']
        qua=self.json['qual']
        data1 = {'date': index1, 'data':values1, 'quality':qua}
        df = pd.DataFrame(data1,columns = ['date','data','quality'])
        df['date'] = pd.to_datetime(df['date'])
        df.index = df['date']
        del df['date']

        # res={}
        # data1 = {'date': ['2014-05-01 18:47:05.069722', '2014-05-01 18:47:05.119994', '2014-05-02 18:47:05.178768', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.280592', '2014-05-03 18:47:05.332662', '2014-05-03 18:47:05.385109', '2014-05-04 18:47:05.436523', '2014-05-04 18:47:05.486877'],'data': [34, 25, 26, 15, 15, 14, 26, 25, 62, 41],'quality': [200, 200, 200, 200, 200, 200, 200, 200, 200, 200]}
        # #data1 = {'date': index1, 'value':values1}
        # df = pd.DataFrame(data1,columns = ['date','data','quality'])
        # df['date'] = pd.to_datetime(df['date'])
        # df.index = df['date']
        # # df.data=df['value']
        # del df['date']
        haygreaves=HargreavesETo1()
        resdata=haygreaves.execute1(df)
        values = np.array(resdata['data'])
        times = resdata.index
        times_string =[]
        for i in times:
            times_string.append(str(i))

        def convert_to_timestamp(a):
            dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
            return int(time.mktime(dt.timetuple()))

        times_timestamp = map(convert_to_timestamp, times_string)

        data4 = []
        for i in range(len(times_string)):
            a = [times_timestamp[i], values[i]]
            data4.append(a)

        # dictionary = {'data': data4}

        self.setData(data4)
        self.setMessage("resampling is successfully working")


class waValidatedb(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        from walib.utils import validatedb
        res = {}
        try:
            test_conn = validatedb(
                self.json["user"],
                self.json["password"],
                self.json["dbname"],
                self.json["host"],
                self.json["port"])
            res["database"] = "active"

        except:
            res["database"] = "inactive"

        self.setData(res)
        self.setMessage("Database validation request successfully executed")