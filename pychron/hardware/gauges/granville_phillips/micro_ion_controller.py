# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
# =============enthought library imports=======================
from __future__ import absolute_import
from traits.api import List, Str, HasTraits, Float, Int
from traitsui.api import View, HGroup, Item, ListEditor, InstanceEditor, Group
# =============standard library imports ========================
from numpy import random, char
import time

# =============local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice
from pychron.core.ui.color_map_bar_editor import BarGaugeEditor
from pychron.hardware.gauges.base_controller import BaseGauge
from pychron.hardware.gauges.granville_phillips.base_micro_ion_controller import BaseMicroIonController


class Gauge(BaseGauge):
    def traits_view(self):
        v = View(HGroup(Item('display_name', show_label=False, style='readonly',
                             width=-30, ),
                        Item('pressure',
                             format_str='%0.2e',
                             show_label=False,
                             style='readonly'),
                        Item('pressure',
                             show_label=False,
                             width=self.width,
                             editor=BarGaugeEditor(low=self.low,
                                                   high=self.high,
                                                   scale='power',
                                                   color_scalar=self.color_scalar,
                                                   width=self.width))))
        return v


class MicroIonController(BaseMicroIonController, CoreDevice):
    scan_func = 'get_pressures'
    gauge_klass = Gauge

    def gauge_view(self):
        v = View(Group(Item('gauges', style='custom',
                            show_label=False,
                            editor=ListEditor(mutable=False,
                                              style='custom',
                                              editor=InstanceEditor())),
                       show_border=True,
                       label=self.display_name))
        return v

    def graph_builder(self, g):
        super(MicroIonController, self).graph_builder(g, show_legend=True)
        g.new_series()
        g.set_series_label('IG', series=0)

        g.new_series()
        g.set_series_label('CG1', series=1)

        g.new_series()
        g.set_series_label('CG2', series=2)

# ============= EOF ====================================
