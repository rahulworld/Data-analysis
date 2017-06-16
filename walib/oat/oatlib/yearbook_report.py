# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import pandas as pd
import numpy as np
import datetime as dt


class prec_repo():
    """ """

    def __init_info__(self):
        """ initialize info """
        self.info = {
            "name": None,
            "no": None,
            "coordinates": None,
            "altitude": None,
            "bacino": None
            }

    def __init_cy_daily_data__(self):
        """ initialize current year daily_data """
        self.cy_daily_data = [[] for x in range(12)]

    def __init_cy_monthly_stats__(self):
        """ initialize cy_monthly_stats """
        self.cy_monthly_stats = {
            "sum": [None for x in range(12)],
            "max": [(None, None) for x in range(12)],
            "rainy_days": [None for x in range(12)],
            }

    def __init_cy_yearly_stats__(self):
        """ initialize cy_yearly_stats """
        self.cy_yearly_stats = {
            "sum": None,
            "rainy_days": None
            }

    def __init_monthly_stats__(self):
        """ initialize monthly_stats """
        self.monthly_stats = {
            "mean": [None for x in range(12)],
            "max_mon": [(None, None) for x in range(12)],
            "min_mon": [(None, None) for x in range(12)],
            "max_day": [(None, None) for x in range(12)],
            "max_rainy_days": [(None, None) for x in range(12)],
            "min_rainy_days": [(None, None) for x in range(12)],
            "mean_rainy_days": [None for x in range(12)],
            }

    def __init_yearly_stats__(self):
        """ initialize yearly stats """
        self.yearly_stats = {
            "mean": None,
            "rainy_days": None
            }

    def __init__(self):
        """ """
        self.__init_info__()
        self.__init_cy_daily_data__()
        self.__init_cy_monthly_stats__()
        self.__init_cy_yearly_stats__()
        self.__init_monthly_stats__()
        self.__init_yearly_stats__()

    def __repr__(self):
        """ """
        rep = "info: %s\n" % self.info
        rep += "cy_daily_data: %s\n" % self.cy_daily_data
        rep += "cy_monthly_stats: %s\n" % self.cy_monthly_stats
        rep += "cy_yearly_stats: %s\n" % self.cy_yearly_stats
        rep += "monthly_stats: %s\n" % self.monthly_stats
        rep += "yearly_stats: %s\n" % self.yearly_stats
        return rep

    def set_info(self, oat, no=None, bacino=None):
        """ set basic info """
        self.info["name"] = oat.desc
        self.info["coordinates"] = "%s / %s" % (oat.lat, oat.lon)
        self.info["altitude"] = oat.alt
        if bacino:
            self.info["bacino"] = bacino
        if no:
            self.info["no"] = no

    def set_cy_daily_data(self, oat, year):
        """ set daily data """
        self.__init_cy_daily_data__()
        year = str(year)
        for index, row in oat.ts[year].iterrows():
            try:
                #print(index.month, index.day, row['data'])
                self.cy_daily_data[index.month - 1].append(
                    float("%.2f" % row['data'])
                    )
            except:
                print(index.month, index.day)

    def set_cy_monthly_stats(self, oat, year):
        """ set current year monthly stats """
        self.__init_cy_monthly_stats__()
        for m in range(12):
            t = "%s-%02d" % (year, m + 1)
            mm = oat.ts[t]
            ms = mm['data'].sum()
            mx = mm['data'].max()
            self.cy_monthly_stats["sum"][m] = float("%.2f" % ms)
            self.cy_monthly_stats["max"][m] = (
                float("%.2f" % mx),
                ", ".join([str(i) for i in mm[mm['data'] == mx].index.day])
            )
            self.cy_monthly_stats["rainy_days"][m] = mm[mm['data'] > 0.2]['data'].count()
            #self.cy_monthly_stats["rainy_days"][m] = oat.ts[t][oat.ts['data'] > 0.2]['data'].count()

    def set_cy_yearly_stats(self, oat, year):
        """ set current year yearly stats """
        self.__init_cy_yearly_stats__()
        year = str(year)
        self.cy_yearly_stats["sum"] = float("%.2f" % oat.ts[year]['data'].sum())
        self.cy_yearly_stats["rainy_days"] = oat.ts[year][oat.ts['data'] > 0.2]['data'].count()

    def set_monthly_stats(self, oat):
        """ set historic monthly stats """
        self.__init_monthly_stats__()
        #years = range(oat.period()[0].year, oat.period()[1].year)
        toat = oat.copy()
        toat.ts['year'] = toat.ts.index.year
        toat.ts['month'] = toat.ts.index.month
        self.monthly_stats["from"] = dt.datetime.strptime(toat.data_availability[0], "%Y-%m-%dT%H:%M:%S.%fZ").year
        self.monthly_stats["to"] = dt.datetime.strptime(toat.data_availability[1], "%Y-%m-%dT%H:%M:%S.%fZ").year

        ##aggregate monthly with sum
        #from methods import method
        #oatM = oat.process(method.Resample(freq='1M',how='sum'))

        #precipitation monthly mean
        for m in range(12):
            self.monthly_stats["mean"][m] = float("%.2f" % toat.ts[toat.ts['month'] == m + 1].groupby('year').sum()['data'].mean())

        #precipitation max montly
        for m in range(12):
            #somma di quel mese negli anni
            mm = toat.ts[toat.ts['month'] == m + 1]
            grouper = mm.groupby('year').sum()
            tm = grouper['data'].min()
            tmx = grouper['data'].max()

            #max monthly prec
            self.monthly_stats["max_mon"][m] = (
                float("%.2f" % tmx),
                ", ".join([str(i) for i in grouper[grouper['data'] == tmx].index.values])
                )

            #min monthly prec
            self.monthly_stats["min_mon"][m] = (
                float("%.2f" % tm),
                ", ".join([str(i) for i in grouper[grouper['data'] == tm].index.values])
                )

            #max daily prec
            mmax = mm['data'].max()
            self.monthly_stats["max_day"][m] = (
                float("%.2f" % mmax),
                ", ".join(["%s %s" % (i.day, i.year) for i in mm[mm['data'] == mmax].index])
            )

            #calculate time series of days with prec
            grouper2 = mm[(mm['data'] > 0.2)].groupby('year').count()
            grouper2.index = [dt.datetime(d, m + 1, 1) for d in grouper2.index]
            grouper = grouper2.resample('A', how='max').fillna(0)

            #max num day with prec
            mmax = grouper['data'].max()
            self.monthly_stats["max_rainy_days"][m] = (
                float("%.2f" % mmax),
                ", ".join([str(i) for i in grouper[grouper['data'] == mmax].index.year])
                )

            #min num day with prec
            mmin = grouper['data'].min()
            #if m != 12:
                #print(m)
                #pd.set_option('display.max_rows', len(grouper2))
                #print(grouper2)
                #pd.reset_option('display.max_rows')
                #print(mmin, grouper2[grouper2['data'] == mmin].index.year)
            #print("*********")
            self.monthly_stats["min_rainy_days"][m] = (
                float("%.2f" % mmin),
                ", ".join([str(i) for i in grouper[grouper['data'] == mmin].index.year])
                )

            #mean num day with prec
            mmean = grouper['data'].mean()
            self.monthly_stats["mean_rainy_days"][m] = float("%.2f" % mmean)

    def set_yearly_stats(self, oat):
        """ set yearly stats """
        self.__init_yearly_stats__()
        toat = oat.copy()
        toat.ts['year'] = toat.ts.index.year
        #grouper = mm.groupby('year')

        #precipitation yearly mean
        self.yearly_stats["mean"] = float("%.2f" % toat.ts.groupby('year').sum()['data'].mean())
        self.yearly_stats["rainy_days"] = float("%.2f" % toat.ts[toat.ts['data'] > 0.2].groupby('year').count()['data'].mean())
