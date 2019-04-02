# ===============================================================================
# Copyright 2018 ross
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
from traitsui.api import View, VGroup, HGroup, Item, EnumEditor, RangeEditor

from pychron.core.pychron_traits import BorderVGroup
from pychron.options.options import MainOptions, object_column, checkbox_column, SubOptions


class DefineEquilibrationMainOptions(MainOptions):
    def _get_columns(self):
        cols = [object_column(name='name', editable=False),
                # checkbox_column(name='plot_enabled', label='Plot'),
                checkbox_column(name='save_enabled', label='Enabled'),
                object_column(name='equilibration_time', label='Eq. Time'),
                ]
        return cols

    def _get_edit_view(self):
        g1 = HGroup(Item('name', editor=EnumEditor(name='names')),
                    Item('equilibration_time', label='Eq. Time'))

        v = View(VGroup(g1, show_border=True))
        return v


class DefineEquilibrationSubOptions(SubOptions):
    def traits_view(self):
        v = View(BorderVGroup(Item('show_statistics'),
                              Item('ncols',
                                   editor=RangeEditor(mode='text'), label='N. Columns')))
        return v


VIEWS = {'main': DefineEquilibrationMainOptions,
         'display': DefineEquilibrationSubOptions}
# ============= EOF =============================================
