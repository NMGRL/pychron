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
from pyface.action.action import Action
from pyface.image_resource import ImageResource
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_window_layout import TaskWindowLayout
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths


class OpenPyScriptAction(Action):
    """
    """
    description = 'Open pyscript'
    name = 'Open Script...'
    accelerator = 'Ctrl+Shift+O'

    def perform(self, event):
        if event.task.id == 'pychron.pyscript':
            task = event.task
            task.open()
        else:
            application = event.task.window.application
            win = application.create_window(TaskWindowLayout('pychron.pyscript',
                                                             size=(1200, 100)
                                                             ))
            task = win.active_task
            test_path='/Users/ross/Pychrondata_dev/scripts/extraction/jan_pause.py'
            # test_path='/Users/ross/Pychrondata_dev/scripts/measurement/jan_unknown.py'
            if task.open(path=test_path):
                win.open()

class NewPyScriptAction(Action):
    """
    """
    description = 'New pyscript'
    name = 'New Script'
#    accelerator = 'Shift+Ctrl+O'

    def perform(self, event):
        if event.task.id == 'pychron.pyscript':
            task = event.task
            task.new()
        else:
            application = event.task.window.application
            win = application.create_window(TaskWindowLayout('pychron.pyscript'))
            task = win.active_task
            if task.new():
                win.open()


class JumpToGosubAction(TaskAction):
    name='Jump to Gosub'
    image = ImageResource(name='script_go', search_path=paths.icon_search_path)
    method='jump_to_gosub'
    tooltip = 'Jump to gosub defined at the current line. CMD+click on a gosub will also work.'
#============= EOF =============================================
