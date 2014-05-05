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
from enable.markers import MarkerTrait
from traits.api import HasTraits, Str, Range, on_trait_change, Event, Bool, List
from traitsui.api import View, Item, EnumEditor, HGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.pychron_constants import ARGON_KEYS


class XYScatterTool(HasTraits):
    index_attr = Str('Ar40')
    value_attr = Str('Ar39')

    marker_size = Range(0.0, 10., 1.0)
    marker = MarkerTrait

    update_needed = Event
    auto_refresh = Bool

    attrs = List(ARGON_KEYS)

    @on_trait_change('index_attr, value_attr, marker+')
    def _refresh(self):
        if self.auto_refresh:
            self.update_needed = True

    def traits_view(self):
        v = View(
            HGroup(Item('auto_refresh'),
                   icon_button_editor('update_needed', 'refresh')),
            Item('index_attr',
                 editor=EnumEditor(name='attrs'),
                 label='X Attr.'),
            Item('value_attr',
                 editor=EnumEditor(name='attrs'),
                 label='Y Attr.'),
            Item('marker_size'),
            Item('marker'),
            resizable=True)
        return v

#============= EOF =============================================

