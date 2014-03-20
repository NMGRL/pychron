#===============================================================================
# Copyright 2014 Jake Ross
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

#============= standard library imports ========================
#============= local library imports  ==========================

from chaco.default_colormaps import color_map_name_dict
from traits.has_traits import HasTraits
from traits.trait_types import Button, Str, Int, Enum, Any, List, Bool
from traits.traits import Property
from traitsui.editors import EnumEditor
from traitsui.group import VGroup, HGroup
from traitsui.item import Item, UItem
from traitsui.view import View

from pychron.pychron_constants import ERROR_TYPES


class DummyFluxMonitor(HasTraits):
    sample = Str


class FluxTool(HasTraits):
    calculate_button = Button('Calculate')
    monitor_age = Property(depends_on='monitor')
    color_map_name = Str('jet')
    levels = Int(10, auto_set=False, enter_set=True)
    model_kind = Str('Plane')

    data_source = Str('database')
    # plot_kind = Str('Contour')
    plot_kind = Enum('Contour', 'Hole vs J')

    # def _plot_kind_default(self,):
    monitor = Any
    monitors = List

    group_positions = Bool(False)
    show_labels = Bool(True)

    mean_j_error_type = Enum(*ERROR_TYPES)
    predicted_j_error_type = Enum(*ERROR_TYPES)
    save_mean_j = Bool(True)

    def _monitor_default(self):
        return DummyFluxMonitor()

    def _get_monitor_age(self):
        ma = 28.02e6
        if self.monitor:
            ma = self.monitor.age

        return ma

    def traits_view(self):
        contour_grp = VGroup(Item('color_map_name',
                                  label='Color Map',
                                  editor=EnumEditor(values=sorted(color_map_name_dict.keys()))),
                             Item('levels'),
                             visible_when='plot_kind=="Contour"')
        monitor_grp = Item('monitor', editor=EnumEditor(name='monitors'))
        v = View(
            VGroup(HGroup(UItem('calculate_button'),
                          UItem('data_source', editor=EnumEditor(values=['database', 'file'])),
                          monitor_grp),
                   Item('save_mean_j', label='Save Mean J'),
                   Item('mean_j_error_type', label='Mean J Error'),
                   Item('predicted_j_error_type', label='Predicted J Error'),
                   HGroup(Item('group_positions'),
                          Item('object.monitor.sample',
                               style='readonly', label='Sample')),
                   Item('show_labels',
                        label='Display Labels',
                        tooltip='Display hole labels on plot'),
                   HGroup(UItem('plot_kind'),
                          Item('model_kind', label='Fit Model',
                               editor=EnumEditor(values=['Bowl', 'Plane']))),
                   # UItem('plot_kind', editor=EnumEditor(values=['Contour', 'Hole vs J']))),
                   contour_grp))
        return v

#============= EOF =============================================

