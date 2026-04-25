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

import os
from operator import attrgetter

from envisage.ui.tasks.action.task_window_launch_group import TaskWindowLaunchAction
from pyface.action.api import ActionItem, Group
from pyface.confirmation_dialog import ConfirmationDialog
from pyface.constant import OK, CANCEL, YES
from pyface.directory_dialog import DirectoryDialog
from pyface.file_dialog import FileDialog
from pyface.tasks.action.schema import SMenu, SMenuBar, SGroup
from pyface.tasks.task import Task
from pyface.tasks.task_layout import TaskLayout
from pyface.timer.do_later import do_later, do_after
from traits.api import Any, on_trait_change, List, Unicode, Instance

from pychron.core.helpers.filetools import add_extension, view_file
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.preference_mixin import PreferenceMixin
from pychron.envisage.resources import icon
from pychron.envisage.tasks.actions import (
    GenericSaveAction,
    GenericSaveAsAction,
    GenericFindAction,
    RaiseAction,
    RaiseUIAction,
    ResetLayoutAction,
    MinimizeAction,
    PositionAction,
    IssueAction,
    CloseAction,
    CloseOthersAction,
    AboutAction,
    OpenAdditionalWindow,
    RestartAction,
    DocumentationAction,
    ChangeLogAction,
    StartupTestsAction,
    ShareSettingsAction,
    ApplySettingsAction,
)
from pychron.loggable import Loggable
from pychron.paths import paths


class WindowGroup(Group):
    items = List
    manager = Any

    def _manager_default(self):
        manager = self
        while isinstance(manager, Group):
            manager = manager.parent

        return manager

    def _items_default(self):
        application = self.manager.controller.task.window.application
        application.on_trait_change(
            self._rebuild, "active_window, window_opened, window_closed, windows, uis[]"
        )
        return []

    def _make_actions(self, vs):
        items = []
        if self.manager.controller.task.window is not None:
            application = self.manager.controller.task.window.application
            added = []
            for vi in application.windows + vs:
                if hasattr(vi, "active_task"):
                    if vi.active_task:
                        if not vi.active_task.id in added:
                            checked = vi == application.active_window
                            items.append(
                                ActionItem(
                                    action=RaiseAction(
                                        window=vi,
                                        checked=checked,
                                        name=vi.active_task.name,
                                    )
                                )
                            )
                            added.append(vi.active_task.id)
                else:
                    items.append(
                        ActionItem(
                            action=RaiseUIAction(
                                name=vi.title or vi.id, ui=vi, checked=checked
                            )
                        )
                    )

        return items

    def _rebuild(self, obj, name, old, vs):
        self.destroy()

        if name == "window_opened":
            vs = vs.window
        else:
            vs = []

        if not isinstance(vs, list):
            vs = [vs]

        self.items = self._make_actions(vs)
        self.manager.changed = True


class MyTaskWindowLaunchAction(TaskWindowLaunchAction):
    """
    modified TaskWIndowLaunchAction default behaviour

    .perform() previously created a new window on every event.

    now raise the window if its available else create it
    """

    # style = 'toggle'

    def perform(self, event):
        application = event.task.window.application
        application.open_task(self.task_id)
        self.checked = True

    @on_trait_change("task:window:opened")
    def _window_opened(self):
        if self.task:
            if self.task_id == self.task.id:
                self.checked = True

    @on_trait_change("task:window:closing")
    def _window_closed(self):
        if self.task:
            if self.task_id == self.task.id:
                # not having the desired effect. check on action remaims
                self.checked = False


class TaskGroup(Group):
    items = List


