#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Str, List, Any, Property, Event, cached_property, \
    Button
from traitsui.api import View, Item, HGroup, spring
from pychron.helpers.traitsui_shortcuts import listeditor

#============= standard library imports ========================
#============= local library imports  ==========================

class Readout(HasTraits):
    name = Str
    value = Property(depends_on='refresh')
    format = Str('{:0.3f}')
    refresh = Event
    spectrometer = Any

    def traits_view(self):
        v = View(HGroup(Item('value', style='readonly', label=self.name)))
        return v

    @cached_property
    def _get_value(self):
        cmd = 'Get{}'.format(self.name)
        v = self.spectrometer.get_parameter(cmd)
        if v is not None:
            try:
                v = self.format.format(float(v))
            except ValueError:
                pass
        else:
            v = ''
        return v


class ReadoutView(HasTraits):
    readouts = List(Readout)
    spectrometer = Any
    refresh = Button
    def load(self, config):
        if config is not None:
            for section in config.sections():
                rd = Readout(name=section,
                             spectrometer=self.spectrometer)
                self.readouts.append(rd)

    def _refresh_fired(self):
        for rd in self.readouts:
            rd.refresh = True

    def traits_view(self):
        v = View(
                 listeditor('readouts'),
                 HGroup(spring, Item('refresh', show_label=False))
                 )
        return v

#============= EOF =============================================
