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

import hashlib
import random
from threading import Thread

# ============= enthought library imports =======================
from envisage.extension_point import ExtensionPoint
from envisage.ui.tasks.action.exit_action import ExitAction
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.tasks_plugin import TasksPlugin
from pyface.action.group import Group
from pyface.confirmation_dialog import confirm
from pyface.constant import NO
from pyface.tasks.action.dock_pane_toggle_group import DockPaneToggleGroup
from pyface.tasks.action.schema import SMenu, SGroup
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import List, Tuple, HasTraits, Password
from traitsui.api import View, Item

from pychron.envisage.resources import icon
from pychron.envisage.tasks.actions import (
    ToggleFullWindowAction,
    EditInitializationAction,
    EditTaskExtensionsAction,
    GenericFindAction,
    GenericSaveAsAction,
    GenericSaveAction,
    ShareSettingsAction,
    ApplySettingsAction,
    CloseAction,
    CloseOthersAction,
    OpenAdditionalWindow,
    MinimizeAction,
    ResetLayoutAction,
    PositionAction,
    IssueAction,
    AboutAction,
    DocumentationAction,
    ChangeLogAction,
    RestartAction,
    StartupTestsAction,
    ManageSettingsAction,
)
from pychron.envisage.tasks.base_plugin import BasePlugin
from pychron.envisage.tasks.base_task import WindowGroup
from pychron.envisage.tasks.preferences import (
    GeneralPreferencesPane,
    BrowserPreferencesPane,
)
from pychron.globals import globalv
from pychron.paths import paths


class PychronTasksPlugin(BasePlugin):
    id = "pychron.tasks.plugin"
    name = "Tasks"
    preferences_panes = List(contributes_to="envisage.ui.tasks.preferences_panes")
    task_extensions = List(contributes_to="envisage.ui.tasks.task_extensions")

    actions = ExtensionPoint(List, id="pychron.actions")
    file_defaults = ExtensionPoint(List(Tuple), id="pychron.plugin.file_defaults")
    help_tips = ExtensionPoint(List, id="pychron.plugin.help_tips")
    available_task_extensions = ExtensionPoint(
        List, id="pychron.available_task_extensions"
    )

    my_tips = List(contributes_to="pychron.plugin.help_tips")
    background_processes = ExtensionPoint(List, id="pychron.background_processes")

    def start(self):
        self.info("Writing plugin file defaults")
        paths.write_file_defaults(self.file_defaults)

        self._set_user()
        self._random_tip()
        self._start_background_processes()

    def _start_background_processes(self):
        self.info("starting background processes disabled")
        return

        for i, p in enumerate(self.background_processes):
            if isinstance(p, tuple):
                name, func = p
            else:
                func = p
                name = "Background{:02n}".format(i)

            if hasattr(func, "__call__"):
                t = Thread(target=func, name=name)
                t.setDaemon(True)
                t.start()

    def _set_user(self):
        self.application.preferences.set("pychron.general.username", globalv.username)
        self.application.preferences.save()

    def _random_tip(self):
        if globalv.random_tip_enabled and self.application.get_boolean_preference(
            "pychron.general.show_random_tip"
        ):
            from pychron.envisage.tasks.tip_view import TipView

            t = random.choice(self.help_tips)

            tv = TipView(text=t)
            tv.edit_traits()

    def _my_tips_default(self):
        return [
            "Use <b>Help>What's New</b> to view the official ChangeLog for the current version",
            'Turn Off Random Tip two ways:<br><b>1. Preferences>General></b> Uncheck "Random Tip".</b><br>'
            "<b>2.</b> Set the flag <i>random_tip_enabled</i> to False in the initialization file",
            'Use <b>Window/Reset Layout</b> to change the current window back to its default "Look"',
            "Submit bugs or issues to the developers manually using <b>Help/Add Request/Report Bug</b>",
            "The current version of Pychron contains over 156K lines of code in 1676 files",
            'If menu actions are missing first check that the desired "Plugin" is enabled using <b>Help/Edit '
            'Initialization</b>. If "Plugin" is enabled, check that the desired action is enabled using '
            "<b>Help/Edit UI</b>.",
        ]

    def _preferences_panes_default(self):
        return [GeneralPreferencesPane, BrowserPreferencesPane]

    def _task_extensions_default(self):
        actions = [
            SchemaAddition(
                factory=EditInitializationAction,
                id="edit_plugins",
                path="MenuBar/help.menu",
            )
        ]
        return [TaskExtension(actions=actions)]


