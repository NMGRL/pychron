#===============================================================================
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
#===============================================================================



'''
@author: Jake Ross
@copyright: 2009
@license: Educational Community License 1.0
'''
#=============enthought library imports=======================
from traits.api import List, Str, Bool, Float, Int
from traitsui.api import View, Item, ListEditor
#=============standard library imports ========================

# from numpy import random
import time
#=============local library imports  ==========================
from setpoint import Setpoint

from pychron.hardware.core.core_device import CoreDevice

class BaseGauge(CoreDevice):
    '''
        This is the virtual representation of a MKS Gauge
        
        G{classtree}
    '''

    description = Str
    state = Bool
    # show_data = Bool

    pressure = Float
    identify = Bool(False)

    indicator = Bool
    delay_after_power_on = Bool(False)

    # setpoints = Float
    # etpoint_enabled=Bool
    nsetpoints = Int(3)
    setpoints = List(Setpoint)

    error = Int


    def initialize(self, *args, **kw):
        '''
        '''
        self.load_setpoints()
        return True

    def load_setpoints(self):
        '''
        '''
        for i in range(self.nsetpoints):
            s = Setpoint(parent=self,
                       index=i + 1)
            s.load()
            self.setpoints.append(s)


        # self.write(q)


    def get_transducer_pressure(self, retry=5, verbose=False):
        '''
        gets the pressure from the transducer
            
            
            @see: L{GaugeManager}
            
        '''
#        if self.simulation:
#            self.pressure = random.randint(10)
#            return

        if not self.state:
            return

        if self.delay_after_power_on:
            self.delay_after_power_on = False
            return

        def read(q):
            p = self._parse_response('pressure', self.ask(q,
                                                      verbose=verbose,
                                                      # delay = 125
                                                      )
                                )
            if isinstance(p, float):
                return True, p


        q = self._build_query(self.address, 'pressure')
        read_success = False
        if isinstance(retry, int):
            i = 0
            while i < retry:
                p = read(q)
                if p is not None and p[0]:
                    self.pressure = p[1]
                    read_success = True
                    break
#                elif p is not None:
#                    if p[1]=='OFF':
#                        self.error=2
#                    elif p[1]=='UNDER9':
#                        self.error=3
#                    self.error=0
                time.sleep(0.1)
                i += 1
        else:
            p = read(q)
            if p is not None and p[0]:
                self.pressure = p[1]
                read_success = True

        if not read_success:

            # self.error=1
            # reset error flag
            # self.error=0

            self.pressure = 0

            self.trait_set(state=False, trait_change_notify=False)
#
#        else:#if self.state:
#            self.pressure = p

    def set_state(self):
        '''
        '''
        pass

    def _state_changed(self):
        '''
        '''
        if not self.state:
            self.pressure = 0


        self.set_state()

    def config_view(self):
        '''
        '''
        return View(
                    # Item('name', style = 'readonly', show_label = False),
                    Item('setpoints', style='custom',
                         show_label=False,
                         editor=ListEditor(use_notebook=True,
                                           dock_style='tab',
                                           page_name='.name'))
                    )






# class SetPoint(HasTraits):
#    #setpoint5=Float
#    #raits_view=View('setpoint5')
#    #setpoint_values=[]
#    #setpoint_values=List(Float,)
#    def __init__(self, parent, size = 1, simulation = False):
#        self.parent_gauge = parent
#        self.size = size
#        super(SetPoint, self).__init__()
#        self._set_up(size, simulation)
#    def _set_up(self, size, simulation):
#        for i in range(size):
#            #query the gauges set point
# #            if simulation:
# #                s=1
# #                b=False
# #            else:
# #                s=self.parent_gauge.get_setpoint(i+1)
# #                b=self.parent_gauge.get_setpoint_state(i+1)
#            s = 1
#            b = False
#            #self.setpoint_values.append(s)
#            self.add_trait('setpoint%i' % i, Float(s, enter_set = True, auto_set = False))
#            self.add_trait('setpoint%i_state' % i, Bool(b, enter_set = True, auto_set = False))
#
#    def traits_view(self):
#        content = []
#        for s in range(self.size):
#            g = HGroup(Item('setpoint%i' % s),
#                     Item('setpoint%i_state' % s))
#            content.append(g)
#        vg = VGroup(content = content)
#        return View(vg)
#    def set_transducer_set_point(self, v, i):
#        self.parent_gauge.set_transducer_set_point(v, i)

            # self.data_buffer.add_datum(self.pressure)

            # self.flag = not self.flag
            # m = 'pressure == %0.3e' % p
            # self.logger.info(m)


#    def _data_buffer_default(self):
#
#        return XYDataBuffer(parent = self, size = 10000)
#
#
#        self.data_buffer.add_datum(self._pressure)

#===================listeners=====================
#    @on_trait_change('_pressure')
#    def pressure_change(self, o, n, oo, nn):
#

#        '''
#        this is validating the pressure and toggling flag
#        '''
#        if nn == 1.0 and abs(oo - nn) > 0.1:
#            self.trait_set(pressure = oo, trait_change_notify = False)
#        else:
#            self.flag = not self.flag
#    def set_transducer_set_point(self, v, i):
#        '''
#        sends command to transducer to set the setpoint value
#        '''
#        q = self._build_command(self.address, 'setpoint', v, setpointindex = i)
#        self.write(q)
#        #print q
#        #print self.read()
#    def get_set_point_state(self):
#        '''
#            loops thru the transducers setpoints and saves them to the setpoint object
#        '''
#        for i in range(self.setpoint.size):
#            #print 'aadfasdfasd',self.get_setpoint_state(i)
#            self.setpoint.trait_set(**{'setpoint%i_state' % i:self.get_setpoint_state(i + 1)})
#
#    def get_setpoint(self, i):
#        '''
#            get and return the setpoint value
#        '''
#        type = 'setpoint'
#        if not self.simulation:
#            q = self._build_query(self.address, type, setpointindex = i)
#            #print q
#            self.write(q)
#            #print 'query ',q, '  response ',self.read()
#            #print self.read()
#            #s=self._parse_response(type, '@253SP11.0E+1;FF')
#            s = self._parse_response(type, self.read())
#        else:
#            s = 1
#
#        msg = 'write ' + q
#        self.logger.info(msg)
#        msg = 'read ' + str(s)
#        self.logger.info(msg)
#
#        return s
#    def get_set_point_values(self):
#        for i in range(self.setpoint.size):
#            self.setpoint.trait_set(**{'setpoint%i' % i:self.get_setpoint(i + 1)})
#    def get_setpoint_state(self, i):
#        #self.counter+=1
#        type = 'setpoint_state'
#
#        q = self._build_query(self.address, type, setpointindex = i)
#        self.write(q)
#        r = self.read()
#        #print r
#       # print self.simulation
#        if self.simulation:
#            return False
#        else:
#            return self._parse_response(type, r)
#    def _setup_setpoints(self):
#        '''
#        helper method to setup the setpoint
#        setpoint can be of size 1 (MP, ION) or 3 (MP3)
#        '''
#        s = 1
#        if self.type == 'MP3':
#            s = 3
#        self.setpoint = SetPoint(self, size = s, simulation = self.simulation)
