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



#============= enthought library imports =======================
from traits.api import Any, Property
# from traitsui.api import View, Item, Group, HGroup, VGroup

#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.config_loadable import ConfigMixin


class SpectrometerDevice(ConfigMixin):
    microcontroller = Any
    # spectrometer = Any
    #    simulation = DelegatesTo('microcontroller')

    simulation = Property
    verbose = False

    def _get_simulation(self):
        s = True
        if self.microcontroller:
            s = self.microcontroller.simulation
        return s

    def finish_loading(self):
        pass

    def ask(self, *args, **kw):
        if self.microcontroller:
            if self.verbose:
                kw['verbose']=True

            return self.microcontroller.ask(*args, **kw)


#============= EOF =============================================
