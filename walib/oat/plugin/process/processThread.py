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
# from PyQt4.QtCore import *
from PyQt4.QtCore import QObject, QThread, Qt, pyqtSignal

from oat.oatlib import method


class Thread(QThread):

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

     # this class is solely needed for these two methods, there
     # appears to be a bug in PyQt 4.6 that requires you to
     # explicitly call run and start from the subclass in order
     # to get the thread to actually start an event loop

    def start(self):
        QThread.start(self)

    def run(self):
        QThread.run(self)


class BaseThread(QObject):
    """
        Base thread for method execution

        All the method are executed in a background thread, to prevent the gui to freeze
    """
    def __init__(self, gui):
        super(BaseThread, self).__init__()
        self.result = None
        self.gui = gui
        self.history = {
            "process": "",
            "params": {}
        }

    end = pyqtSignal(dict, dict)
    exception = pyqtSignal(Exception)
    debug = pyqtSignal(str)


class StatisticsThread(BaseThread):
    """
        Execute hydro graph separator
    """
    def __init__(self, gui):
        super(StatisticsThread, self).__init__(gui)
        self.history['process'] = "Statistics"

    def run(self):
        try:
            data = self.gui.statisticsData.isChecked()
            quality = self.gui.statisticsQuality.isChecked()

            tbounds = [None, None]
            if self.gui.statisticsTime.isChecked():
                timezone = self.gui.statisticsTz.value()
                if timezone >= 0:
                    timez = "+" + "%02d:00" % (timezone)
                else:
                    timez = "-" + "%02d:00" % (abs(timezone))

                begin_pos = self.gui.statisticsBegin.text() + timez
                end_pos = self.gui.statisticsEnd.text() + timez

                tbounds = [begin_pos, end_pos]

            self.history['params']['data'] = data
            self.history['params']['quality'] = quality
            self.history['params']['tbounds'] = tbounds

            self.result = self.gui.oat.process(method.Statistics(data=data, quality=quality, tbounds=tbounds),
                                               detailedresult=True)

            self.end.emit(self.result, self.history)
        except Exception as e:
            self.exception.emit(e)


class HydroGraphSepThread(BaseThread):
    """
        Execute hydro graph separator
    """
    def __init__(self, gui):
        super(HydroGraphSepThread, self).__init__(gui)
        self.history['process'] = "HydroGraphSeparation"

    def run(self):
        try:
            mode = self.gui.hydrosepMode.currentText()
            alpha = self.gui.hydrosepAlpha.value()
            bfl = self.gui.hydrosepBfl.value()

            self.history['params']['mode'] = mode
            self.history['params']['alpha'] = alpha
            self.history['params']['bfl'] = bfl

            self.debug.emit('Start processing...')

            if 'use' in self.gui.oat.ts.columns:
                del self.gui.oat.ts['use']
            self.result = self.gui.oat.process(method.HydroGraphSep(mode, alpha=alpha, bfl_max=bfl),
                                               detailedresult=True)

            self.debug.emit("processing end")

            self.end.emit(self.result, self.history)
        except Exception as e:
            self.exception.emit(e)


class DigitalThread(BaseThread):
    """
        Execute digital filter (?)
    """
    def __init__(self, gui):
        super(DigitalThread, self).__init__(gui)
        self.history['process'] = "DigitalFitler"

    def run(self):
        try:
            highcut = self.gui.highcut.value()
            lowcut = self.gui.lowcut.value()
            order = self.gui.order.value()
            filter_type = self.gui.filterType.currentText()

            if highcut == 0:
                self.exception.emit(Exception('high cutoff freq must be > 0.0'))
                return

            self.history['params']['highcut'] = highcut
            self.history['params']['lowcut'] = lowcut
            self.history['params']['order'] = order
            self.history['params']['filter_type'] = filter_type

            self.result = self.gui.oat.process(method.DigitalFilter(lowcut, highcut, order=order, btype=filter_type),
                                               detailedresult=True)

            self.end.emit(self.result, self.history)

        except Exception as e:
            self.exception.emit(e)


