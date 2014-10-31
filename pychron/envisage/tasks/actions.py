# ===============================================================================
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
import os
import shutil
from pyface.tasks.task_window_layout import TaskWindowLayout
import sys
from traits.api import on_trait_change, Any
from pyface.action.action import Action
from pyface.tasks.action.task_action import TaskAction
#============= standard library imports ========================
#============= local library imports  ==========================

import webbrowser
from pyface.confirmation_dialog import confirm
from pyface.constant import YES

#===============================================================================
# help
#===============================================================================
from pychron.envisage.resources import icon


class CopyPreferencesAction(Action):
    name = 'Copy Preferences'
    def perform(self, event):
        from pychron.envisage.user_login import get_src_dest_user
        app = event.task.application
        args = app.id.split('.')
        cuser = args[-1]
        base_id= '.'.join(args[:-1])
        src_name, dest_name = get_src_dest_user(cuser)

        if src_name:


            dest_id = '{}.{}'.format(base_id,dest_name)
            src_id = '{}.{}'.format(base_id, src_name)

            root = os.path.join(os.path.expanduser('~'), '.enthought')

            src_dir = os.path.join(root, src_id)
            dest_dir = os.path.join(root, dest_id)
            if not os.path.isdir(dest_dir):
                os.mkdir(dest_dir)

            name = 'preferences.ini'
            dest=os.path.join(dest_dir, name)
            src = os.path.join(src_dir, name)
            print 'writing {} to {}'.format(src, dest)
            shutil.copyfile(src, dest)

class RestartAction(Action):
    name = 'Restart'
    def perform(self, event):
        os.execl(sys.executable, *([sys.executable]+sys.argv))


class WebAction(Action):
    def _open_url(self, url):
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
        url = 'https://github.com/NMGRL/Laboratory/issues/new'
        self._open_url(url)


class DocumentationAction(WebAction):
    name = 'View Documentation'
    # image = icon('insert-comment')

    def perform(self, event):
        """
            goto issues page add an request or report bug
        """
        url = 'http://pychron.readthedocs.org/en/latest/index.html'
        self._open_url(url)


class AboutAction(Action):
    name = 'About Pychron'

    def perform(self, event):
        app = event.task.window.application
        app.about()


class ResetLayoutAction(TaskAction):
    name = 'Reset Layout'
    image = icon('view-restore')

    def perform(self, event):
        self.task.window.reset_layout()


class PositionAction(Action):
    name = 'Window Positions'
    image = icon('window-new')

    def perform(self, event):
        from pychron.envisage.tasks.layout_manager import LayoutManager

        app = event.task.window.application
        lm = LayoutManager(app)
        lm.edit_traits()


class MinimizeAction(TaskAction):
    name = 'Minimize'
    accelerator = 'Ctrl+m'

    def perform(self, event):
        app = self.task.window.application
        app.active_window.control.showMinimized()


class CloseAction(TaskAction):
    name = 'Close'
    accelerator = 'Ctrl+W'

    def perform(self, event):
        ok = YES
        if len(self.task.window.application.windows) == 1:
            ok = confirm(self.task.window.control, message='Quit Pychron?')

        if ok == YES:
            self.task.window.close()


class CloseOthersAction(TaskAction):
    name = 'Close others'
    accelerator = 'Ctrl+Shift+W'

    def perform(self, event):
        win = self.task.window
        for wi in self.task.window.application.windows:
            if wi != win:
                wi.close()


class OpenAdditionalWindow(TaskAction):
    name = 'Open Additional Window'
    description = 'Open an additional window of the current active task'

    def perform(self, event):
        app = self.task.window.application
        win = app.create_window(TaskWindowLayout(self.task.id))
        win.open()


class RaiseAction(TaskAction):
    window = Any
    style = 'toggle'

    def perform(self, event):
        self.window.activate()
        self.checked = True

    @on_trait_change('window:deactivated')
    def _on_deactivate(self):
        self.checked = False


class RaiseUIAction(TaskAction):
    style = 'toggle'

    def perform(self, event):
        self.checked = True


class GenericSaveAction(TaskAction):
    name = 'Save'
    accelerator = 'Ctrl+S'
    image = icon('document-save')

    def perform(self, event):
        task = self.task
        if hasattr(task, 'save'):
            task.save()


class GenericSaveAsAction(TaskAction):
    name = 'Save As...'
    accelerator = 'Ctrl+Shift+S'
    image = icon('document-save-as')

    def perform(self, event):
        task = self.task
        if hasattr(task, 'save_as'):
            task.save_as()


class GenericFindAction(TaskAction):
    accelerator = 'Ctrl+F'
    name = 'Find text...'

    def perform(self, event):
        task = self.task
        if hasattr(task, 'find'):
            task.find()


class FileOpenAction(Action):
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


class NewAction(Action):
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

#============= EOF =============================================
