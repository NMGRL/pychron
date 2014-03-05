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
    Bool, Password, Color, Property
from traitsui.api import View, Item, Group, VGroup
from envisage.ui.tasks.preferences_pane import PreferencesPane


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper, BaseConsolePreferences, \
    BaseConsolePreferencesPane


class PositiveInteger(Int):
    def validate(self, object, name, value):
        if value >= 0:
            return value

        self.error(object, name, value)


class ExperimentPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.experiment'
    id = 'pychron.experiment.preferences_page'

    use_notifications = Bool
    notifications_port = Int

    use_auto_save = Bool
    auto_save_delay = Int

    irradiation_prefix = Str
    monitor_name = Str

    baseline_color = Color
    sniff_color = Color
    signal_color = Color

    filter_outliers = Bool(False)
    fo_iterations = Int(1)
    fo_std_dev = Int(2)

    min_ms_pumptime = Int

    use_memory_check = Bool
    memory_threshold = Property(PositiveInteger,
                                depends_on='_memory_threshold')
    _memory_threshold = Int

    def _get_memory_threshold(self):
        return self._memory_threshold

    def _set_memory_threshold(self, v):
        if v is not None:
            self._memory_threshold = v


class UserNotifierPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.experiment'
    server_username = Str
    server_password = Password
    server_host = Str
    server_port = Int


class ConsolePreferences(BaseConsolePreferences):
    preferences_path = 'pychron.experiment'


class SysLoggerPreferences(BasePreferencesHelper):
    use_syslogger = Bool
    preferences_path = 'pychron.syslogger'
    username = Str
    password = Password

    host = Str


#======================================================================================================
# panes
#======================================================================================================
class ExperimentPreferencesPane(PreferencesPane):
    model_factory = ExperimentPreferences
    category = 'Experiment'

    def traits_view(self):
        notification_grp = VGroup(
            Item('use_notifications'),
            Item('notifications_port',
                 enabled_when='use_notifications',
                 label='Port'),
            label='Notifications')

        editor_grp = Group(
            Item('use_auto_save',
                 tooltip='If "Use auto save" experiment queue saved after "timeout" seconds'),
            Item('auto_save_delay',
                 label='Auto save timeout (s)',
                 tooltip='If experiment queue is not saved then wait "timeout" seconds before saving or canceling'),
            label='Editor')

        irradiation_grp = Group(Item('irradiation_prefix',
                                     label='Irradiation Prefix'),
                                Item('monitor_name'),
                                label='Irradiations')

        color_group = Group(Item('sniff_color', label='Sniff'),
                            Item('baseline_color', label='Baseline'),
                            Item('signal_color', label='Signal'),
                            label='Colors')

        filter_grp = Group(Item('filter_outliers'),
                           VGroup(Item('fo_iterations', label='N. Iterations'),
                                  Item('fo_std_dev', label='N. standard deviations'),
                                  enabled_when='filter_outliers',
                                  show_border=True),
                           label='Post Fit Filtering')
        overlap_grp = Group(Item('min_ms_pumptime', label='Min. Mass Spectrometer Pumptime (s)'),
                            label='Overlap')
        memory_grp = Group(Item('use_memory_check', label='Check Memory',
                                tooltip='Ensure enough memory is available during experiment execution'),
                           Item('memory_threshold', label='Threshold',
                                enabled_when='use_memory_check',
                                tooltip='Do not continue experiment if available memory less than "Threshold"'),
                           label='Memory')

        return View(color_group, notification_grp,
                    editor_grp, irradiation_grp,
                    filter_grp, overlap_grp, memory_grp)


class UserNotifierPreferencesPane(PreferencesPane):
    model_factory = UserNotifierPreferences
    category = 'Experiment'

    def traits_view(self):
        auth_grp = VGroup(Item('server_username', label='User'),
                          Item('server_password', label='Password'),
                          Item('server_host', label='Host'),
                          Item('server_port', label='Port'),
                          label='User Notifier')

        v = View(auth_grp)
        return v


class ConsolePreferencesPane(BaseConsolePreferencesPane):
    model_factory = ConsolePreferences
    label = 'Experiment'


class SysLoggerPreferencesPane(PreferencesPane):
    model_factory = SysLoggerPreferences
    category = 'Experiment'

    def traits_view(self):
        auth_grp = VGroup(Item('host'),
                          Item('username'),
                          Item('password'),
                          enabled_when='use_syslogger')

        v = View(VGroup(Item('use_syslogger', label='Use SysLogger'),
                        auth_grp,
                        label='SysLogger'))
        return v

#============= EOF =============================================