class ExceedanceThread(BaseThread):
    """
        Run exceedance filter
    """
    def __init__(self, gui):
        super(ExceedanceThread, self).__init__(gui)
        self.history['process'] = "Exceedance"

    def run(self):
        try:
            val = self.gui.exeValues.text()
            if len(val) != 0:
                values = map(float, val.split(','))
            else:
                values = None

            perc = self.gui.exePerc.text()

            if len(perc) != 0:
                perc = map(float, perc.split(','))
            else:
                perc = None

            etu = self.gui.exeEtu.currentText()
            under = self.gui.exeUnder.isChecked()

            self.history['params']['percentage'] = perc
            self.history['params']['values'] = values
            self.history['params']['etu'] = etu
            self.history['params']['under'] = under

            self.result = self.gui.oat.process(method.Exceedance(perc=perc, values=values, etu=etu, under=under),
                                               detailedresult=True)

            self.end.emit(self.result, self.history)
        except Exception as e:
            self.exception.emit(e)


class HydroEventsThread(BaseThread):
    """
        Run Hydro events filter

        calculate portion of time series associated with peak flow events

    """
    def __init__(self, gui):
        super(HydroEventsThread, self).__init__(gui)
        self.history['process'] = "HydroEvents"

    def run(self):
        try:
            rise = self.gui.hEvtRise.value()
            fall = self.gui.hEvtFall.value()
            window = self.gui.hEvtWindow.value()
            peak = self.gui.hEvtPeak.value()
            suffix = self.gui.hEvtSuffix.text()

            period = None
            if self.gui.hEvtTime.checkState() == Qt.Checked:

                begin = self.gui.hEvtBegin.text().replace(" ", "T")
                end = self.gui.hEvtEnd.text().replace(" ", "T")

                period = [begin, end]

            if suffix == "":
                suffix = "_event_N"

            self.history['params']['rise_lag'] = rise
            self.history['params']['fall_lag'] = fall
            self.history['params']['window'] = window
            self.history['params']['min_peak'] = peak
            self.history['params']['suffix'] = suffix
            self.history['params']['period'] = period

            self.result = self.gui.oat.process(method.HydroEvents(rise_lag=rise, fall_lag=fall, window=window,
                                                                  min_peak=peak, suffix=suffix, period=period),
                                               detailedresult=True)

            self.end.emit(self.result, self.history)
        except Exception as e:
            self.exception.emit(e)


class HydroIndicesThread(BaseThread):
    """
        Run Hydro indices filter
    """
    def __init__(self, gui):
        super(HydroIndicesThread, self).__init__(gui)
        self.history['process'] = "HydoIndices"

    def run(self):

        try:
            htype = self.gui.hIndexType.currentText()

            if htype != 'MA':
                self.exception.emit(Exception("Sorry, only Ma is supported (Alphanumeric Code)"))
                return

            if self.gui.hIndexCode.text() == '':
                self.exception.emit(Exception("Please define code"))
                return

            code = map(int, self.gui.hIndexCode.text().split(','))

            if len(code) != 2:
                self.exception.emit(Exception("Please change code"))
                return
            elif code[0] > code[1]:
                self.exception.emit(Exception('code 1 must be lower than code 2'))
                return
            elif code[0] < 1:
                self.exception.emit(Exception("Code 1 shoul'd be >= 1"))
                return
            elif code[1] > 45:
                self.exception.emit(Exception("Code 2 shoul'd be <= 45"))
                return

            comp = self.gui.hIndexComponent.currentText()
            classification = self.gui.hIndexClassification.currentText()
            median = self.gui.hIndexMedian.isChecked()
            drain = self.gui.hIndexDrain.value()

            period = None
            if self.gui.hIndexTime.checkState() == Qt.Checked:
                begin = self.gui.hIndexBegin.text().replace(" ", "T")
                end = self.gui.hIndexEnd.text().replace(" ", "T")

                period = [begin, end]

            self.result = {
                "op": "hydroIndices",
                "type": "dict list",
                "data": []
            }

            self.history['params']['htype'] = htype
            self.history['params']['code'] = code
            self.history['params']['flow_component'] = comp
            self.history['params']['stream_classification'] = classification
            self.history['params']['median'] = median
            self.history['params']['drain_area'] = drain
            self.history['params']['period'] = period

            self.debug.emit(str(self.history))

            for c in range(code[0], code[1]):
                self.debug.emit(str(c))
                result = self.gui.oat.process(method.HydroIndices(htype=htype, code=c, flow_component=comp,
                                                                  stream_classification=classification, median=median,
                                                                  drain_area=drain, period=period), detailedresult=True)
                self.debug.emit(str(result))
                self.result['data'].append({"index": c, "value": result['data']})

            self.end.emit(self.result, self.history)
        except Exception as e:
            self.exception.emit(e)