class BaseTask(Task, Loggable, PreferenceMixin):
    _full_window = False

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.init_logger()

    def _activate_task(self, tid):
        if self.window:
            for task in self.window.tasks:
                if task.id == tid:
                    break
            else:
                task = self.application.create_task(tid)
                self.window.add_task(task)

            self.window.activate_task(task)
            return task

    def toggle_full_window(self):
        if self._full_window:
            self.window.set_layout(self.default_layout)
            self.debug("set to normal view")
        else:
            self.window.set_layout(TaskLayout())
            self.debug("set full window view")

        self._full_window = not self._full_window

    def show_pane(self, p):
        op = p
        if isinstance(p, str):
            if "." in p:
                for k in self.trait_names():
                    try:
                        v = getattr(self, k)
                        if v.id == p:
                            p = v
                            break
                    except AttributeError:
                        continue

            else:
                p = getattr(self, p)

        self.debug("showing pane {} ==> {}".format(op, p))
        self._show_pane(p)

    def _show_pane(self, p):
        def _show():
            ctrl = p.control
            if ctrl:
                if not p.visible:
                    ctrl.show()
                ctrl.raise_()
            else:
                self.debug("No control for pane={}".format(p.id))

        if p:
            # self.debug('$$$$$$$$$$$$$ show pane {}'.format(p.id))
            invoke_in_main_thread(do_later, _show)

    def _menu_bar_default(self):
        view_menu = SMenu(*self._view_groups(), id="view.menu", name="&View")
        mb = SMenuBar(view_menu)
        return mb

    def _view_groups(self):
        def groupfunc(task_factory):
            gid = 0
            if hasattr(task_factory, "task_group"):
                gid = task_factory.task_group
                if gid:
                    gid = ("hardware", "experiment").index(gid) + 1
                else:
                    gid = 0

            return gid

        application = self.window.application
        groups = []
        for _, factories in groupby_key(application.task_factories, groupfunc):
            items = []
            for factory in sorted(factories, key=attrgetter("id")):
                for win in application.windows:
                    if win.active_task:
                        if win.active_task.id == factory.id:
                            checked = True
                            break
                else:
                    checked = False

                action = MyTaskWindowLaunchAction(task_id=factory.id, checked=checked)

                if hasattr(factory, "accelerator"):
                    action.accelerator = factory.accelerator
                add = True
                if hasattr(factory, "include_view_menu"):
                    add = factory.include_view_menu

                if hasattr(factory, "image"):
                    if factory.image:
                        action.image = icon(factory.image)

                if add:
                    items.append(ActionItem(action=action))

            groups.append(TaskGroup(items=items))

        return groups

    def _confirmation(self, message="", title="Save Changes?"):
        dialog = ConfirmationDialog(
            parent=self.window.control,
            message=message,
            cancel=True,
            default=CANCEL,
            title=title,
        )
        return dialog.open()

    @on_trait_change("window:opened")
    def _on_open(self, event):
        self._opened_hook()

    def _opened_hook(self):
        pass

    @on_trait_change("window:closed")
    def _on_closed(self, event):
        self._closed_hook()

    def _closed_hook(self):
        pass

    @on_trait_change("window:closing")
    def _on_close(self, event):
        """Prompt the user to save when exiting."""

        close = self._prompt_for_save()
        event.veto = not close

    def _handle_prompt_for_save(self, message, title="Save Changes?"):
        result = self._confirmation(message, title)
        if result == CANCEL:
            return False
        elif result == YES:
            return "save"

        return True

    def _prompt_for_save(self):
        return True


class BaseManagerTask(BaseTask):
    default_directory = Unicode
    default_open_action = "open"

    _default_extension = ""
    wildcard = None
    manager = Any

    def prepare_destroy(self):
        if self.manager:
            if hasattr(self.manager, "prepare_destroy"):
                self.manager.prepare_destroy()

    def activated(self):
        if self.manager:
            if hasattr(self.manager, "activate"):
                self.manager.activate()

    def view_pdf(self, p):
        self.view_file(p, application="Preview")

    def view_xls(self, p):
        application = "Microsoft Office 2011/Microsoft Excel"
        self.view_file(p, application)

    def view_csv(self, p):
        application = "TextWrangler"
        self.view_file(p, application)

    def view_file(self, p, application="Preview"):
        view_file(p, application=application, logger=self)

    def open_directory_dialog(self, **kw):
        if "default_directory" not in kw:
            kw["default_directory"] = self.default_directory

        if "wildcard" not in kw:
            if self.wildcard:
                kw["wildcard"] = self.wildcard

        dialog = DirectoryDialog(action="open", **kw)
        if dialog.open() == OK:
            r = dialog.path
            return r

    def open_file_dialog(self, action=None, wildcard_args=None, **kw):
        if "default_directory" not in kw:
            kw["default_directory"] = self.default_directory

        if wildcard_args is None:
            if "wildcard" not in kw:
                if self.wildcard:
                    kw["wildcard"] = self.wildcard
        else:
            kw["wildcard"] = FileDialog.create_wildcard(*wildcard_args)

        if action is None:
            action = self.default_open_action

        dialog = FileDialog(action=action, **kw)
        if dialog.open() == OK:
            r = dialog.path
            if action == "open files":
                r = dialog.paths
            return r

    def save_file_dialog(self, ext=None, **kw):
        if "default_directory" not in kw:
            kw["default_directory"] = self.default_directory
        dialog = FileDialog(parent=self.window.control, action="save as", **kw)
        if dialog.open() == OK:
            path = dialog.path
            if path:
                if ext is None:
                    ext = self._default_extension
                return add_extension(path, ext=ext)


class BaseExtractionLineTask(BaseManagerTask):
    canvas_pane = Instance(
        "pychron.extraction_line.tasks.extraction_line_pane.CanvasDockPane"
    )

    def _get_el_manager(self):
        app = self.window.application
        man = app.get_service(
            "pychron.extraction_line.extraction_line_manager.ExtractionLineManager"
        )
        return man

    def prepare_destroy(self):
        man = self._get_el_manager()
        if man:
            man.deactivate()

    def _add_canvas_pane(self, panes):
        man = self._get_el_manager()
        if man:
            from pychron.extraction_line.tasks.extraction_line_pane import (
                CanvasDockPane,
            )

            config = os.path.join(paths.canvas2D_dir, "alt_config.xml")
            self.canvas_pane = CanvasDockPane(canvas=man.new_canvas(config=config))
            panes.append(self.canvas_pane)

        return panes

    @on_trait_change("window:opened")
    def _window_opened(self):
        self.debug("window opened")
        man = self._get_el_manager()
        if man:
            do_after(1000, man.activate)


class BaseHardwareTask(BaseManagerTask):
    pass


# ============= EOF =============================================
