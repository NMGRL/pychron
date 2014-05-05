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
from enable.colors import ColorTrait
from enable.markers import MarkerTrait
from traits.api import HasTraits, Str, Range, on_trait_change, Event, Bool, Dict, Enum, Property
from traitsui.api import View, Item, EnumEditor, HGroup, VGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.pychron_constants import FIT_TYPES, NULL_STR

TIME_SCALARS = {'h': 3600., 'm': 60., 's': 1.0, 'days': (3600. * 24)}


class XYScatterTool(HasTraits):
    index_attr = Str('Ar40')
    value_attr = Str('Ar39')

    marker_size = Range(0.0, 10., 1.0)
    marker = MarkerTrait

    update_needed = Event
    auto_refresh = Bool

    attrs = Dict({'Ar40': '01:Ar40',
                  'Ar39': '02:Ar39',
                  'Ar38': '03:Ar38',
                  'Ar37': '04:Ar37',
                  'Ar36': '05:Ar36',
                  'Ar40/Ar39': '06:Ar40/Ar39',
                  'Ar40/Ar38': '07:Ar40/Ar38',
                  'Ar40/Ar36': '08:Ar40/Ar36',
                  'timestamp': '09:Analysis Time',
                  'cleanup': '10:Cleanup',
                  'extract_value': '11:Extract Value',
                  'duration': '12:Extract Duration'
    })

    index_time_units = Enum('h', 'm', 's', 'days')
    index_time_scalar = Property

    value_time_units = Enum('h', 'm', 's', 'days')
    value_time_scalar = Property
    fit = Enum([NULL_STR] + FIT_TYPES)
    marker_color = ColorTrait

    def get_marker_dict(self):
        kw = dict(marker=self.marker,
                  marker_size=self.marker_size,
                  color=self.marker_color)
        return kw

    def _get_index_time_scalar(self):
        return TIME_SCALARS[self.index_time_units]

    def _get_value_time_scalar(self):
        return TIME_SCALARS[self.value_time_units]

    @on_trait_change('index_+, value_+, marker+')
    def _refresh(self):
        if self.auto_refresh:
            self.update_needed = True

    def traits_view(self):
        v = View(
            HGroup(Item('auto_refresh'),
                   icon_button_editor('update_needed', 'refresh')),
            HGroup(Item('index_attr',
                        editor=EnumEditor(name='attrs'),
                        label='X Attr.'),
                   Item('index_time_units',
                        label='Units',
                        visible_when='index_attr=="timestamp"')),
            HGroup(Item('value_attr',
                        editor=EnumEditor(name='attrs'),
                        label='Y Attr.'),
                   Item('value_time_units',
                        label='Units',
                        visible_when='value_attr=="timestamp"')),
            VGroup(
                Item('marker'),
                Item('marker_size', label='Size'),
                Item('marker_color', label='Color'),
                show_border=True),
            Item('fit'),
            resizable=True)
        return v

#============= EOF =============================================

