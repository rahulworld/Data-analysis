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
from walib import resource, utils, databaseManager, configManager
import sys
import os
import xml.etree.ElementTree as ET
import urllib2
from walib.oat.oatlib import method


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

class resamplingData(waIstsos):

    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        res = {}
        try:
            from pandas import read_csv
            from pandas import datetime
            from datetime import datetime
            import pandas as pd
            import json

            # freq = self.gui.resampleFreq.text()
            # how = self.gui.resampleHow.currentText()
            # fill = self.gui.resampleFill.currentText()

            if fill == '':
                fill = None

            limit = self.gui.resampleLimit.value()
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
            res = method.Resample(freq=freq, how=how, fill=fill, limit=limit,how_quality=quality)

            data = {'date': ['2014-05-01 18:47:05.069722', '2014-05-01 18:47:05.119994', '2014-05-02 18:47:05.178768', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.280592', '2014-05-03 18:47:05.332662', '2014-05-03 18:47:05.385109', '2014-05-04 18:47:05.436523', '2014-05-04 18:47:05.486877'],'battle_deaths': [34, 25, 26, 15, 15, 14, 26, 25, 62, 41]}
            df = pd.DataFrame(data, columns = ['date', 'battle_deaths'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']
            resdata=df.resample('D', how='sum').to_json()
            # def validatedb(user, password, dbname, host, port=5432, service=None):
            test_conn = validatedb(
                self.json["user"],
                self.json["password"],
                self.json["dbname"],
                self.json["host"],
                self.json["port"])
            res["database"] = "active"

        except:
            res["database"] = "inactive"
    
    def resammpling(Frequency,samplingMethod,Limit,fill,Quality,seriesData):

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
        self.setData(resdata)
        self.setMessage("this is resampling data")

class regularization(waIstsos):

    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executeGet(self):
        from pandas import read_csv
        from pandas import datetime
        from datetime import datetime
        import pandas as pd
        import json
        data = {'date': ['2014-05-01 18:47:05.069722', '2014-05-01 18:47:05.119994', '2014-05-02 18:47:05.178768', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.230071', '2014-05-02 18:47:05.280592', '2014-05-03 18:47:05.332662', '2014-05-03 18:47:05.385109', '2014-05-04 18:47:05.436523', '2014-05-04 18:47:05.486877'],'battle_deaths': [34, 25, 26, 15, 15, 14, 26, 25, 62, 41]}
        df = pd.DataFrame(data, columns = ['date', 'battle_deaths'])
        df['date'] = pd.to_datetime(df['date'])
        df.index = df['date']
        del df['date']
        resdata=df.resample('D', how='sum').to_json()
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
        self.setData(resdata)
        self.setMessage("this is resampling data")


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
