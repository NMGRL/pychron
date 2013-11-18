#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Str, Int, \
    Bool, Password
from traitsui.api import View, Item, Group, VGroup
from envisage.ui.tasks.preferences_pane import PreferencesPane

from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper, BaseConsolePreferences, BaseConsolePreferencesPane


#============= standard library imports ========================
#============= local library imports  ==========================


class ExperimentPreferences(BasePreferencesHelper):
    name = 'Experiment'
    preferences_path = 'pychron.experiment'
    id = 'pychron.experiment.preferences_page'

    use_auto_figure = Bool
    use_notifications = Bool
    notifications_port = Int

    use_auto_save = Bool
    auto_save_delay = Int

    irradiation_prefix = Str
    monitor_name = Str


class ExperimentPreferencesPane(PreferencesPane):
    model_factory = ExperimentPreferences
    category = 'Experiment'

    def traits_view(self):
        auto_figure_grp = Group(
            Item('use_auto_figure'),
            VGroup(
                Item('use_notifications'),
                Item('notifications_port',
                     enabled_when='use_notifications',
                     label='Port'),

                label='Notifications'
            ),
            label='Auto Figure'
        )
        editor_grp = Group(
            Item('use_auto_save',
                 tooltip='If "Use auto save" experiment queue saved after "timeout" seconds'
            ),
            Item('auto_save_delay',
                 label='Auto save timeout (s)',
                 tooltip='If experiment queue is not saved then wait "timeout" seconds before saving or canceling'
            ),
            label='Editor'
        )
        irradiation_grp = Group(Item('irradiation_prefix',
                                     label='Irradiation Prefix'),
                                Item('monitor_name'),
                                label='Irradiations')

        return View(
            auto_figure_grp,
            editor_grp,
            irradiation_grp,
        )


class ConsolePreferences(BaseConsolePreferences):
    preferences_path = 'pychron.experiment'


class ConsolePreferencesPane(BaseConsolePreferencesPane):
    model_factory = ConsolePreferences
    label = 'Experiment'


class SysLoggerPreferences(BasePreferencesHelper):
    use_syslogger = Bool
    preferences_path = 'pychron.syslogger'
    username = Str
    password = Password

    host = Str


class SysLoggerPreferencesPane(PreferencesPane):
    model_factory = SysLoggerPreferences
    category = 'Experiment'

    def traits_view(self):
        auth_grp = VGroup(Item('host'),
                          Item('username'),
                          Item('password'),
                          enabled_when='use_syslogger')

        v = View(VGroup(Item('use_syslogger', label='Use SysLogger'),
                        auth_grp))
        return v

#============= EOF =============================================
