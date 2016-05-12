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
from traits.api import Directory, Bool, String, Float
from traitsui.api import View, Item, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import GitRepoPreferencesHelper, remote_status_item, \
    BasePreferencesHelper


class GeneralPreferences(GitRepoPreferencesHelper):
    preferences_path = 'pychron.general'
    root_dir = Directory
    use_login = Bool
    multi_user = Bool
    confirm_quit = Bool
    show_random_tip = Bool
    # use_advanced_ui = Bool

    organization = String(enter_set=True, auto_set=False)
    default_principal_investigator = String

    def _organization_changed(self, new):
        if not self.remote and new:
            self.remote = '{}/Laboratory'.format(new)


class GeneralPreferencesPane(PreferencesPane):
    model_factory = GeneralPreferences
    category = 'General'

    def traits_view(self):
        root_grp = VGroup(Item('root_dir', label='Pychron Directory'),
                          show_border=True, label='Root')
        login_grp = VGroup(Item('use_login'), Item('multi_user'),
                           label='Login', show_border=True)

        o_grp = VGroup(Item('organization', label='Name'),
                       remote_status_item('Laboratory Repo'),
                       show_border=True,
                       label='Organization')

        v = View(VGroup(Item('confirm_quit', label='Confirm Quit',
                             tooltip='Ask user for confirmation when quitting application'),
                        Item('show_random_tip', label='Random Tip',
                             tooltip='Display a Random Tip whe the application starts'),
                        Item('default_principal_investigator', label='Default PI'),
                        # Item('use_advanced_ui', label='Advanced UI',
                        #      tooltip='Display the advanced UI'),
                        root_grp,
                        login_grp,
                        o_grp,
                        label='General',
                        show_border=True))
        return v


class BrowserPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.browser'
    recent_hours = Float
    reference_hours_padding = Float


class BrowserPreferencesPane(PreferencesPane):
    model_factory = BrowserPreferences
    category = 'Browser'

    def traits_view(self):
        v = View(Item('recent_hours'),
                 Item('reference_hours_padding'))
        return v

# ============= EOF =============================================
