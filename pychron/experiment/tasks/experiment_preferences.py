# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Str, Int, \
    Bool, Password, Color, Property, Float, Enum
from traitsui.api import View, Item, Group, VGroup, HGroup, UItem
from envisage.ui.tasks.preferences_pane import PreferencesPane
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper, BaseConsolePreferences, \
    BaseConsolePreferencesPane
from pychron.pychron_constants import QTEGRA_INTEGRATION_TIMES


class PositiveInteger(Int):
    def validate(self, object, name, value):
        if value >= 0:
            return value

        self.error(object, name, value)


class LabspyPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.experiment'
    use_labspy = Bool


class DVCPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.experiment'
    use_dvc_persistence = Bool


class ExperimentPreferences(BasePreferencesHelper):
    preferences_path = 'pychron.experiment'
    id = 'pychron.experiment.preferences_page'

    use_notifications = Bool
    notifications_port = Int
    use_autoplot = Bool

    send_config_before_run = Bool
    use_auto_save = Bool
    auto_save_delay = Int

    baseline_color = Color
    sniff_color = Color
    signal_color = Color

    bg_color = Color
    even_bg_color = Color

    min_ms_pumptime = Int

    use_system_health = Bool

    use_memory_check = Bool
    memory_threshold = Property(PositiveInteger,
                                depends_on='_memory_threshold')
    _memory_threshold = Int

    use_analysis_grouping = Bool
    grouping_threshold = Float
    grouping_suffix = Str

    use_automated_run_monitor = Bool
    set_integration_time_on_start = Bool
    default_integration_time = Enum(*QTEGRA_INTEGRATION_TIMES)

    automated_runs_editable = Bool

    use_xls_persister = Bool

    success_color = Color
    extraction_color = Color
    measurement_color = Color
    canceled_color = Color
    truncated_color = Color
    failed_color = Color
    end_after_color = Color
    invalid_color = Color

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
    include_log = Bool


class ConsolePreferences(BaseConsolePreferences):
    preferences_path = 'pychron.experiment'
    use_message_colormapping = Bool


# class SysLoggerPreferences(BasePreferencesHelper):
# use_syslogger = Bool
#     preferences_path = 'pychron.syslogger'
#     username = Str
#     password = Password
#
#     host = Str


# ======================================================================================================
# panes
# ======================================================================================================
class LabspyPreferencesPane(PreferencesPane):
    model_factory = LabspyPreferences
    category = 'Experiment'

    def traits_view(self):
        v = View(VGroup(Item('use_labspy', label='Use Labspy'),
                        label='Labspy', show_border=True))
        return v


class DVCPreferencesPane(PreferencesPane):
    model_factory = DVCPreferences
    category = 'Experiment'

    def traits_view(self):
        v = View(VGroup(Item('use_dvc_persistence', label='Use DVC Persistence'),
                        label='DVC', show_border=True))
        return v


