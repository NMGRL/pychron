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

#============= enthought library imports =======================
from envisage.extension_point import ExtensionPoint
from envisage.plugin import Plugin
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.tasks_plugin import TasksPlugin
from pyface.tasks.action.dock_pane_toggle_group import DockPaneToggleGroup
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import List
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.actions import ToggleFullWindowAction, EditInitializationAction
from pychron.envisage.tasks.panes import GeneralPreferencesPane


class PychronTasksPlugin(Plugin):
    preferences_panes = List(
        contributes_to='envisage.ui.tasks.preferences_panes')
    task_extensions = List(contributes_to='envisage.ui.tasks.task_extensions')

    actions = ExtensionPoint(List, id='pychron.actions')

    def _preferences_panes_default(self):
        return [GeneralPreferencesPane]

    def _task_extensions_default(self):
        actions = [SchemaAddition(id='DockPaneToggleGroup',
                                  factory=DockPaneToggleGroup,
                                  path='MenuBar/view.menu'),
                   SchemaAddition(factory=ToggleFullWindowAction,
                                  id='toggle_full_window',
                                  path='MenuBar/window.menu'),
                   SchemaAddition(factory=EditInitializationAction,
                                  id='edit_plugins',
                                  path='MenuBar/help.menu')]
        return [TaskExtension(actions=actions)]


class myTasksPlugin(TasksPlugin):
    pass

    #def _create_preferences_dialog_service(self):
    #    from preferences_dialog import myPreferencesDialog
    #
    #    dialog = myPreferencesDialog(application=self.application)
    #    dialog.trait_set(categories=self.preferences_categories,
    #                     panes=[factory(dialog=dialog)
    #                            for factory in self.preferences_panes])
    #    return dialog

# ============= EOF =============================================
