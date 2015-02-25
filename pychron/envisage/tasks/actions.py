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

from pyface.tasks.task_window_layout import TaskWindowLayout
from traits.api import Any, List
from pyface.action.action import Action
from pyface.tasks.action.task_action import TaskAction
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
# ============= standard library imports ========================
import os
import shutil
import sys
# ============= local library imports  ==========================
from pychron.envisage.resources import icon

# from pychron.processing.tasks.actions.processing_actions import myTaskAction


# ===============================================================================
# help
# ===============================================================================
from pychron.envisage.user_login import login_file


def restart():
    os.execl(sys.executable, *([sys.executable] + sys.argv))


def get_key_binding(k_id):
    from pychron.envisage.key_bindings import user_key_map

    try:
        return user_key_map[k_id][0]
    except KeyError:
        pass


class myTaskAction(TaskAction):
    task_ids = List

    def _task_changed(self):
        if self.task:
            if self.task.id in self.task_ids:
                enabled = True
                if self.enabled_name:
                    if self.object:
                        enabled = bool(self._get_attr(self.object,
                                                      self.enabled_name, False))
                if enabled:
                    self._enabled = True
            else:
                self._enabled = False

    def _enabled_update(self):
        """
             reimplement ListeningAction's _enabled_update
        """
        if self.enabled_name:
            if self.object:
                self.enabled = bool(self._get_attr(self.object,
                                                   self.enabled_name, False))
            else:
                self.enabled = False
        elif self._enabled is not None:
            self.enabled = self._enabled
        else:
            self.enabled = bool(self.object)


class PAction(Action):
    def __init__(self, *args, **kw):
        super(PAction, self).__init__(*args, **kw)
        acc = get_key_binding(self.id)
        self.accelerator = acc or self.accelerator


class PTaskAction(TaskAction):
    def __init__(self, *args, **kw):
        super(PTaskAction, self).__init__(*args, **kw)
        acc = get_key_binding(self.id)
        self.accelerator = acc or self.accelerator


class DemoAction(Action):
    name = 'Demo'
    accelerator = 'Shift+Ctrl+0'

    def perform(self, event):
        app = event.task.application
        app.info('Demo message: {}'.format('Hello version 1.3'))


class StartupTestsAction(Action):
    name = 'Run Startup Tests'
    def perform(self, event):
        app = event.task.application
        from pychron.globals import globalv

        ov = globalv.use_startup_tests
        globalv.use_startup_tests = True

        for plugin in app.plugin_manager:
            if hasattr(plugin, 'startup_test'):
                plugin.startup_test()

        globalv.use_startup_tests = ov

        st = app.startup_tester
        if st.results:
            from pychron.startup_test.results_view import ResultsView

            v = ResultsView(model=st,
                            _cancel_auto_close=True,
                            can_cancel=False)
            app.open_view(v)

class KeyBindingsAction(PAction):
    name = 'Edit Key Bindings'

    def perform(self, event):
        from pychron.envisage.key_bindings import edit_key_bindings

        edit_key_bindings()


class UserAction(PAction):
    def _get_current_user(self, event):
        app = event.task.application
        args = app.id.split('.')
        cuser = args[-1]
        base_id = '.'.join(args[:-1])
        return base_id, cuser


class SwitchUserAction(UserAction):
    name = 'Switch User'
    image = icon('user_suit')

    def perform(self, event):
        from pychron.envisage.user_login import get_user

        base_id, cuser = self._get_current_user(event)
        user = get_user(current=cuser)
        if user:
            # from pychron.paths import paths
            # set login file
            with open(login_file, 'w') as fp:
                fp.write(user)
            restart()


class CopyPreferencesAction(UserAction):
    name = 'Copy Preferences'

    def perform(self, event):
        from pychron.envisage.user_login import get_src_dest_user

        base_id, cuser = self._get_current_user(event)
        src_name, dest_names = get_src_dest_user(cuser)

        if src_name:

            for di in dest_names:
                dest_id = '{}.{}'.format(base_id, di)
                src_id = '{}.{}'.format(base_id, src_name)

                root = os.path.join(os.path.expanduser('~'), '.enthought')

                src_dir = os.path.join(root, src_id)
                dest_dir = os.path.join(root, dest_id)
                if not os.path.isdir(dest_dir):
                    os.mkdir(dest_dir)

                name = 'preferences.ini'
                dest = os.path.join(dest_dir, name)
                src = os.path.join(src_dir, name)
                shutil.copyfile(src, dest)


class RestartAction(PAction):
    name = 'Restart'
    image = icon('system-restart')

    def perform(self, event):
        restart()


class WebAction(PAction):
    def _open_url(self, url):

        import webbrowser
        import urllib2

        try:
            urllib2.urlopen(url)
        except (urllib2.HTTPError, urllib2.URLError):
            return

        webbrowser.open_new(url)


class IssueAction(WebAction):
    name = 'Add Request/Report Bug'
    image = icon('bug')

    def perform(self, event):
        """
            goto issues page add an request or report bug
        """
        url = 'https://github.com/NMGRL/pychron/issues/new'
        self._open_url(url)