class ResampleThread(BaseThread):
    """
        Run resample method
    """
    def __init__(self, gui):
        super(ResampleThread, self).__init__(gui)
        self.history['process'] = "Resample"

    def run(self):
        try:
            freq = self.gui.resampleFreq.text()
            how = self.gui.resampleHow.currentText()
            fill = self.gui.resampleFill.currentText()

            if fill == '':
                fill = None

            limit = self.gui.resampleLimit.value()
            if limit == -1:
                limit = None

            quality = self.gui.resampleQual.currentText()

            self.history['params']['frequency'] = freq
            self.history['params']['how'] = how
            self.history['params']['fill'] = fill
            self.history['params']['limit'] = limit
            self.history['params']['how_quality'] = quality

            self.result = self.gui.oat.process(method.Resample(freq=freq, how=how, fill=fill, limit=limit,
                                                               how_quality=quality), detailedresult=True)

            self.end.emit(self.result, self.history)
        except Exception as e:
            self.exception.emit(e)


class QualityStatThread(BaseThread):
    """
        Run quality Stat method
    """
    def __init__(self, gui):
        super(QualityStatThread, self).__init__(gui)
        self.history['process'] = "QualityStat"

    def run(self):
        try:
            value = self.gui.qualityValue.value()
            stat = self.gui.qualityStat.currentText()

            tbounds = [(None, None)]
            vbounds = [(None, None)]
            if self.gui.qualityTime.isChecked():
                timezone = self.gui.qualityTz.value()
                if timezone >= 0:
                    timez = "+" + "%02d:00" % (timezone)
                else:
                    timez = "-" + "%02d:00" % (abs(timezone))

                begin_pos = self.gui.qualityBegin.text() + timez
                end_pos = self.gui.qualityEnd.text() + timez

                tbounds = [(begin_pos, end_pos)]

            if self.gui.qualityUseval.isChecked():
                min_val = self.gui.qualityLow.value()
                max_val = self.gui.qualityHigh.value()
                vbounds = [(min_val, max_val)]

            self.history['params']['value'] = value
            self.history['params']['vbounds'] = vbounds
            self.history['params']['tbounds'] = tbounds
            self.history['params']['statflag'] = stat

            self.result = self.gui.oat.process(method.SetQualityStat(value=value, vbounds=vbounds, tbounds=tbounds,
                                                                     statflag=stat), detailedresult=True)

            self.end.emit(self.result, self.history)
        except Exception as e:
            self.exception.emit(e)


class DataValuesThread(BaseThread):
    """
        Run data values method
    """
    def __init__(self, gui):
        super(DataValuesThread, self).__init__(gui)
        self.history['process'] = "DataValues"

    def run(self):
        try:
            value = self.gui.dvalueValue.value()

            tbounds = [(None, None)]
            vbounds = [(None, None)]
            if self.gui.dvalueTime.isChecked():
                timezone = self.gui.dvalueTz.value()
                if timezone >= 0:
                    timez = "+" + "%02d:00" % (timezone)
                else:
                    timez = "-" + "%02d:00" % (abs(timezone))

                begin_pos = self.gui.dvalueBegin.text() + timez
                end_pos = self.gui.dvalueEnd.text() + timez

                tbounds = [(begin_pos, end_pos)]

            if self.gui.dvalueUse.isChecked():
                min_val = self.gui.dvalueLow.value()
                max_val = self.gui.dvalueHigh.value()
                vbounds = [(min_val, max_val)]

            self.history['params']['value'] = value
            self.history['params']['vbounds'] = vbounds
            self.history['params']['tbounds'] = tbounds

            self.result = self.gui.oat.process(method.SetDataValues(value=value, vbounds=vbounds, tbounds=tbounds),
                                               detailedresult=True)

            self.end.emit(self.result, self.history)
        except Exception as e:
            self.exception.emit(e)


