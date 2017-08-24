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
import scipy
from walib.OAT import Methods


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

class DigitalThread(waIstsos):
    """
        Execute digital filter (?)
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        try:
            index1=self.json['index1']
            values1=self.json['values1']
            qua=self.json['qual']

            highcut = self.json['dhigh']
            lowcut = self.json['dlow']
            order = self.json['dorder']
            filter_type = self.json['dfilter']

            if highcut == 0:
                self.exception.emit(Exception('high cutoff freq must be > 0.0'))
                return
     
            data1 = {'date': index1, 'data':values1, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']
            
            digital=Methods.DigitalFilter(lowcut, highcut, order=order, btype=filter_type)
            dig=digital.execute(df)

        except:
            dig = "inactive"

        self.setData(dig)
        self.setMessage("digital filter is successfully working")


class Statisticsmethod(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    """
        Execute hydro graph separator
    """
    def executePost(self):
        try:
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

            timezoneSta=int(timezoneSta)

            tbounds = [None, None]
            if timeSta:
                timezone = timezoneSta
                if timezone >= 0:
                    timez = "+" + "%02d:00" % (timezone)
                else:
                    timez = "-" + "%02d:00" % (abs(timezone))
                begin_pos = beginSta + timez
                end_pos = endSta + timez
                tbounds = [begin_pos, end_pos]

            stat=Methods.Statistics(data=data, quality=quality, tbounds=tbounds)
            st=stat.execute(df)
        except:
            data4 = "inactive"
        self.setData(st['data'])
        self.setMessage("Statistics is successfully working")

class resamplingData(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        try:
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
            values2=self.json['values1']
            qua=self.json['qual']

            if freq=="":
                freq='1H'

            if fill == '':
                fill = None

            if limit == -1:
                limit = None

            data1 = {'date': index1, 'data':values2, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']

            resample=Methods.Resample1(freq=freq, how=how, fill=fill, limit=int(limit), how_quality=quality)
            resdata=resample.execute1(df)

            values = np.array(resdata['data'])
            values1 = np.array(resdata['quality'])
            times = resdata.index
            times_string =[]
            for i in times:
                times_string.append(str(i))

            def convert_to_timestamp(a):
                dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
                return int(time.mktime(dt.timetuple()))*1000000
            # %Y-%m-%d %H:%M:%S.%f
            times_timestamp = map(convert_to_timestamp, times_string)

            data4 = []
            for i in range(len(times_string)):
                a = [times_timestamp[i], values[i], values1[i]]
                data4.append(a)

            # dictionary = {'data': data4}
        except:
            data4 = "inactive"

        self.setData(data4)
        self.setMessage("resampling is successfully working")

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

        exeedance=Methods.Exceedance(perc=perc, values=values, etu=etu, under=under)
        resdata=exeedance.execute1(df)
        self.setData(resdata)
        self.setMessage("exceedance is successfully working")


class IntegrateMethod(waIstsos):
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        try:
            index1=self.json['index1']
            values1=self.json['values1']
            qua=self.json['qual']

            tunit = self.json['itimeunit']
            factor = self.json['ifactor']
            how = self.json['ihow']
            astext = self.json['idataastext']
            itimeuse=self.json['iusetime']
            itimezone=self.json['itimezone']
            ibegin=self.json['ibegin']
            iend=self.json['iend']

            itimezone=int(itimezone)

            period = [(None, None)]
            if itimeuse:
                timezone1 = itimezone
                if timezone1 >= 0:
                    timez = "+" + "%02d:00" % (timezone1)
                else:
                    timez = "-" + "%02d:00" % (abs(timezone1))

                begin_pos = ibegin + timez
                end_pos = iend + timez

                period = [(begin_pos, end_pos)]

            data1 = {'date': index1, 'data':values1, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']
            
            Intgrt=Methods.Integrate(periods=period, tunit=tunit, factor=factor, how=how,astext=astext)
            IG=Intgrt.execute(df)
        except:
            IG = "inactive"

        self.setData(IG)
        self.setMessage("Integrate is successfully working")


class HydroSeparationTh(waIstsos):
    """
        Run HargreavesETo method
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        try:
            import pandas as pd
            import numpy as np
            import datetime
            from datetime import datetime
            import time
            index1=self.json['index1']
            values1=self.json['values1']
            qua=self.json['qual']

            mode = self.json['hsmode']
            alpha =self.json['hsalpha']
            bfl = self.json['hsbfl']
            alpha1=float(alpha)        
            bfl1=float(bfl)
            data1 = {'date': index1, 'data':values1, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']

            HS=Methods.HydroGraph12(mode=mode, alpha=alpha1, bfl_max=bfl1)
            resdata=HS.execute12(df)

            # HS=HydroGraph12(mode, alpha=alpha, bfl_max=bfl)
            # resdata=HS.execute12(df)
            values = np.array(resdata['runoff']['data'])
            values1 = np.array(resdata['base']['data'])
            times = resdata['runoff'].index
            times_string =[]
            for i in times:
                times_string.append(str(i))

            def convert_to_timestamp(a):
                dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
                return int(time.mktime(dt.timetuple()))*1000000

            times_timestamp = map(convert_to_timestamp, times_string)

            data4 = []
            for i in range(len(times_string)):
                a = [times_timestamp[i], values[i],values1[i]]
                data4.append(a)

            # dictionary = {'data': data4}
        except:
            data4 = "inactive"

        self.setData(data4)
        self.setMessage("hydrosepration is successfully working")

class QualityMethod(waIstsos):
    """
        Run data values method
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        try:
            import pandas as pd
            import numpy as np
            import datetime
            from datetime import datetime
            import time
            index1=self.json['index1']
            values1=self.json['values1']
            qua=self.json['qual']

            value = self.json['qvalue']
            stat = self.json['qstat']

            timeuse = self.json['qtime']
            dvbegin = self.json['qbegin']
            dvend = self.json['qend']
            dvtimezone = self.json['qtimezone']

            limituse = self.json['qlimit']
            dvlow = self.json['qlow']
            dvhigh = self.json['qhigh']

            dvlow=int(dvlow)
            dvhigh=int(dvhigh)

            tbounds = [(None, None)]
            vbounds = [(None, None)]

            dvtimezone=int(dvtimezone)

            if timeuse:
                if dvtimezone >= 0:
                    timez = "+" + "%02d:00" % (dvtimezone)
                else:
                    timez = "-" + "%02d:00" % (abs(dvtimezone))
                begin_pos = dvbegin + timez
                end_pos = dvend + timez
                tbounds = [(begin_pos, end_pos)]

            if limituse:
                min_val = dvlow
                max_val = dvhigh
                vbounds = [(min_val, max_val)]

            data1 = {'date': index1, 'data':values1, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']

            setQualityStat=Methods.QualityStat(value=value, vbounds=vbounds, tbounds=tbounds,statflag=stat)
            resdata=setQualityStat.execute(df)
            # return resdata
            values = np.array(resdata['data'])
            values1 = np.array(resdata['quality'])
            times = resdata.index
            times_string =[]
            for i in times:
                times_string.append(str(i))

            def convert_to_timestamp(a):
                dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
                return int(time.mktime(dt.timetuple()))*1000000

            times_timestamp = map(convert_to_timestamp, times_string)
            data4 = []
            for i in range(len(times_string)):
                a = [times_timestamp[i], values[i],values1[i]]
                data4.append(a)
            # dictionary = {'data': data4}
        except:
            data4 = "inactive"
        self.setData(data4)
        self.setMessage("data values is successfully working")

class DataValuesMethod(waIstsos):
    """
        Run data values method
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        try:
            import pandas as pd
            import numpy as np
            import datetime
            from datetime import datetime
            import time
            index1=self.json['index1']
            values1=self.json['values1']
            qua=self.json['qual']

            value = self.json['dvvalue']
            value = float(value)

            timeuse = self.json['dvtime']
            dvbegin = self.json['dvbegin']
            dvend = self.json['dvend']
            dvtimezone = self.json['dvtimezone']
            dvtimezone=int(dvtimezone)

            limituse = self.json['dvlimit']
            dvlow = self.json['dvlow']
            dvhigh = self.json['dvhigh']

            dvlow=float(dvlow)
            dvhigh=float(dvhigh)

            tbounds = [(None, None)]
            vbounds = [(None, None)]

            if timeuse:
                if dvtimezone >= 0:
                    timez = "+" + "%02d:00" % (dvtimezone)
                else:
                    timez = "-" + "%02d:00" % (abs(dvtimezone))
                begin_pos = dvbegin + timez
                end_pos = dvend + timez
                tbounds = [(begin_pos, end_pos)]

            if limituse:
                min_val = dvlow
                max_val = dvhigh
                vbounds = [(min_val, max_val)]

            data1 = {'date': index1, 'data':values1, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']

            setDataValues=Methods.SetDataValues1(value=value, vbounds=vbounds, tbounds=tbounds)
            resdata=setDataValues.execute(df)
            # return resdata
            values = np.array(resdata['data'])
            values2 = np.array(resdata['quality'])
            times = resdata.index
            times_string =[]
            for i in times:
                times_string.append(str(i))

            def convert_to_timestamp(a):
                dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
                return int(time.mktime(dt.timetuple()))*1000000

            times_timestamp = map(convert_to_timestamp, times_string)
            data4 = []
            for i in range(len(times_string)):
                a = [times_timestamp[i], values[i], values2[i]]
                data4.append(a)
            # dictionary = {'data': data4}
        except:
            data4 = "inactive"
        self.setData(data4)
        self.setMessage("data values is successfully working")


class fillMethod(waIstsos):
    """
        Run HargreavesETo method
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        try:
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
            
            fill1=Methods.Fill1(fill, limit)
            resdata=fill1.execute(df)

            values = np.array(resdata['data'])
            values1 = np.array(resdata['quality'])
            times = resdata.index
            times_string =[]
            for i in times:
                times_string.append(str(i))

            def convert_to_timestamp(a):
                dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
                return int(time.mktime(dt.timetuple()))*1000000

            times_timestamp = map(convert_to_timestamp, times_string)

            data4 = []
            for i in range(len(times_string)):
                a = [times_timestamp[i], values[i],values1[i]]
                data4.append(a)

            # dictionary = {'data': data4}
        except:
            data4 = "inactive"

        self.setData(data4)
        self.setMessage("resampling is successfully working")


class Hargreaves(waIstsos):
    """
        Run HargreavesETo method
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        data4 = []
        try:
            import pandas as pd
            import numpy as np
            import datetime
            from datetime import datetime
            import time
            index1=self.json['index1']
            values1=self.json['values1']
            qua=self.json['qual']
            data1 = {'date': index1, 'data':values1, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']

            haygreaves=Methods.HargreavesETo1()
            resdata=haygreaves.execute1(df)
            values = np.array(resdata['data'])
            values1 = np.array(resdata['quality'])
            times = resdata.index
            times_string =[]
            for i in times:
                times_string.append(str(i))

            def convert_to_timestamp(a):
                dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
                return int(time.mktime(dt.timetuple()))*1000000

            times_timestamp = map(convert_to_timestamp, times_string)

            for i in range(len(times_string)):
                a = [times_timestamp[i], values[i],values1[i]]
                data4.append(a)

            # dictionary = {'data': data4}
        except:
            data4 = "inactive"

        self.setData(data4)
        self.setMessage("Hargreaves is successfully working")


class HydroIndices(waIstsos):
    """
        Run Hydro indices filter
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)
    
    def executePost(self):
        result1 = {
            "op": "hydroIndices",
            "type": "dict list",
            "data": []
        }
        try:
            import pandas as pd
            import numpy as np
            import datetime
            from datetime import datetime
            import time
            index1=self.json['index1']
            values1=self.json['values1']
            qua=self.json['qual']

            htype = self.json['hialpha']
            hindicies = self.json['hiindi']
            # hindicies = '1,3'

            if htype != 'MA':
                self.exception.emit(Exception("Sorry, only Ma is supported (Alphanumeric Code)"))
                return

            if hindicies == '':
                self.exception.emit(Exception("Please define code"))
                return

            code1 = map(int, hindicies.split(','))
            # code = [1,3]

            if len(code1) != 2:
                self.exception.emit(Exception("Please change code"))
                return
            elif code1[0] > code1[1]:
                self.exception.emit(Exception('code 1 must be lower than code 2'))
                return
            elif code1[0] < 1:
                self.exception.emit(Exception("Code 1 shoul'd be >= 1"))
                return
            elif code1[1] > 45:
                self.exception.emit(Exception("Code 2 shoul'd be <= 45"))
                return

            comp = self.json['hicomp']
            classification = self.json['hicss']
            median = self.json['himed']
            drain = self.json['hida']
            drain=int(drain)
            per=self.json['hiper']
            beg=self.json['hib']
            en=self.json['hie']

            period = None
            if per:
                begin = beg.replace(" ", "T")
                end = en.replace(" ", "T")

                period = [begin, end]

            data1 = {'date': index1, 'data':values1, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']

            for c in range(code1[0], code1[1]):
                HyI = Methods.HydroIndices1(htype=htype, code1=c, flow_component=comp,stream_classification=classification,median=median,drain_area=drain, period=period)
                result=HyI.execute(df)
                result1['data'].append({"index": c, "value": result})
        except:
            result1[data] = "inactive"

        self.setData(result1)
        self.setMessage("Hydro Indicies is successfully working")


class HydroEventsTh(waIstsos):
    """
        Run Hydro events filter
        calculate portion of time series associated with peak flow events
    """
    def __init__(self, waEnviron):
        waIstsos.__init__(self, waEnviron)

    def executePost(self):
        dataFull=[]
        try:
            import pandas as pd
            import numpy as np
            import datetime
            from datetime import datetime
            import time
            index1=self.json['index1']
            values1=self.json['values1']
            qua=self.json['qual']

            rise = float(self.json['hydrise'])
            fall = float(self.json['hydfall'])
            window = int(self.json['hydwindow'])
            peak = float(self.json['hydpeak'])

            suffix = self.json['hydseries']
            per=self.json['hydtime']
            beg=self.json['hydbeg']
            en=self.json['hydend']
            period = None
            if per:
                begin = beg.replace(" ", "T")
                end = en.replace(" ", "T")
                period = [begin, end]

            if suffix == "":
                suffix = "_event_N"

            data1 = {'date': index1, 'data':values1, 'quality':qua}
            df = pd.DataFrame(data1,columns = ['date','data','quality'])
            df['date'] = pd.to_datetime(df['date'])
            df.index = df['date']
            del df['date']

            HyE=Methods.HydroEvents12(rise_lag=rise, fall_lag=fall, window=window,min_peak=peak, suffix=suffix, period=period)
            resdata=HyE.execute12(df)

            for i in range(len(resdata)):
                values = np.array(resdata[i]['data'])
                values2 = np.array(resdata[i]['quality'])
                times = resdata[i].index
                times_string =[]
                for i in times:
                    times_string.append(str(i))

                def convert_to_timestamp(a):
                    dt = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
                    return int(time.mktime(dt.timetuple()))*1000000

                times_timestamp = map(convert_to_timestamp, times_string)
                data4 = []
                for i in range(len(times_string)):
                    a = [times_timestamp[i], values[i],values2[i]]
                    data4.append(a)
                dataFull.append(data4)

        except:
            dataFull = "inactive"
        self.setData(dataFull)
        self.setMessage("Hydro events is successfully working")


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
