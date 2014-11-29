# ===============================================================================
# Copyright 2013 Jake Ross
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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import CInt, Str, on_trait_change, Int
from traitsui.api import View, Item, VGroup, ListStrEditor, HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import FavoritesPreferencesHelper, FavoritesAdapter, \
    BaseConsolePreferences, BaseConsolePreferencesPane, BasePreferencesHelper


class SystemMonitorPreferences(FavoritesPreferencesHelper):
    preferences_path = 'pychron.sys_mon'

    system_name = Str
    host = Str
    port = CInt

    def _get_attrs(self):
        return ['fav_name',
                'system_name', 'host', 'port']

    def _get_values(self):
        return [self.fav_name,
                self.system_name, self.host, str(self.port)]

    @on_trait_change('host, port, system_name')
    def attribute_changed(self, name, new):

        if self.favorites:
            idx = ['', 'system_name',
                   'host',
                   'port']

            for i, fastr in enumerate(self.favorites):
                vs = fastr.split(',')
                if vs[0] == self.fav_name:
                    aind = idx.index(name)
                    fa = fastr.split(',')
                    fa[aind] = new
                    fastr = ','.join(map(str, fa))
                    self.favorites[i] = fastr
                    self.selected = fastr
                    break


class SystemMonitorPreferencesPane(PreferencesPane):
    model_factory = SystemMonitorPreferences
    category = 'SystemMonitor'

    def traits_view(self):
        fav_grp = VGroup(Item('fav_name',
                              show_label=False),
                         Item('favorites',
                              show_label=False,
                              width=100,
                              editor=ListStrEditor(
                                  editable=False,
                                  adapter=FavoritesAdapter(),
                                  selected='object.selected',
                              )),
                         HGroup(
                             icon_button_editor('add_favorite', 'add',
                                                tooltip='Add saved connection'),
                             icon_button_editor('delete_favorite', 'delete',
                                                tooltip='Delete saved connection')))
        conn_grp = VGroup(Item('system_name'),
                          Item('host'),
                          Item('port'),
        )
        v = View(VGroup(HGroup(fav_grp, conn_grp),
                        label='Connections',
        ))
        return v


class ConsolePreferences(BaseConsolePreferences):
    preferences_path = 'pychron.sys_mon'


class ConsolePreferencesPane(BaseConsolePreferencesPane):
    model_factory = ConsolePreferences
    label = 'System Monitor'


class DashboardPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.dashboard'
    host = Str
    port = Int


class DashboardPreferencesPane(PreferencesPane):
    model_factory = DashboardPreferences
    category = 'SystemMonitor'

    def traits_view(self):
        v = View(VGroup(Item('host'),
                        Item('port'),
                        label='Dashboard'))
        return v

# ============= EOF =============================================
