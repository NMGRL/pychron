
# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Str, Float, Bool, List
# from traitsui.api import View, Item
from pychron.monitors.monitor import Monitor
#============= standard library imports ========================
#============= local library imports  ==========================

class VacuumSection(HasTraits):
    gauge_controller = Str
    gauge_name = Str
    valve = Str
    pressure_trip = Float
    pressure_reset = Float
    tripped = Bool

class SystemMonitor(Monitor):
    analytical_sections = List
    def _load_hook(self, config):
        for section in config.sections():
            if section.startswith('VacuumSection'):
                g = self.config_get(config, section, 'gauge')
                if '.' in g:
                    gc, gn = g.split('.')
                else:
                    self.warning_dialog('Invalid Gauge identifier {}. Should be <GaugeController>.<GaugeName> e.g. Bone.IG'.format(g))
                    continue

                ds = self.config_get(config, section, 'disable_valves', default='')
                ds = ds.split(',')
                p = self.config_get(config, section, 'pressure_trip', cast='float', default=10)
                r = self.config_get(config, section, 'pressure_reset', cast='float', default=1e-10)
                if r > p:
                    self.warning_dialog('Invalid pressure_reset {}. Pressure_reset must be less than pressure_trip {}'.format(r, p))
                    continue

                a = VacuumSection(name=section,
                                  gauge_controller=gc,
                                  gauge_name=gn,
                                  disable_valves=ds,
                                  pressure_trip=p, pressure_reset=r)
                self.analytical_sections.append(a)
        return True

    def _fcheck_analytical_pressure(self):
        man = self.manager
        for section in self.analytical_sections:
            p = man.get_pressure(section.gauge_controller, section.gauge_name)
            if p > section.pressure_trip:
                for vi in section.disable_valves:
                    man.disable_valve(vi)
                section.tripped = True
            elif section.tripped:
                if p < section.pressure_reset:
                    for vi in section.disable_valves:
                        man.disable_valve(vi)
                    section.tripped = False

# ============= EOF =============================================

# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================