class NoteAction(WebAction):
    name = 'Add Laboratory Note'
    image = icon('insert-comment')

    def perform(self, event):
        """
            goto issues page add an request or report bug
        """
        app = event.task.window.application
        name = app.preferences.get('pychron.general.remote')
        if not name:
            name = 'NMGRL/Laboratory'

        url = 'https://github.com/{}/issues/new'.format(name)
        self._open_url(url)


class DocumentationAction(WebAction):
    name = 'View Documentation'
    image = icon('documentation')

    def perform(self, event):
        """
            goto issues page add an request or report bug
        """
        url = 'http://pychron.readthedocs.org/en/latest/index.html'
        self._open_url(url)


class ChangeLogAction(WebAction):
    name = "What's New"
    image = icon('documentation')
    description = 'View changelog'


    def perform(self, event):
        """
            goto issues page add an request or report bug
        """
        from pychron.version import __version__
        url = 'https://github.com/NMGRL/pychron/blob/release/v{}/CHANGELOG.md'.format(__version__)
        if not self._open_url(url):
            url = 'https://github.com/NMGRL/pychron/blob/develop/CHANGELOG.md'
            self._open_url(url)


class AboutAction(PAction):
    name = 'About Pychron'

    def perform(self, event):
        app = event.task.window.application
        app.about()


class ResetLayoutAction(PTaskAction):
    name = 'Reset Layout'
    image = icon('view-restore')

    def perform(self, event):
        self.task.window.reset_layout()


class PositionAction(PAction):
    name = 'Window Positions'
    image = icon('window-new')

    def perform(self, event):
        from pychron.envisage.tasks.layout_manager import LayoutManager

        app = event.task.window.application
        lm = LayoutManager(app)
        lm.edit_traits()


class MinimizeAction(PTaskAction):
    name = 'Minimize'
    accelerator = 'Ctrl+m'

    def perform(self, event):
        app = self.task.window.application
        app.active_window.control.showMinimized()


class CloseAction(PTaskAction):
    name = 'Close'
    accelerator = 'Ctrl+W'

    def perform(self, event):
        ok = YES
        if len(self.task.window.application.windows) == 1:
            ok = confirm(self.task.window.control, message='Quit Pychron?')

        if ok == YES:
            self.task.window.close()


class CloseOthersAction(PTaskAction):
    name = 'Close others'
    accelerator = 'Ctrl+Shift+W'

    def perform(self, event):
        win = self.task.window
        for wi in self.task.window.application.windows:
            if wi != win:
                wi.close()


class OpenAdditionalWindow(PTaskAction):
    name = 'Open Additional Window'
    description = 'Open an additional window of the current active task'

    def perform(self, event):
        app = self.task.window.application
        win = app.create_window(TaskWindowLayout(self.task.id))
        win.open()


class RaiseAction(PTaskAction):
    window = Any
    style = 'toggle'

    def perform(self, event):
        self.window.activate()
        self.checked = True

    # @on_trait_change('window:deactivated')
    # def _on_deactivate(self):
    #     self.checked = False


class RaiseUIAction(PTaskAction):
    style = 'toggle'

    def perform(self, event):
        self.checked = True


class GenericSaveAction(PTaskAction):
    name = 'Save'
    accelerator = 'Ctrl+S'
    image = icon('document-save')

    def perform(self, event):
        task = self.task
        if hasattr(task, 'save'):
            task.save()


class GenericSaveAsAction(PTaskAction):
    name = 'Save As...'
    accelerator = 'Ctrl+Shift+S'
    image = icon('document-save-as')

    def perform(self, event):
        task = self.task
        if hasattr(task, 'save_as'):
            task.save_as()


class GenericFindAction(PTaskAction):
    accelerator = 'Ctrl+F'
    name = 'Find text...'

    def perform(self, event):
        task = self.task
        if hasattr(task, 'find'):
            task.find()


class FileOpenAction(PAction):
    task_id = ''
    test_path = ''
    image = icon('document-open')

    def perform(self, event):
        if event.task.id == self.task_id:
            task = event.task
            task.open()
        else:
            application = event.task.window.application
            win = application.create_window(TaskWindowLayout(self.task_id))
            task = win.active_task
            if task.open(path=self.test_path):
                win.open()


class NewAction(PAction):
    task_id = ''

    def perform(self, event):
        if event.task.id == self.task_id:
            task = event.task
            task.new()
        else:
            application = event.task.window.application
            win = application.create_window(TaskWindowLayout(self.task_id))
            task = win.active_task
            if task.new():
                win.open()


# class GenericReplaceAction(TaskAction):
#    pass
#        else:
#            manager = self._get_experimentor(event)
#            manager.save_as_experiment_queues()

class ToggleFullWindowAction(myTaskAction):
    name = 'Toggle Full Window'
    method = 'toggle_full_window'
    image = icon('view-fullscreen-8')
    task_ids = ['pychron.recall', 'pychron.labbook', 'pychron.processing.figures']


class EditInitializationAction(Action):
    name = 'Edit Initialization'
    image = icon('brick-edit')

    def perform(self, event):
        from pychron.envisage.initialization.initialization_edit_view import edit_initialization

        if edit_initialization():
            restart()

# ============= EOF =============================================
