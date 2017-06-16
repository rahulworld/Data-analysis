# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

import os.path
from datetime import datetime, timedelta

from osgeo import ogr, osr

import pandas as pd
import numpy as np

try:
    from oatlib import oat_utils
except:
    import oat_utils

#from import oat_utils


class Sensor():
    """Initialize the oat object

    Arguments:
        name (str): the name of the time serie
        desc (str): the description of the time serie
        prop (str): the observed property
        unit (str): the unit of measure of the observed property
        lat (float): the latitude of the station
        lon (float): the longitude of the station
        alt (float): the altitude of the station
        tz (int): the time zone
        freq (str): the data frequency

    Example:
        name: "temperature-4",
        description: "Temperature",
        uom: "celsius",
        longitude: 2.363471,
        latitude: 48.917536,
        timezone: "+1" ,
        unit: "Celsius"

    """

    def __init__(self, name, prop, unit, lat=None, lon=None, alt=None, tz=0,
                desc=None, freq=None, data_availability=[None, None], statflag=None, use=True, topscreen=None, bottomscreen=None):
        """Inits the oat class

        Args:
            name (str): the name of the sensor (maximum length is 10 characters)
            prop(str): the observed property
            unit(str): the unit of measure of the observed property
            lat(float): the latitude of the station
            lon(float): the longitude of the station
            alt(float): the altitude of the station
            tz(int): the time zone
            desc(str): the description of the time serie
            ts(obj): a pandas timeseries object with (time, value) columns et (event time) as time-index and ov (observed values) as value columns
            data_availability(list): time period of data availability (sensor historical records)
            statflag(str): statistical flags to indicate the quality value of the series
            use(bool): wheter to make the current sensor available or not for further elaborations
            topscreen(float): top level of piezometer screen
            bottomscreen(float): bottom level of piezometer screen
        """
        self.name = name  # [:10] if len(name) > 10 else name
        self.desc = desc
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.tz = tz
        self.unit = unit
        self.prop = prop
        self.ts = None
        self.srid = 4326  # srid
        self.freq = freq
        self.statflag = statflag
        self.use = use
        self.data_availability = data_availability
        self.topscreen = topscreen
        self.bottomscreen = bottomscreen

    @classmethod
    def from_sqlite(cls, source, sensor):
        """Create the oat class from sqliteif not self.data_availability:
            begin = self.oat.ts.index.values[0]
            end = self.oat.ts.index.values[-1]

            self.data_availability = [begin, end]

        Args:
            source (str): the sqlite file (including path)
            sensor (list): sensor name
        """
        try:
            from pyspatialite import dbapi2 as db
        except ImportError:
            raise ImportError('<pyspatialite> package not installed')

        con = db.connect(source)

        # check if table contains altitude column
        tmp = con.execute('PRAGMA table_info(freewat_sensors)').fetchall()
        tmp_name = [i[1] for i in tmp]

        if 'altitude' in tmp_name:
            pass
        else:
            print("add missing table....")
            con.execute('ALTER TABLE freewat_sensors ADD COLUMN altitude REAL')
            con.commit()


        sql = "SELECT name, desc, tz, unit, prop, freq, X(geom) as lon, Y(geom) as lat, begin_pos, end_pos, statflag, use, topscreen, bottomscreen, altitude"
        sql += " FROM freewat_sensors WHERE name=?"
        res = con.execute(sql, (sensor,)).fetchone()
        con.close()

        return cls(name=res[0], desc=res[1], tz=res[2], unit=res[3],
                    prop=res[4], freq=res[5], lon=res[6], lat=res[7], alt=res[14],
                    data_availability=[res[8], res[9]], statflag=res[10], use=(res[11] != 0), topscreen=res[12], bottomscreen=res[13])

    @classmethod
    def from_istsos(cls, service, procedure, observed_property, basic_auth=None, srid=4326):
        """Create the oat class from istSOS

        Args:
            service (str): url of the SOS service
            procedure (list): sensor name
            observed_property (list): observed property name
            basic_auth(tuple): touple of username and password - e.g.: ('utente','123')
        """
        try:
            import requests
            #from io import StringIO

        except ImportError:
            raise ImportError('<requests packages not installed>')

        #check input validity
        if len(procedure.split(',')) > 1:
            raise ValueError('<procedure> parameter numerosity is ONE')

        url = service.split('/')

        wa_service = '/'.join(url[:-1]) + '/wa/istsos/services/' + url[-1] + '/procedures/' + procedure


        if basic_auth:
            if len(basic_auth) == 2:
                sos_auth = requests.auth.HTTPBasicAuth(basic_auth[0], basic_auth[1])
            else:
                raise ValueError('<basic_auth> tuple numerosity is TWO')
        else:
            sos_auth = None
        #execute the DS request
        r = requests.get(wa_service, auth=sos_auth)

        #print( "************", r.text)

        #r.encoding = 'UTF-8'
        wa_res = r.json()

        #print(wa_res, "************", r.text)
        #"""

        try:
            oat_name = wa_res['data']['system']
            oat_desc = wa_res['data']['location']['properties']['name']
            epsg = wa_res['data']['location']['crs']['properties']['name']
            oat_lon = wa_res['data']['location']['geometry']['coordinates'][0]
            oat_lat = wa_res['data']['location']['geometry']['coordinates'][1]
            oat_alt = wa_res['data']['location']['geometry']['coordinates'][2]
            oat_data_availability = wa_res['data']['outputs'][0]["constraint"]["interval"]

            # Convert coordinate to EPSG:4326

            # Spatial Reference System
            inputEPSG = int(epsg.replace("EPSG:", ""))
            outputEPSG = srid

            # create a geometry from coordinates
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(float(oat_lon), float(oat_lat))

            # create coordinate transformation
            inSpatialRef = osr.SpatialReference()
            inSpatialRef.ImportFromEPSG(inputEPSG)

            outSpatialRef = osr.SpatialReference()
            outSpatialRef.ImportFromEPSG(outputEPSG)

            coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

            # transform point
            point.Transform(coordTransform)

            oat_lon = point.GetX()
            oat_lat = point.GetY()

            for e in wa_res['data']['outputs']:
                if e['definition'].find(observed_property) >= 0:
                    try:
                        G_unit = str(e['uom'])
                    except:
                        G_unit = "unknown"
                    return cls(
                            prop=observed_property,
                            unit=G_unit,
                            lat=oat_lat,
                            lon=oat_lon,
                            alt=oat_alt,
                            name=oat_name,
                            desc=oat_desc,
                            data_availability=oat_data_availability)

        except Exception as e:
            raise e

    def __repr__(self, line=4):
        """the repr method"""
        pd.set_option('display.max_rows', line)
        rep = "name: %s\n" % self.name
        rep += "desc: %s\n" % self.desc
        rep += "lat: %s\n" % self.lat
        rep += "lon: %s\n" % self.lon
        rep += "alt: %s\n" % self.alt
        rep += "tz: %s\n" % self.tz
        rep += "unit: %s\n" % self.unit.encode('utf-8')
        #rep += "unit: {}\n".format(self.unit.encode('utf-8'))  # .encode('utf-8')
        rep += "prop: %s\n" % self.prop
        rep += "freq: %s\n" % self.freq
        rep += "statflag: %s\n" % self.statflag
        rep += "use: %s\n" % self.use
        rep += "data_availability: %s\n" % self.data_availability
        rep += "ts: %s\n" % self.ts
        return rep

    def load_ts(self, stype, **kwargs):
        """Loader method to append new data to an existing sensor

        Args:
            stype(str): data source type
            kwargs: arguments as per specific module
        Note:
            kwarg depends on the type instantiated, please take a look at specific load methods
        """

        if stype == 'CSV':
            self.ts_from_csv(kwargs)
        elif stype == 'SOS':
            self.ts_from_istsos(kwargs)
        elif stype == 'SQLITE':
            self.ts_from_sqlite(kwargs)
        elif stype == 'PGDB':
            print('PGDB tbd')
        else:
            raise ValueError('Provided data sourcy type is not supported')

        #create the dataquylity column initialized to 1
        self.ts['quality'] = np.zeros(self.ts.size[0])
        #self.ts['quality'] = np.zeros(self.ts.count())

    def ts_from_dict(self, data):
        """Load data from a dict with the following structure:

        Args:
            data (dict): dict

        Example:
            data = {
                'time': ['2015-12-01T12:00:00'],
                'data': [12.56],
                #----optionally----
                'quality': [100],
                'use': [True],
                'obs_index': ['tt_1']
            }

        """
        #self.ts = pd.DataFrame.from_dict(data)

        columns = []
        if not 'time' in data:
            raise ValueError("time key is mandatory")
        columns.append('time')
        lentime = len(data['time'])
        if not 'data' in data:
            raise ValueError("data key is mandatory")
        columns.append('data')
        if 'quality' in data:
            columns.append('quality')
        if 'use' in data:
            columns.append('use')
        if 'obs_index' in data:
            columns.append('obs_index')

        for key in columns:
            if len(data[key]) != lentime:
                raise ValueError("list shall all be of the same length")

        self.ts = pd.DataFrame(data, index=data['time'], columns=columns)
        #self.ts.index.name = 'time'

        self.__set_data_availability()

    def ts_from_csv(self, csvfile, sep=',', timecol=[0], valuecol=1, qualitycol=-1, skiprows=None, comment='#',
        na_values=[], dayfirst=False, strftime=None, freq=None):
        """Load data from a CSV file

        Args:
            csvfile (str):  Either a string path to a file, URL (including http, ftp, and S3 locations), or any object with a read method
                            (such as an open file or StringIO)
            sep (str): A delimiter / separator to split fields on. With sep=None, read_csv will try to infer the delimiter automatically
                        in some cases by "sniffing". The separator may be specified as a regular expression; for instance you may use ‘|\s*’
                        to indicate a pipe plus arbitrary whitespace.
            timecol (list): list of column numbers to be used to parse the times of observations e.g. [0,1]
            valuecol (int) the column number containing the observations values e.g. 2
            qualitycol (int): the column number containing the quality index e.g. 3
            skiprows (int): An integer to skip the first n rows (including headers)
            comment (str): A character indicating a comment line not to be imported
            na_values (list): List of values to be associated with no data value,
            dayfirst (bool): Day came before of month?
            strftime (str): strftime directive (see http://strftime.org/)
        """
        ts_cols = {'time': timecol}
        if not strftime:
            try:
                import dateutil.parser
                ts_parse = lambda x: dateutil.parser.parse(x).replace(tzinfo=None)
            except ImportError:
                ts_parse = lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            ts_parse = lambda x: datetime.strptime(x, strftime)

        if qualitycol != -1:
            names = timecol + ['data', 'quality']
            usecols = timecol + [valuecol, qualitycol]
        else:
            names = timecol + ['data']
            usecols = timecol + [valuecol]

        self.ts = pd.read_csv(
                        header=None,
                        skiprows=skiprows,
                        names=names,
                        comment=comment,
                        na_values=na_values,
                        dayfirst=False,
                        parse_dates=ts_cols,
                        filepath_or_buffer=csvfile,
                        sep=sep,
                        date_parser=ts_parse,
                        index_col='time',
                        usecols=usecols,
                        engine='python'
                        )

        #print(self.ts)

        if freq:
            self.freq = freq
            self.ts.asfreq(freq)

        #if not self.data_availability[0]:
            #begin = self.ts.index.values[0].astype('datetime64[s]')
            #end = self.ts.index.values[-1].astype('datetime64[s]')

            #self.data_availability = [str(begin), str(end)]

        self.__set_data_availability()

        #create the data-quality column initialized to 0
        if qualitycol == -1:
            self.ts['quality'] = np.zeros(self.ts.size)

    def ts_from_istsos(self, service, procedure, observed_property, offering=None,
                    event_time=None, spatial_filter=None, basic_auth=None, freq=None,
                    aggregate_function=None, aggregate_interval=None, qualityIndex=True):
        """Load data from an istsos server

        Args:
            service (str): url of the SOS service
            procedure (list): sensor name
            observed_property (list): observed property name
            offering (str): name of the offering - default value is \'temporary\'
            temporalFilter (tuple): begin and end instant for a between filter - default value None
            featureOfInterest (list): name of the feature of interests - default value None
            spatialFilter (list): bbox coordinates as a list [minx,miny,maxx,maxy]- default value None
            basic_auth(tuple): touple of username and password - e.g.: ('utente','123')
            aggregate_function (str): aggregate function, e.g. MAX, MIN, AVG, SUM, default None
            aggregate_interval (str): aggregate interval, expressed in iso 8601 duration e.g. "P1DT12H"
            qualityIndex (bool): if True istSOS qualityIndex is loaded
        """

        try:
            import requests
            from io import StringIO

        except ImportError:
            raise ImportError('<requests> package not installed')

        #check input validity
        if len(procedure.split(',')) > 1:
            raise ValueError('<procedure> parameter numerosity is ONE')
        if len(observed_property.split(',')) > 1:
            raise ValueError('<observed_property> parameter numerosity is ONE')
        #prepare GetObservation request parameters
        go_parameters = {
                'service': 'SOS',
                'version': '1.0.0',
                'request': 'GetObservation',
                'offering': 'temporary',
                'procedure': procedure,
                'observedProperty': observed_property,
                'responseFormat': 'text/plain'
        }
        #append optional parameters
        if offering:
            go_parameters['offering'] = offering
        if event_time:
            go_parameters['eventTime'] = event_time
        if spatial_filter:
            go_parameters['featureOfInterest'] = spatial_filter
        if qualityIndex is True:
            go_parameters['qualityIndex'] = 'True'
        if basic_auth:
            if len(basic_auth) == 2:
                sos_auth = requests.auth.HTTPBasicAuth(basic_auth[0], basic_auth[1])
            else:
                raise ValueError('<basic_auth> tuple numerosity is TWO')
        else:
            sos_auth = None

        if aggregate_function:
            go_parameters['aggregateFunction'] = aggregate_function
            if not aggregate_interval:
                raise ValueError('Pleaase define a aggregate interval')
            go_parameters['aggregateInterval'] = aggregate_interval

        #execute the GO request
        r = requests.get(service, params=go_parameters, auth=sos_auth)
        #set the pandas time series
        #print (r.text)

        if qualityIndex is True:
            self.ts = pd.read_csv(
                    header=0,
                    skiprows=None,
                    names=['time', 'sensor', 'data', 'quality'],
                    comment='#',
                    na_values=[-999, None, 'None', -999.9],
                    dayfirst=False,
                    parse_dates=['time'],
                    filepath_or_buffer=StringIO(r.text),
                    sep=',',
                    index_col='time',
                    #usecols=['time', 'data', 'quality']
                    usecols=[0, 2, 3]
                    )
        else:
            self.ts = pd.read_csv(
                    header=0,
                    skiprows=None,
                    names=['time', 'sensor', 'data'],
                    comment='#',
                    na_values=[-999, None, 'None', -999.9],
                    dayfirst=False,
                    parse_dates=['time'],
                    filepath_or_buffer=StringIO(r.text),
                    sep=',',
                    index_col='time',
                    #usecols=['time', 'data']
                    usecols=[0, 2]
                    )
            #create the data-quality column initialized to 1
            self.ts['quality'] = np.zeros(self.ts.size)

        if freq:
            self.freq = freq
            self.ts.asfreq(self.freq)

        #set sensor time-zone
        try:
            adate = r.text.split("\n")[1].split(",")[0]
            if "Z" in adate:
                self.tz = "+00:00"
            elif "+" in adate:
                self.tz = adate[adate.find("+"):]
            elif "-" in adate:
                self.tz = adate[adate.find("-"):]
        except:
            pass

        if len(self.ts.index.values) > 0:
            self.__set_data_availability()
        else:
            self.ts = None

    def ts_from_sqlite(self, source, sql=None):
        """Load data from SQLITE

        Args:
            source (str): the sqlite file (including path)
            sql (str): the sql selecting two fields named time and data - *optional*
        """
        try:
            from pyspatialite import dbapi2 as db
        except ImportError:
            raise ImportError('<pyspatialite> package not installed')

        con = db.connect(source)
        if not sql:
            sql = "select time, data, quality, use, obs_index from %s" % self.name

        #execute query and load data
        self.ts = pd.read_sql_query(sql, con, index_col='time', parse_dates=['time'])
        con.close()

        if self.freq:
            self.ts.asfreq(self.freq)

        self.ts['use'] = self.ts['use'].astype(bool)

    def ts_from_gagefile(self, gagefile, startdate, property='stage'):
        """
            Load data from a GAGE file output from modflow

        Args:
            gagefile(str): a string path to a file of a MODFLOW GAGE input file
            startdate(str): isodate starting date (e.g.: '2012-11-21T13:20:00+01:00')
            property(str): the name of the observation to be uploaded as defined in the file (default: 'stage')
                accepted values are: Stage, Flow, Depth, Width, Midpt-Flow, Precip., ET, Runoff
        """
        #get start date
        try:
            time = datetime.strptime(startdate, '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            try:
                import dateutil.parser
                time = dateutil.parser.parse(startdate).replace(tzinfo=None)
            except:
                raise Exception("startdate' input value is not correct")

        #create first value and time series
        mdata = {
            'time': [time],
            'data': [None],
            'quality': [None]
        }
        self.ts = pd.DataFrame(mdata, index=mdata['time'], columns=['data', 'quality'])
        self.ts.index.name = 'time'

        if not os.path.isfile(gagefile):
            raise Exception("gagefile not found!")

        with open(gagefile) as fp:
            lines = fp.readlines()

            #GET GAGE INFO (gage_no, coords, stream_segment, reach)
            if lines[0].find('"GAGE No.') >= 0:
                i = lines[0].find(":")
                gage_no = lines[0][:i].split()[-1].strip()
                for a in lines[0][i:-1].split(";"):
                    d = [x.strip() for x in a.split("=")]
                    if d[0].lower() == "K,I,J COORD.":
                        coords = [x.strip() for x in d[1].split(",")]
                    elif d[0].upper() == "STREAM SEGMENT":
                        stream_segment = d[1]
                    elif d[0].upper() == "REACH":
                        reach = d[1]
            else:
                raise Exception("Hader not found")

            #GET COLUMNS HEADER PROPERTY NAMES
            i == lines[1].find('"DATA:')
            if i >= 0:
                properties = [s.replace('"', '').lower() for s in lines[1][i - 1:].split()]
                try:
                    idx_v = properties.index(property.lower())
                    idx_t = properties.index("time")
                except:
                    ValueError("property value not found in file")
            else:
                raise Exception("Properties header not found")

            #LOAD SELECTED COLUMN INTO TS
            for l in range(2, len(lines)):
                data = lines[l].split()
                #time += timedelta(seconds=(float(data[idx_t]))) # incremental time
                time_ = time + timedelta(seconds=(float(data[idx_t])))
                self.ts.set_value(time_, ['data', 'quality'], [float(data[idx_v]), 0])

        self.__set_data_availability()

    def ts_from_hobfile(self, hobfile, startdate, hobname, disc, outhob=None, stat=None):
        """
            Load data from an hob file output from modflow

        Args:
            hobfile(str): a string path to a file of a MODFLOW HOB input file
            startdate(str): isodate starting date (e.g.: '2012-11-21T13:20:00+01:00')
            hobname(str): the name of the observation to be uploaded as defined in the file (e.g.: 'HOB1')
            disc(list): a list of stress period lengths (e.g.: [)
                        or a string path to a file of a MODFLOW discretization input file
            outhob(str): a string path to a file a MODFLOW HOB output file
                        (if specified simulated values are uploaded, if not specified observed values are used)
            stat(str): a string defining the STAT to be uploaded as quality value of the serie 'STATh' or 'STATdd'
                        (applies to MODFLOW-2000 files only)

        """

        #validating inputs

        #get start date
        ts_parse = oat_utils.get_startdate(startdate)

        #create first value and time series
        mdata = {
            'time': [],
            'data': [],
            'quality': []
        }
        self.ts = pd.DataFrame(mdata, index=mdata['time'], columns=['data', 'quality'])
        self.ts.index.name = 'time'

        set1 = None  # NH MOBS MAXM IUHOBSV HOBDRY
        set2 = None  # TOMULTH EVH
        set3 = None  # OBSNAM LAYER ROW COLUMN IREFSP TOFFSET ROFF COFF HOBS
        set4 = None  # MLAY, PR
        set5 = None  # ITT
        set6 = None  # OBSNAM IREFSP TOFFSET HOBS

        # Read the output HOB file
        #=============================
        outvals = {}
        if outhob:
            if not os.path.isfile(outhob):
                raise Exception("outhob file not found!")
            with open(outhob) as fpo:
                for line in fpo:
                    if not line[0] in ['"', '#']:
                        data = line.split()
                        outvals[data[2]] = data[0]

        # Read the discretization file
        #=============================
        if isinstance(disc, (list, tuple)):
            #list of SP length
            pass
        elif os.path.isfile(disc):
            #read discretization file
            PERLEN = oat_utils.read_dis(disc)
        else:
            raise Exception("disc must be a list of SP length or a file path to a discretization file")

        PERLEN.insert(0, 0)

        # Read the input HOB file and get observations
        # or simulated values if outhob is given
        #========================================
        with open(hobfile) as fp:
            lines = fp.readlines()

            #skip set0 & comments
            l = 1
            while lines[l][0] == "#":
                l += 1

            #get set1
            set1 = lines[l][:lines[l].find("#")].split()
            NH = int(float(set1[0]))
            MOBS = int(float(set1[1]))
            MAXM = int(float(set1[2]))
            IUHOBSV = int(float(set1[3]))
            HOBDRY = float(set1[4])
            if len(set1) == 6:
                NOPRINT = int(float(set1[5]))
            else:
                NOPRINT = None

            #skip comments
            l += 1
            while lines[l][0] == "#":
                l += 1

            #get set2
            set2 = lines[l][:lines[l].find("#")].split()
            TOMULTH = float(set2[0])
            if len(set2) == 2:
                EVH = float(set2[1])
            else:
                EVH = None

            #get bloks of set3, 4, 5 list of stress period lengths (e.g.: [)
            n = 0

            while n < NH:

                #print(n, l, NH, lines[l])

                OBSNAM = []
                LAYER = None
                ROW = None
                COLUMN = None
                IREFSP = None
                TOFFSET = None
                ROFF = None
                COFF = None
                HOBS = []
                STATISTIC = None
                STATFLAG = None
                PLOTSYMBOL = None
                MLAY = []
                PR = []

                l += 1
                while lines[l][0] == "#":
                    l += 1
                set3 = lines[l][:lines[l].find("#")].split()

                OBSNAM = set3[0]
                LAYER = int(float(set3[1]))
                ROW = int(float(set3[2]))
                COLUMN = int(float(set3[3]))
                IREFSP = int(float(set3[4]))
                ROFF = float(set3[6])
                COFF = float(set3[7])

                if IREFSP >= 0:
                    TOFFSET = float(set3[5])
                    HOBS = float(set3[8])
                    # this is valid for modflow 2000 only
                    #STATISTIC = set3[9]
                    #STATFLAG = int(float(set3[10]))
                    #PLOTSYMBOL = int(float(set3[11]))
                    sp_start_time = ts_parse + timedelta(seconds=sum(PERLEN[:int(IREFSP) - 1]))
                    isodate_str = sp_start_time + timedelta(seconds=(float(TOFFSET) * TOMULTH))

                    if outhob:
                        val = float(outvals[OBSNAM])
                        qual = 0.0
                    else:
                        val = float(HOBS)
                        qual = 0.0

                    self.ts.set_value(isodate_str, ['data', 'quality'], [val, qual])
                    n += 1

                if LAYER < 0:
                    #skip comments
                    l += 1
                    while lines[l][0] == "#":
                        l += 1
                    set4 = lines[l][:lines[l].find("#")].split()
                    for l in range(LAYER):
                        MLAY = int(float(set4[0::2]))
                        PR = float(set4[1::2])

                val = 0
                #n += 1
                if IREFSP < 0:
                    #print("IREFSP<0")
                    l += 1
                    while lines[l][0] == "#":
                        l += 1
                    set5 = lines[l][:lines[l].find("#")].split()
                    ITT = int(float(set5[0]))

                    PERLENTMP = PERLEN[1:]
                    for t in range(abs(IREFSP)):
                        l += 1
                        n += 1

                        if OBSNAM == hobname:
                            hob = lines[l][:lines[l].find("#")].split()
                            #TODO: check if it is seconds
                            sp_start_time = ts_parse + timedelta(seconds=sum(PERLENTMP[:int(hob[1]) - 1]))
                            isodate_str = sp_start_time + timedelta(seconds=(float(hob[2]) * TOMULTH))

                            if outhob:
                                if ITT == 2:
                                    val += float(outvals[hob[0]])
                                else:
                                    val = float(outvals[hob[0]])

                            else:
                                if ITT == 2:
                                    val += float(hob[3])
                                else:
                                    val = float(hob[3])

                            #TODO: only for modflow2000 (?)
                            if stat == "STATh":
                                qual = float(hob[4])
                            elif stat == "STATdd":
                                qual = float(hob[5])
                            else:
                                qual = 0.0

                            #TODO: add observation 'obs_index' & 'use' columns
                            self.ts.set_value(isodate_str, ['data', 'quality'], [val, qual])

        self.__set_data_availability()

    def ts_from_listfile(self, listfile, startdate=None, cum=False, prop='TOTAL', inout='IN'):
        """
            Load data from a listing file output of modflow model:

        Args:
            listfile(str): Either a string path to a file, URL (including http, ftp, and S3 locations), or any object with a read method
                            (such as an open file or StringIO)
            startdate(str): isodate starting date (e.g.: '2012-11-21T13:20:00+01:00')

            cum(bool): use cumulative volumes if True, use time step rates if False
            prop(str): the property to be read; one of 'STORAGE', 'CONSTANT HEAD', 'WELLS', 'RIVER LEAKAGE', 'TOTAL'
            inout(str): 'IN' or 'OUT' volumes

        """

        #validate inputs
        if not inout in ['IN', 'OUT']:
            raise Exception("'inut' input value is not correct")

        #define property in case of total
        if prop == 'TOTAL':
            prop = 'TOTAL %s' % inout

        #get start date
        from datetime import datetime, timedelta
        try:
            ts_parse = datetime.strptime(startdate, '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            try:
                import dateutil.parser
                ts_parse = dateutil.parser.parse(startdate).replace(tzinfo=None)
            except:
                raise Exception("startdate' input value is not correct")

        #create first value and time series
        mdata = {
            'time': [],
            'data': [],
            'quality': []
        }
        self.ts = pd.DataFrame(mdata, index=mdata['time'], columns=['data', 'quality'])
        self.ts.index.name = 'time'

        #assign loop variables
        #volume = 'VOLUMETRIC BUDGET FOR ENTIRE MODEL AT END OF TIME STEP'
        #stress = ", STRESS PERIOD"
        #time = 'TOTAL TIME'

        block_open = False
        inout_open = False
        val_found = False
        right_block = False

        #read files and extract values
        with open(listfile) as fp:
            for line in fp:

                if not right_block:
                    index = line.find('VOLUMETRIC BUDGET FOR ENTIRE MODEL AT END OF TIME STEP')

                    if index >= 0:
                        right_block = True
                    continue

                if not block_open:
                    #find volumetric budget block
                    split_col = line.find('RATES FOR THIS TIME STEP')

                    if split_col >= 0:
                        block_open = True
                        continue

                elif block_open and not inout_open:
                    if line.find(inout) >= 0:
                        inout_open = True
                        continue

                elif block_open and inout_open and not val_found:
                    if cum:
                        if line[:split_col].find(prop) >= 0:
                            val = float(line[:split_col].split('=')[1])
                            val_found = True
                            continue
                    else:
                        if line[split_col:].find(prop) >= 0:
                            val = float(line[split_col:].split('=')[1])
                            val_found = True
                            continue

                elif block_open and inout_open and val_found:
                    if line.find('TOTAL TIME') >= 0:
                        delta = int(float(line.strip().split()[2]))
                        #isodate_str = '%s' % (ts_parse + timedelta(seconds=delta))
                        isodate_str = ts_parse + timedelta(seconds=delta)

                        self.ts.set_value(isodate_str, ['data', 'quality'], [val, 0])

                        block_open = False
                        inout_open = False
                        val_found = False
                        right_block = False

        self.__set_data_availability()

    def ts_randn(self, start_time, lenght, frequency=None):
        """ populate time series with random values

        Args:
            start_time (str): starting timestamp of the time serie
            lenght (int): lenght of the time serie
            frequency (str): frequency of the time serie ('H','D','M','Y')
        """
        if frequency is None:
            frequency = self.freq
        if self.freq is None:
            frequency = 'D'
        rng = pd.date_range(start_time, periods=lenght, freq=frequency)
        #ts = pd.Series(np.random.randn(len(rng)), index=rng, name='data')
        ts = pd.DataFrame(np.random.randn(len(rng)), index=rng, columns=['data'])
        ts['quality'] = np.zeros(ts.size)
        self.ts = ts
        self.freq = frequency

    def ts_zeros(self, start_time, lenght, frequency=None):
        """ populate time series with zero (0) values

        Args:
            start_time (str): starting timestamp of the time serie
            lenght (int): lenght of the time serie
            frequency (str): frequency of the time serie ('H','D','M','Y')
        """
        if frequency is None:
            frequency = self.freq
        if self.freq is None:
            frequency = 'D'
        rng = pd.date_range(start_time, periods=lenght, freq=frequency)
        #ts = pd.Series(np.random.randn(len(rng)), index=rng, name='data')
        ts = pd.DataFrame(np.zeros(len(rng)), index=rng, columns=['data'])
        ts['quality'] = np.zeros(ts.size)
        self.ts = ts
        self.freq = frequency

    def ts_ones(self, start_time, lenght, frequency=None):
        """ populate time series with one (1) values

        Args:
            start_time (str): starting timestamp of the time serie
            lenght (int): lenght of the time serie
            frequency (str): frequency of the time serie ('H','D','M','Y')
        """
        if frequency is None:
            frequency = self.freq
        if self.freq is None:
            frequency = 'D'
        rng = pd.date_range(start_time, periods=lenght, freq=frequency)
        #ts = pd.Series(np.random.randn(len(rng)), index=rng, name='data')
        ts = pd.DataFrame(np.zeros(len(rng)), index=rng, columns=['data'])
        ts['quality'] = np.ones(ts.size)
        self.ts = ts
        self.freq = frequency

    def ts_const(self, value, start_time, lenght, frequency=None):
        """ populate time series with constant values

        Args:
            value (float): constant value to populate the time serie
            start_time (str): starting timestamp of the time serie
            lenght (int): lenght of the time serie
            frequency (str): frequency of the time serie ('H','D','M','Y')
        """
        if frequency is None:
            frequency = self.freq
        if self.freq is None:
            frequency = 'D'
        rng = pd.date_range(start_time, periods=lenght, freq=frequency)
        #ts = pd.Series(np.random.randn(len(rng)), index=rng, name='data')
        ts = pd.DataFrame(np.zeros(len(rng)), index=rng, columns=['data'])
        ts['quality'] = np.ones(ts.size) * value
        self.ts = ts
        self.freq = frequency

    #TODO----strat---
    def save_as_hobfile(self,set1,set2,):
        """ save a list of sensors as MODFLOW's HOB input file """
        pass
    #TODO----end---

    def save_to_sqlite(self, source, name=None, overwrite=False):
        """Save the oat object to sqlite

        Args:
            source (str): the sqlite file (including path)
            name (list): the sensor name to be used (it shall be unique)
        """
        try:
            from pyspatialite import dbapi2 as db
        except ImportError:
            raise ImportError('<pyspatialite> package not installed')

        #connect / create the DB
        con = db.connect(source)
        cur = con.cursor()

        if name is None:
            name = self.name

        #Check if DB is spatial otherwise enable it
        sql = "SELECT * FROM spatial_ref_sys;"
        try:
            res = cur.execute(sql).fetchone()
        except:
            cur.execute('SELECT InitSpatialMetadata(1)')

        #Check if table <freewat_sensors> already exists
        sql = "SELECT * FROM freewat_sensors;"
        try:
            res = cur.execute(sql).fetchone()
        except:
            #create spatial table for SENSORS if not exists
            sql = "CREATE TABLE IF NOT EXISTS freewat_sensors ("
            sql += "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
            sql += "name TEXT NOT NULL UNIQUE,"
            sql += "desc TEXT,"
            sql += "tz INTEGER,"
            sql += "unit TEXT NOT NULL,"
            sql += "prop TEXT NOT NULL,"
            sql += "freq TEXT,"
            # add time
            sql += "begin_pos DATETIME,"
            sql += "end_pos DATETIME,"
            #add statflag and use
            sql += "statflag TEXT,"
            sql += "use INTEGER DEFAULT 0,"
            sql += "topscreen REAL,"
            sql += "bottomscreen REAL,"
            sql += "altitude REAL )"
            res = cur.execute(sql).fetchall()
            #add geometry column
            sql = "SELECT AddGeometryColumn('freewat_sensors',"
            sql += "'geom', %s, 'POINT', 'XY')" % (self.srid)
            res = cur.execute(sql).fetchall()

        # check if altitude exists
        tmp = cur.execute('PRAGMA table_info(freewat_sensors)').fetchall()
        tmp_name = [i[1] for i in tmp]

        if 'altitude' in tmp_name:
            pass
        else:
            print("add missing table from save....")
            cur.execute('ALTER TABLE freewat_sensors ADD COLUMN altitude REAL')

        #check if sensor exists
        sql = "SELECT id FROM freewat_sensors WHERE name=?;"
        res_e = cur.execute(sql, (name, )).fetchall()

        if res_e and overwrite:
            #update sensor metadata
            print("sensor exists")
            sql = "UPDATE freewat_sensors"
            sql += " SET name=?,desc=?,tz=?,unit=?,prop=?,freq=?, geom=%s, begin_pos=?, end_pos=?, statflag=?, use=?, topscreen=?, bottomscreen=?,"
            sql += "altitude=? WHERE name=?"
            geom = "GeomFromText('POINT(%s %s)',%s)" % (self.lon, self.lat, self.srid)
            params = (name, self.desc, self.tz, self.unit,
                        self.prop, self.freq, self.data_availability[0],
                        self.data_availability[1], self.statflag, self.use, self.topscreen, self.bottomscreen, self.alt, name)
        elif not res_e:
            print("sensor NOT exists")
            #insert sensor metadata
            sql = "INSERT INTO freewat_sensors"
            sql += " (name, desc, tz, unit, prop, freq, geom, begin_pos, end_pos, statflag, use, topscreen, bottomscreen, altitude)"
            sql += " VALUES (?,?,?,?,?,?,%s,?,?,?,?,?,?,?)"
            geom = "GeomFromText('POINT(%s %s)',%s)" % (self.lon, self.lat, self.srid)
            params = (name, self.desc, self.tz, self.unit, self.prop, self.freq,
                    self.data_availability[0], self.data_availability[1], self.statflag, self.use, self.topscreen, self.bottomscreen, self.alt)
        else:
            raise IOError("<sensor '%s' already exists> set parameter 'overwrite=True' to allow overwrite" % name)

        #print(sql, params)
        cur.execute(sql % geom, params).fetchall()

        if not res_e:
            sql = "SELECT id FROM freewat_sensors WHERE name=?;"
            res_e = cur.execute(sql, (name, )).fetchall()

        # Add column use (at observation level)
        if not 'use' in self.ts.columns:
            self.ts['use'] = True

        # add column index if doeasn't exists
        if not 'obs_index' in self.ts.columns:
            idx_list = []
            for i in range(0, len(self.ts.index)):
                idx_list.append(self.name[0:3] + '_' + str(res_e[0][0]) + '_' + str(i + 1))

            self.ts['obs_index'] = idx_list

        #print (self.ts)
        self.ts.to_sql(name=name, con=con, if_exists='replace')

        print("table updated")
        cur.close()
        con.commit()
        con.close()

    def save_to_csv(self, filepath):
        """
        Write oat data to csv file

        Args:
            filepath (str): file path to save
        """

        if self.ts.empty:
            return

        self.ts.to_csv(filepath, columns=['data', 'quality', 'obs_index', 'use'])

    def delete_from_sqlite(self, source, name=None):
        """Delete the oat object from sqlite

        Args:
            source (str): the sqlite file (including path)
            name (list): the sensor name to be used
        """

        try:
            from pyspatialite import dbapi2 as db
        except ImportError:
            raise ImportError('<pyspatialite> package not installed')

        #connect / create the DB
        con = db.connect(source)
        cur = con.cursor()

        if name is None:
            name = self.name

        #check if sensor exists
        sql = "SELECT name FROM freewat_sensors WHERE name=?;"
        res = cur.execute(sql, (self.name,)).fetchall()

        if res:
            #delete the sensor metadata
            sql = "DELETE FROM freewat_sensors WHERE name=?;"
            res = cur.execute(sql, (self.name,)).fetchall()
            #delete the sensor data
            sql = "DROP TABLE %s ;" % (name)
            res = cur.execute(sql).fetchall()  # , (name,)
        else:
            raise ValueError("%s not found in db %s" % (name, source))

    def copy(self):
        """ Return a deep copy of the OAT object"""
        import copy
        return copy.deepcopy(self)

    def plot(self, data=True, quality=False, kind='line', data_color='b', axis=None, qaxis=None):
        """ plot function

        Args:
            data (bool): the sqlite file (including path)
            quality (bool): the sensor name to be used
            kind (str): kind of plot
            axis (): axis for data
            qaxis (): axis for quality plot

        """
        if not qaxis:
            qaxis = axis
        if data is True and quality is False:
            return self.ts['data'].plot(kind=kind, style=data_color, ax=axis)
        elif data is True and quality is True:
            self.ts['data'].plot(kind=kind, style=data_color, ax=axis)
            return self.ts['quality'].plot(kind=kind, style='r', ax=qaxis)
        elif data is False and quality is True:
            return self.ts['quality'].plot(kind=kind, style='r', ax=qaxis)
        else:
            raise Exception("data and quality cannot be both False")

    def process(self, method, detailedresult=False):
        """ Method to apply a method for processing
            by implementing the BEHAVIORAL VISITOR PATTERN
        """
        #verfy method is of type method
        return method.execute(self, detailedresult)

    def weight(self, method, detailedresult=False):
        """ Method to assign weights to observations
            by implementing the BEHAVIORAL VISITOR PATTERN
        """
        return method.execute(self, detailedresult)

    def period(self, astext=False):
        """ Method to extract the time series upper
            and lower time limits

            Args:
                astext (bool): define if outsput should be a tuple of datetime object or text
        """
        if astext:
            return ("%s" % self.ts.index.min(), "%s" % self.ts.index.max())
        else:
            return (self.ts.index.min(), self.ts.index.max())

    def set_data_availability(self):
        """
            ...
        """
        self.__set_data_availability()

    def __set_data_availability(self):
        """
            Method to set data availability when loading from istsos, hobfile, listfile and gagefile
        """
        if len(self.ts.index.values) > 0:
            begin = self.ts.index.values[0].astype('datetime64[s]')
            end = self.ts.index.values[-1].astype('datetime64[s]')

            self.data_availability = [str(begin), str(end)]