class IntegrateThread(BaseThread):
    """
        Run integrate filter
    """
    def __init__(self, gui):
        super(IntegrateThread, self).__init__(gui)
        self.history['process'] = "Integrate"

    def run(self):

        try:
            tunit = self.gui.intUnit.currentText()
            factor = self.gui.intFactor.value()
            how = self.gui.intHow.currentText()
            astext = self.gui.intText.isChecked()

            period = [(None, None)]
            if self.gui.intTime.isChecked():
                timezone = self.gui.intTz.value()
                if timezone >= 0:
                    timez = "+" + "%02d:00" % (timezone)
                else:
                    timez = "-" + "%02d:00" % (abs(timezone))

                begin_pos = self.gui.intBegin.text() + timez
                end_pos = self.gui.intEnd.text() + timez

                period = [(begin_pos, end_pos)]

            self.history['params']['periods'] = period
            self.history['params']['tunit'] = tunit
            self.history['params']['factor'] = factor
            self.history['params']['how'] = how
            self.history['params']['astext'] = astext

            self.result = self.gui.oat.process(method.Integrate(periods=period, tunit=tunit, factor=factor, how=how,
                                                                astext=astext), detailedresult=True)

            self.end.emit(self.result, self.history)

        except Exception as e:
            self.exception.emit(e)


class CompareThread(BaseThread):
    """
        Run compare filter
    """
    def __init__(self, gui):
        super(CompareThread, self).__init__(gui)
        self.history['process'] = "Compare"

    def run(self):

        try:
            stats = []

            if self.gui.compareBias.isChecked():
                stats.append('BIAS')
            if self.gui.compareError.isChecked():
                stats.append('STANDARD_ERROR')
            if self.gui.compareRel.isChecked():
                stats.append('RELATIVE_BIAS')
            if self.gui.compareRelStd.isChecked():
                stats.append('RELATIVE_STANDARD_ERROR')
            if self.gui.compareNash.isChecked():
                stats.append('NASH_SUTCLIFFE')
            if self.gui.compareCoeff.isChecked():
                stats.append('COEFFICIENT_OF_EFFICIENCY')
            if self.gui.compareIndex.isChecked():
                stats.append('INDEX_OF_AGREEMENT')
            if self.gui.compareVol.isChecked():
                stats.append('VOLUMETRIC_EFFICIENCY')

            exponent = self.gui.compareExponent.value()
            sensor_name = self.gui.compareSensor.currentText()
            compare_sensor = self.gui.get_sensor_from_db(sensor_name)

            align = self.gui.compareAlign.isChecked()

            self.history['params']['stats'] = stats
            self.history['params']['compare_sensor'] = sensor_name
            self.history['params']['exponent'] = exponent
            self.history['params']['align'] = align

            self.result = self.gui.oat.process(method.Compare(compare_sensor, stats, exponent, align),
                                               detailedresult=True)

            self.end.emit(self.result, self.history)

        except Exception as e:
            self.exception.emit(e)


class SubtractThread(BaseThread):
    """
        Run subtract method
    """
    def __init__(self, gui):
        super(SubtractThread, self).__init__(gui)
        self.history['process'] = "Subtract"

    def run(self):
        try:
            sens_name = self.gui.subSensor.currentText()
            align = self.gui.subMethod.currentText()

            if not self.gui.oat.freq:
                e = Exception("Please define sensor freq before run this method")
                self.exception.emit(e)
                return

            if sens_name == '':
                e = Exception("Please define a valid sensor name")
                self.exception.emit(e)
                return

            sens = self.gui.get_sensor_from_db(sens_name)

            self.history['params']['sensor'] = sens_name
            self.history['params']['align_method'] = align
            self.result = self.gui.oat.process(method.Subtract(sensor=sens, align_method=align), detailedresult=True)

            self.end.emit(self.result, self.history)

        except Exception as e:
            self.exception.emit(e)


class FillThread(BaseThread):
    """
        Run Fill method
    """
    def __init__(self, gui):
        super(FillThread, self).__init__(gui)
        self.history['process'] = "Fill"

    def run(self):
        try:
            fill = self.gui.fillBox.currentText()
            limit = self.gui.fillLimit.value()

            self.history['params']['fill'] = fill
            self.history['params']['limit'] = limit
            self.result = self.gui.oat.process(method.Fill(fill=fill, limit=limit), detailedresult=True)

            self.end.emit(self.result, self.history)

        except Exception as e:
            self.exception.emit(e)


class HargreavesEToThread(BaseThread):
    """
        Run HargreavesETo method
    """
    def __init__(self, gui):
        super(HargreavesEToThread, self).__init__(gui)
        self.history['process'] = "HargreavesETo"

    def run(self):
        try:

            self.result = self.gui.oat.process(method.HargreavesETo(), detailedresult=True)
            self.end.emit(self.result, self.history)

        except Exception as e:
            self.exception.emit(e)
