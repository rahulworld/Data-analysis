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

try:
    from oatlib import oat_algorithms as oa
except:
    import oat_algorithms as oa


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


class resamplingData(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        res = {}
        from pandas import read_csv
        from pandas import datetime
        from datetime import datetime
        import pandas as pd
        # import json
        freq=self.json['freq']
        how=self.json['sampling']
        fill=self.json['fill']
        limit=self.json['limit']
        quality=self.json['Quality']
        index1=self.json['index1']
        values1=self.json['values1']
        if freq=="":
            fill='1H'
        # self.oat.ts=self.json['data']['']
        if fill == '':
            fill = None

        if limit == -1:
            limit = None

        # quality = self.gui.resampleQual.currentText()

        # self.history['params']['frequency'] = freq
        # self.history['params']['how'] = how
        # self.history['params']['fill'] = fill
        # self.history['params']['limit'] = limit
        # self.history['params']['how_quality'] = quality

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
        # df.data=df['value']
        del df['date']

        resample=Resample1(freq=freq, how=how, fill=fill, limit=int(limit), how_quality=quality)
        res['resampled']=resample.execute1(df).to_json()
        # resdata=df.resample('D', how='sum').to_json()
        # res["resampled"]=resdata

        self.setData(res['resampled'])
        self.setMessage("resampling is successfully working")

class exeedance(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        res = {}
        from pandas import read_csv
        from pandas import datetime
        from datetime import datetime
        import pandas as pd
        # import json
        freq=self.json['freq']
        how=self.json['sampling']
        fill=self.json['fill']
        limit=self.json['limit']
        quality=self.json['Quality']
        index1=self.json['index1']
        values1=self.json['values1']
        if freq=="":
            fill='1H'
        # self.oat.ts=self.json['data']['']
        if fill == '':
            fill = None

        if limit == -1:
            limit = None

        # quality = self.gui.resampleQual.currentText()

        # self.history['params']['frequency'] = freq
        # self.history['params']['how'] = how
        # self.history['params']['fill'] = fill
        # self.history['params']['limit'] = limit
        # self.history['params']['how_quality'] = quality

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
        # df.data=df['value']
        del df['date']

        resample=Resample1(freq=freq, how=how, fill=fill, limit=int(limit), how_quality=quality)
        res['resampled']=resample.execute1(df).to_json()
        # resdata=df.resample('D', how='sum').to_json()
        # res["resampled"]=resdata

        self.setData(res['resampled'])
        self.setMessage("resampling is successfully working")


class DigitalFilter():
    """ """

    def __init__(self, fs, lowcut, highcut=0.0, order=5, btype='lowpass'):
        """bandpass Butterworth filter

        Args:
            lowcut (float): low cutoff frequency
            highcut (float): high cutoff frequency
            fs (float): sampling frequency
            order (int): the filter order
            btype (str): band type, one of ['lowpass', 'highpass', 'bandpass', 'bandstop']

        Returns:
            A new OAT object with filitered data
        """
        super(DigitalFilter, self).__init__()

        self.lowcut = lowcut
        self.highcut = highcut
        self.fs = fs
        self.order = order
        self.btype = btype

    def execute(self, oat, detailedresult=False):
        """ Apply bandpass Butterworth filter to an OAT object """
        try:
            from scipy.signal import butter, lfilter, lfilter_zi
        except:
            raise ImportError("scipy.signal module is required for this method")

        nyq = 0.5 * self.fs
        low = self.lowcut / nyq
        high = self.highcut / nyq
        b, a = butter(self.order, [low, high], btype=self.btype)
        #y = lfilter(b, a, oat.ts['data'])
        zi = lfilter_zi(b, a)
        y, zo = lfilter(b, a, oat.ts['data'], zi=zi * oat.ts['data'][0])

        #copy oat and return the modified copy
        temp_oat = oat.copy()
        temp_oat.ts['data'] = y

        self.result['type'] = "sensor"
        self.result['data'] = temp_oat

        return self.returnResult(detailedresult)



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
