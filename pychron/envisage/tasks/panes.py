# ===============================================================================
# Copyright 2014 Jake Ross
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
from traitsui.api import View, Item, HGroup, VGroup
from traits.api import Directory, Bool
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.tasks.base_preferences_helper import GitRepoPreferencesHelper, test_connection_item


class GeneralPreferences(GitRepoPreferencesHelper):
    preferences_path = 'pychron.general'
    root_dir = Directory
    use_login = Bool
    multi_user = Bool


class GeneralPreferencesPane(PreferencesPane):
    model_factory = GeneralPreferences
    category = 'General'

    def traits_view(self):
        root_grp = VGroup(Item('root_dir', label='Pychron Directory'),
                          show_border=True, label='Root')
        login_grp = VGroup(Item('use_login'), Item('multi_user'),
                           label='Login', show_border=True)
        v = View(VGroup(root_grp,
                        login_grp,
                        HGroup(Item('remote', label='Laboratory Repo'),
                               test_connection_item()),
                        CustomLabel('remote_status',
                                    color_name='remote_status_color'),

                        show_border=True))
        return v

# ============= EOF =============================================



