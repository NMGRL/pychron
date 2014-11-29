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



# =============enthought library imports=======================
from traits.api import HasTraits, Property, Int, Float, Bool, Any
from traitsui.api import View, Item

# =============standard library imports ========================

# =============local library imports  ==========================
class Setpoint(HasTraits):
    '''
        G{classtree}
    '''
    name = Property(depends_on='index')
    enabled = Property(Bool(), depends_on='_enabled')
    _enabled = Bool

    value = Property(Float(enter_set=True, auto_set=False), depends_on='_value')
    _value = Float

    parent = Any
    index = Int(1)
    def load(self):
        '''
        '''
        p = self.parent
        if not p.simulation:
            cmd = p._build_query(p.address, 'setpoint_enable', setpointindex=self.index)
            e = p._parse_response('setpoint_enable', p.ask(cmd, delay=100))
            if e is None:
                e = False
            self._enabled = e

            cmd = p._build_query(p.address, 'setpoint_value', setpointindex=self.index)
            v = p._parse_response('setpoint_value', p.ask(cmd, delay=100))
            if v is None:
                v = -1
            self._value = v

    def _get_name(self):
        '''
        '''
        return 'Setpoint %i' % self.index

    def _get_enabled(self):
        '''
        '''
        return self._enabled

    def _get_value(self):
        '''
        '''
        return self._value

    def _set_value(self, v):
        '''
            @type v: C{str}
            @param v:
        '''
        self._value = float(v)
        p = self.parent

        cmd = p._build_command(p.address, 'setpoint', float(v), setpointindex=self.index)
        p.ask(cmd, delay=100)



    def _set_enabled(self, v):
        '''
            @type v: C{str}
            @param v:
        '''

        self._enabled = v

        p = self.parent
        cmd = p._build_command(p.address, 'setpoint_enable', v, setpointindex=self.index)
        p.ask(cmd, delay=100)


    def traits_view(self):
        '''
        '''
        return View(Item('value'),
                    Item('enabled'))
