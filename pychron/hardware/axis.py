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



# ============= enthought library imports =======================
from traits.api import  Any, Str, Int, Float, \
    Bool, Property, on_trait_change, CInt
from traitsui.api import View, Item

# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.config_loadable import ConfigLoadable


class Axis(ConfigLoadable):
    '''
    '''
    id = Int
#    name = Str
    position = Float
    negative_limit = Float
    positive_limit = Float
    pdir = Str
    parent = Any(transient=True)
    calculate_parameters = Bool(True)
    drive_ratio = Float(1)

    velocity = Property(depends_on='_velocity')
    _velocity = Float(enter_set=True, auto_set=False)

    acceleration = Property(depends_on='_acceleration')
    _acceleration = Float(enter_set=True, auto_set=False)

    deceleration = Property(depends_on='_deceleration')
    _deceleration = Float(enter_set=True, auto_set=False)

    machine_velocity = Float
    machine_acceleration = Float
    machine_deceleration = Float
    # sets handled by child class

    nominal_velocity = Float
    nominal_acceleration = Float
    nominal_deceleration = Float

    sign = CInt(1)
    def _get_velocity(self):
        return self._velocity

    def _get_acceleration(self):
        return self._acceleration

    def _get_deceleration(self):
        return self._deceleration

    def upload_parameters_to_device(self):
        pass

    @on_trait_change('_velocity, _acceleration, _deceleration')
    def update_machine_values(self, obj, name, old, new):
        setattr(self, 'machine{}'.format(name), new)

    def _calibration_changed(self):
        self.parent.update_axes()

    def simple_view(self):
        v = View(Item('calculate_parameters'),
                 Item('velocity', format_str='%0.3f', enabled_when='not calculate_parameters'),
                    Item('acceleration', format_str='%0.3f', enabled_when='not calculate_parameters'),
                    Item('deceleration', format_str='%0.3f', enabled_when='not calculate_parameters'),
                    Item('drive_ratio')
                    )
        return v

    def full_view(self):
        return self.simple_view()

    def dump(self):
        '''
        '''
        pass
#        self.loaded = False
#
#        p = os.path.join(self.pdir, '.%s' % self.name)
#        with open(p, 'w') as f:
#            pickle.dump(self, f)
#    def load_parameters_from_config(self, path):
#        self.config_path = path
#        self._load_parameters_from_config(path)
#
#    def load_parameters(self, pdir):
#        '''
#        '''
# #        self.pdir = pdir
# #        p = os.path.join(pdir, '.%s' % self.name)
# #
# #        if os.path.isfile(p):
# #            return p
# #        else:
#        self.load(pdir)

    def save(self):
        pass

    def ask(self, cmd):
        return self.parent.ask(cmd)

    def _get_parameters(self, path):
        '''
  
        '''
#        cp = ConfigParser.ConfigParser()
#        cp.read())
        params = []
#        if path is None:
        if not os.path.isfile(path):
            path = os.path.join(path, '{}axis.cfg'.format(self.name))

        cp = self.get_configuration(path)
        if cp:
            params = [item for s in cp.sections() for item in cp.items(s)]

#        for ai in a:
#            print ai
#
#        for s in cp.sections():
#            for i in cp.items(s):
#                params.append(i)
        return params
    def _validate_float(self, v):
        try:
            v = float(v)
            return v
        except ValueError:
            pass
# ============= EOF ====================================