# class mPreferencesAction(PreferencesAction):
#     image = icon('preferences-desktop')


class ConfirmApplicationExit(HasTraits):
    pwd = Password

    def validate(self):
        return True
        return hashlib.sha1(self.pwd).hexdigest() == globalv.dev_pwd

    def traits_view(self):
        v = View(Item("pwd", label="Password"), buttons=["OK", "Cancel"])
        return v


class mExitAction(ExitAction):
    def perform(self, event):
        app = event.task.window.application
        if globalv.username == "dev" and globalv.dev_confirm_exit:
            window = event.task.window
            dialog = ConfirmApplicationExit()
            ui = dialog.edit_traits(parent=window.control, kind="livemodal")
            if not ui.result or not dialog.validate():
                return
        else:
            prefs = app.preferences
            if prefs.get("pychron.general.confirm_quit"):
                ret = confirm(None, "Are you sure you want to Quit?")
                if ret == NO:
                    return
        app.exit(force=True)


class myTasksPlugin(TasksPlugin):
    def _my_task_extensions_default(self):
        from pyface.tasks.action.api import SchemaAddition
        from envisage.ui.tasks.action.preferences_action import PreferencesGroup

        def edit_menu():
            return SMenu(GenericFindAction(), id="edit.menu", name="&Edit")

        def file_menu():
            return SMenu(
                SGroup(id="Open"),
                SGroup(id="New"),
                SGroup(GenericSaveAsAction(), GenericSaveAction(), id="Save"),
                mExitAction(),
                PreferencesGroup(),
                id="file.menu",
                name="&File",
            )

        def tools_menu():
            return SMenu(
                ShareSettingsAction(),
                ApplySettingsAction(),
                ManageSettingsAction(),
                id="tools.menu",
                name="Tools",
            )

        def window_menu():
            return SMenu(
                WindowGroup(),
                Group(CloseAction(), CloseOthersAction(), id="Close"),
                OpenAdditionalWindow(),
                Group(MinimizeAction(), ResetLayoutAction(), PositionAction()),
                ToggleFullWindowAction(),
                # SplitEditorAction(),
                id="window.menu",
                name="Window",
            )

        def help_menu():
            return SMenu(
                IssueAction(),
                # NoteAction(),
                AboutAction(),
                DocumentationAction(),
                ChangeLogAction(),
                RestartAction(),
                # KeyBindingsAction(),
                # SwitchUserAction(),
                StartupTestsAction(),
                EditTaskExtensionsAction(),
                id="help.menu",
                name="&Help",
            )

        def view_menu():
            return SMenu(id="view.menu", name="&View")

        actions = [
            SchemaAddition(
                id="DockPaneToggleGroup",
                factory=DockPaneToggleGroup,
                path="MenuBar/view.menu",
            ),
            SchemaAddition(
                path="MenuBar", factory=file_menu, absolute_position="first"
            ),
            SchemaAddition(
                path="MenuBar", after="file.menu", before="view.menu", factory=edit_menu
            ),
            SchemaAddition(path="MenuBar", after="edit.menu", factory=view_menu),
            SchemaAddition(
                path="MenuBar", factory=tools_menu, absolute_position="last"
            ),
            SchemaAddition(
                path="MenuBar", factory=window_menu, absolute_position="last"
            ),
            SchemaAddition(path="MenuBar", factory=help_menu, absolute_position="last"),
        ]

        return [TaskExtension(actions=actions)]

    def _create_preferences_dialog_service(self):
        from .preferences_dialog import PreferencesDialog

        dialog = PreferencesDialog(application=self.application)
        dialog.trait_set(
            categories=self.preferences_categories,
            panes=[factory(dialog=dialog) for factory in self.preferences_panes],
        )
        return dialog


# ============= EOF =============================================
