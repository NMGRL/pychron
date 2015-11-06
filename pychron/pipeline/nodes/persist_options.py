# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import Enum, Bool
from traitsui.api import View, UItem, VGroup, Tabbed, Item


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.save_model import SaveModel, SaveController
from pychron.paths import paths


class AnalysisTablePersistOptions(SaveModel):
    extension = Enum('xls', 'pdf')
    show_grid = Bool
    show_outline = Bool

    @property
    def default_root(self):
        return paths.table_dir


class AnalysisTablePersistOptionsView(SaveController):
    def traits_view(self):
        path_grp = self._get_path_group(show_border=True)
        view_grp = VGroup(Item('show_grid'),
                          Item('show_outline'),
                          label='Appearance')

        v = View(Tabbed(VGroup(UItem('extension', label='Output Mode'),
                               path_grp),
                        view_grp),
                 title='Save Analysis Table',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


class InterpretedAgePersistOptions(SaveModel):
    extension = Enum('xls', 'pdf')
    show_grid = Bool
    show_outline = Bool

    @property
    def default_root(self):
        return paths.table_dir


class InterpretedAgePersistOptionsView(SaveController):
    def traits_view(self):
        path_grp = self._get_path_group(show_border=True)
        view_grp = VGroup(Item('show_grid'),
                          Item('show_outline'),
                          label='Appearance')

        v = View(Tabbed(VGroup(UItem('extension', label='Output Mode'),
                               path_grp),
                        view_grp),
                 title='Save Interpreted Age Table',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v

# ============= EOF =============================================