# '''
# @author: Jake Ross
# @copyright: 2009
# @license: Educational Community License 1.0
# '''
##=============enthought library imports=======================
# from traits.api import HasTraits, Instance, on_trait_change, Any, Str, Int, Float, Button, List, Bool
# from traitsui.api import View, Item, Group, HGroup, VGroup, ListStrEditor
# from pyface.api import warning, information, confirm
# from pyface.api import ProgressDialog
##=============standard library imports ========================
# import time
# import datetime
# #from thread import *
# from threading import Thread
# import logging
##=============local library imports  ==========================
# #from globals import ghome, gpressuredelay
# #from filetools import parse_setupfile
# #from logger_setup import add_console
#
#
# class ErrorDurationThread(Thread):
#    def run(self):
#        '''
#        '''
#        parent = self.parent
#        name = self.name
#        for i in range(self.delay * 10):
#            if parent.gauge_thread_map[name] is None:
#                break
#            time.sleep(.1)
#        else:
#            parent.error('Pressure has not changed for %i sec' % self.delay, name, requery = True)
# class ErrorThread(Thread):
#    def run(self):
#        '''
#        '''
#        delay = self.delay * 10
#        parent = self.parent
#        for i in range(delay):
#            if parent.error_handled:
#                break
#            time.sleep(.1)
#
#           # w.Close()
#
#        else:
#            parent.raise_unhandled_error()
#            #w=wx.GetApp().GetTopWindow()
#           # w.Close()
#            #w.DestroyChildren()
#            #print 'find',w.FindWindowById(0)
#            #print 'window',w
#
# def point_generator():
#    '''
#    '''
#    i = 0
#    while 1:
#        if i < 100:
#            p = (i, i)
#        elif i >= 100 and i < 200:
#            p = (i, 200 - i)
#        elif i >= 200:
#            p = (400 - i, 0)
#        else:
#            i = 0
#        yield(p)
#        i += 1
# point_gen = point_generator()
# class WindowMoveThread(Thread):
#
#    def run(self):
#        '''
#        '''
#        i = 0
#        while not self.parent.error_handled:
#            w = wx.GetApp().GetTopWindow()
#            p = point_gen.next()
#           # print p
#            w.Move(p)
#
#            time.sleep(0.1)
#
# class SystemMonitor(HasTraits):
#    '''
#    Monitors the system and takes action if there is a problem
#
#    G{classtree}
#    '''
#    errors = List()
#    open = False
#    test = Button
#    error_event = Bool(False)
#    gauge_manager = Instance(GaugeManager)
#
#
#    def __init__(self):
#        '''
#        '''
#
#        self.logger = logging.getLogger('SystemMonitor')
#        add_console(self.logger)
#
#        self.criteria_map = c = {}
#        self.gauge_thread_map = {}
#        self._load_criteria_map()
#        self._load_thread_map()
#
#        self.actuator = AgilentGPActuator(name = 'SystemMonitorActuator')
#    def traits_view(self):
#        '''
#        '''
#        v = View(Item('test'),
#               Item('errors', show_label = False,
#                    editor = ListStrEditor()),
#               height = 200,
#               width = 200,
#               resizable = True)
#        return v
#
#    def _load_criteria_map(self, setup_file = None):
#        '''
#        load the setup file and parse in the criteria. create a dictionary of criteria C{self.criteria_map}
#
#        B{Example System Monitor setupfile}::
#            #gauge name, criterion
#            gauge0,>50
#            gauge1,>50
#            gauge2,>50
#
#        the system monitor with trip when are gauge pressure exceeds (or the opposite of exceeds) the criterion.
#
#        @note: there is no established opposite of exceeds
#
#        @type setup_file: C{str}
#        @param setup_file: absolute path of the setup file
#        '''
#
#
#        c = self.criteria_map
#        if setup_file is None:
#            setup_file = ghome + '/setupfiles/system_monitor.txt'
#
#        f = parse_setupfile(setup_file)
#
#        for g in f:
#            tf = g[1][:1]
#            if tf == '<':
#                tf = False
#            else:
#                tf = True
#            n = g[1][1:]
#            c[g[0]] = [tf, float(n)]
#    def _load_thread_map(self):
#        '''
#        for each criterion create a empty dictionary entry
#        '''
#        tm = self.gauge_thread_map
#        for i in self.criteria_map:
#            tm[i] = None
#    def _pressure_changed(self, object, name, old, new):
#        '''
#        Handler for changes to any of the C{GaugeManager}'s gauges pressures
#
#        @type object: C{BaseGauge}
#        @param object: a gauge object
#        @type name: C{str}
#        @param name: trait name
#        @type old: C{str}
#        @param old: the previous value
#        @type new: C{str}
#        @param new: the new value
#        '''
#        n, f = new.split(',')
#        gauge = object.get_gauge_by_name(n)
#
#        #print 'pressure',gauge.pressure
#        if self.check_pressure(gauge):
#           self.check_pressure_duration(gauge)
#
#    def record_error(self, msg):
#        '''
#        record an error
#
#        @type msg: C{str}
#        @param msg: an error message
#        '''
#
#        ts = (datetime.datetime.today()).ctime()
#        msg = ts.join(msg)
#        self.errors.append(msg)
#        self.logger.warning(msg)
#
#    def raise_unhandled_error(self):
#        '''
#        '''
#        print 'system monitor is taking action for error'
#        self.power_cycle()
#    def _power_cycle(self):
#        '''
#
#        '''
#        self.actuator.open('103')
#        time.sleep(1)
#        self.actuator.close('103')
#        #information(None,'d')
#        #confirm(None,'fffffasd')
#    def error(self, m, n, requery = False):
#        '''
#            @type m: C{str}
#            @param m:
#
#            @type n: C{str}
#            @param n:
#
#            @type requery: C{str}
#            @param requery:
#        '''
#        self.error_handled = False
#       # print 'error 1'
#       # self.error_event=not self.error_event
#       # print 'error 2'
#       #start a window move thread
#        mw = WindowMoveThread()
#        mw.parent = self
#        mw.start()
#        #start error thread
#        t = ErrorThread()
#        t.parent = self
#        t.delay = 30
#        t.start()
#
#        #log the error
#        self.record_error(m)
#
#        #show a warning
#       # confirm(w,m,cancel=True)
#        m += '\nHit OK Cancel System Monitor action'
#        warning(None, m)
#
#
#        #user says ok
#        self.error_handled = True
#        if requery:
#          #  print 'requerying'
#            g = self.gauge_manager.get_gauge_by_name(n)
#            p = n + ',%f' % g.pressure
#            self.gauge_thread_map[n] = None
#            self._pressure_changed(self.gauge_manager, '', '', p)
#
#
#    def check_pressure_duration(self, gauge):
#        '''
#            @type gauge: C{str}
#            @param gauge:
#        '''
#        threadid = self.gauge_thread_map[gauge.name]
#
#        if threadid == None:
#            e = ErrorDurationThread()
#            e.parent = self
#            e.name = gauge.name
#            e.delay = gpressuredelay
#            self.gauge_thread_map[gauge.name] = e
#            e.start()
#        else:
#            self.gauge_thread_map[gauge.name] = None
#
#
#    def check_pressure(self, gauge):
#        '''
#            @type gauge: C{str}
#            @param gauge:
#        '''
#        tpressure = self.criteria_map[gauge.name][1]
#        greater = self.criteria_map[gauge.name][0]
#        if greater:
#            test = lambda p, t: p > t
#        else:
#            test = lambda p, t: p < t
#
#        if test(gauge.pressure, tpressure):
#            m = 'The pressure %s has exceeded set point' % gauge.pressure
#            self.error(m, gauge.name)
#            return False
#        else:
#            return True
