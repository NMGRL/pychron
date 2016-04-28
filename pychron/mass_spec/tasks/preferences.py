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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Str, Bool, Password, List
from traitsui.api import View, Item, HGroup, VGroup, Spring, Label, EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.database.tasks.connection_preferences import ConnectionMixin
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper


class MassSpecConnectionPreferences(BasePreferencesHelper, ConnectionMixin):
    preferences_path = 'pychron.massspec.database'
    name = Str
    username = Str
    password = Password
    host = Str
    _adapter_klass = 'pychron.mass_spec.database.massspec_database_adapter.MassSpecDatabaseAdapter'
    enabled = Bool

    def _anytrait_changed(self, name, old, new):
        if name not in ('_connected_label', '_connected_color',
                        '_connected_color_',
                        'test_connection'):
            self._reset_connection_label(False)
        super(MassSpecConnectionPreferences, self)._anytrait_changed(name, old, new)

    def _get_connection_dict(self):
        return dict(username=self.username,
                    host=self.host,
                    password=self.password,
                    name=self.name,
                    kind='mysql')


class MassSpecConfigPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.massspec.config'
    reference_detector_name = Str
    reference_isotope_name = Str
    _reference_isotope_names = List(('Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36'))
    _reference_detector_names = List(('H2', 'H1', 'AX', 'L1', 'L2', 'CDD'))


class MassSpecConfigPane(PreferencesPane):
    model_factory = MassSpecConfigPreferences
    category = 'MassSpec'

    def traits_view(self):
        v = View(Item('reference_detector_name', label='Reference Detector',
                      editor=EnumEditor(name='_reference_detector_names')),
                 Item('reference_isotope_name', label='Reference Isotope',
                      editor=EnumEditor(name='_reference_isotope_names')))
        return v


class MassSpecConnectionPane(PreferencesPane):
    model_factory = MassSpecConnectionPreferences
    category = 'MassSpec'

    def traits_view(self):
        cgrp = HGroup(Spring(width=10, springy=False),
                      icon_button_editor('test_connection_button', 'database_connect',
                                         tooltip='Test connection'),
                      Spring(width=10, springy=False),
                      Label('Status:'),
                      CustomLabel('_connected_label',
                                  label='Status',
                                  weight='bold',
                                  color_name='_connected_color'))

        massspec_grp = VGroup(Item('enabled', label='Use MassSpec'),
                              VGroup(
                                  cgrp,
                                  Item('name', label='Database'),
                                  Item('host', label='Host'),
                                  Item('username', label='Name'),
                                  Item('password', label='Password'),
                                  enabled_when='enabled',
                                  show_border=True,
                                  label='Authentication'),
                              label='MassSpec DB',
                              show_border=True)

        return View(massspec_grp)

# ============= EOF =============================================
