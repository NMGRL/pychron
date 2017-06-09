# ===============================================================================
# Copyright 2016 Jake Ross
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

# ============= enthought library imports =======================
from traitsui.api import View, UItem, Item, HGroup, VGroup, Label, EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options import AppearanceSubOptions, MainOptions


class XYScatterAppearanceOptions(AppearanceSubOptions):
    pass


class XYScatterMainOptions(MainOptions):
    def _get_edit_view(self):
        x = HGroup(Item('x_n',
                        editor=EnumEditor(name='available_names'),
                        label='X'),
                   Label('/'),
                   UItem('x_d',
                         editor=EnumEditor(name='available_names')))
        y = HGroup(Item('y_n',
                        editor=EnumEditor(name='available_names'),
                        label='Y'),
                   Label('/'),
                   UItem('y_d',
                         editor=EnumEditor(name='available_names')))
        v = View(VGroup(Item('name', editor=EnumEditor(name='names')), x, y))
        return v


VIEWS = {}
VIEWS['main'] = XYScatterMainOptions
VIEWS['appearance'] = XYScatterAppearanceOptions

# ============= EOF =============================================