class ExperimentPreferencesPane(PreferencesPane):
    model_factory = ExperimentPreferences
    category = 'Experiment'

    def traits_view(self):
        system_health_grp = VGroup(Item('use_system_health'),
                                   label='System Health')

        notification_grp = VGroup(
            Item('use_autoplot'),
            Item('use_notifications'),
            Item('notifications_port',
                 enabled_when='use_notifications',
                 label='Port'),
            label='Notifications')

        editor_grp = Group(
            Item('automated_runs_editable',
                 label='Direct editing',
                 tooltip='Allow user to edit Automated Runs directly within table. '
                         'Reopen experiment tab required to take effect'),
            Item('use_auto_save',
                 tooltip='If "Use auto save" experiment queue saved after "timeout" seconds'),
            Item('auto_save_delay',
                 label='Auto save timeout (s)',
                 tooltip='If experiment queue is not saved then wait "timeout" seconds before saving or canceling'),
            Item('bg_color', label='Background'),
            Item('even_bg_color', label='Even Row'),
            label='Editor')

        color_group = Group(Item('sniff_color', label='Equilibration'),
                            Item('baseline_color', label='Baseline'),
                            Item('signal_color', label='Signal'),
                            label='Measurement Colors')

        state_color_grp = VGroup(Item('success_color', label='Success'),
                                 Item('extraction_color', label='Extraction'),
                                 Item('measurement_color', label='Measurement'),
                                 Item('canceled_color', label='Canceled'),
                                 Item('truncated_color', label='Truncated'),
                                 Item('failed_color', label='Failed'),
                                 Item('end_after_color', label='End After'),
                                 Item('invalid_color', label='Invalid'),

                                 label='State Colors')
        analysis_grouping_grp = Group(Item('use_analysis_grouping',
                                           label='Auto group analyses',
                                           tooltip=''),
                                      Item('grouping_suffix',
                                           label='Suffix',
                                           tooltip='Append "Suffix" to the Project name. e.g. MinnaBluff-autogen '
                                                   'where Suffix=autogen'),
                                      Item('grouping_threshold',
                                           label='Grouping Threshold (hrs)',
                                           tooltip='Associate Reference analyses with the project of an analysis that '
                                                   'is within X hours of the current run',
                                           enabled_when='use_analysis_grouping'),
                                      label='Analysis Grouping')

        memory_grp = Group(Item('use_memory_check', label='Check Memory',
                                tooltip='Ensure enough memory is available during experiment execution'),
                           Item('memory_threshold', label='Threshold',
                                enabled_when='use_memory_check',
                                tooltip='Do not continue experiment if available memory less than "Threshold"'),
                           label='Memory')

        monitor_grp = Group(Item('use_automated_run_monitor',
                                 label='Use AutomatedRun Monitor',
                                 tooltip='Use the automated run monitor'),
                            show_border=True,
                            label='Monitor')

        overlap_grp = Group(Item('min_ms_pumptime',
                                 label='Min. Mass Spectrometer Pumptime (s)'),
                            show_border=True,
                            label='Overlap')
        persist_grp = Group(Item('use_xls_persister', label='Save analyses to Excel workbook'),
                            label='Persist', show_border=True)
        automated_grp = Group(VGroup(Item('send_config_before_run',
                                          tooltip='Set the spectrometer configuration before each analysis',
                                          label='Set Spectrometer Configuration on Start'),
                                     Item('set_integration_time_on_start',
                                          tooltip='Set integration time on start of analysis',
                                          label='Set Integration Time on Start'),
                                     Item('default_integration_time',
                                          enabled_when='set_integration_time_on_start'),
                                     persist_grp,
                                     monitor_grp, overlap_grp),
                              label='Automated Run')

        return View(color_group,
                    automated_grp,
                    state_color_grp,
                    notification_grp,
                    editor_grp,
                    analysis_grouping_grp, memory_grp, system_health_grp)


class UserNotifierPreferencesPane(PreferencesPane):
    model_factory = UserNotifierPreferences
    category = 'Experiment'

    def traits_view(self):
        auth_grp = VGroup(Item('include_log'),
                          show_border=True,
                          label='User Notifier')

        v = View(auth_grp)
        return v


class ConsolePreferencesPane(BaseConsolePreferencesPane):
    model_factory = ConsolePreferences
    label = 'Experiment'

    def traits_view(self):
        preview = CustomLabel('preview',
                              size_name='fontsize',
                              color_name='textcolor',
                              bgcolor_name='bgcolor')

        v = View(VGroup(HGroup(UItem('fontsize'),
                               UItem('textcolor'),
                               UItem('bgcolor')),
                        preview,
                        Item('use_message_colormapping'),
                        show_border=True,
                        label=self.label))
        return v

# class SysLoggerPreferencesPane(PreferencesPane):
#     model_factory = SysLoggerPreferences
#     category = 'Experiment'
#
#     def traits_view(self):
#         auth_grp = VGroup(Item('host'),
#                           Item('username'),
#                           Item('password'),
#                           enabled_when='use_syslogger')
#
#         v = View(VGroup(Item('use_syslogger', label='Use SysLogger'),
#                         auth_grp,
#                         show_border=True,
#                         label='SysLogger'))
#         return v

# ============= EOF =============================================
