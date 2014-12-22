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
# ===============================================================================

# ============= enthought library imports =======================
from pyface.action.action import Action
from pyface.tasks.action.task_action import TaskAction
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.envisage.tasks.actions import FileOpenAction, NewAction


class HopsEditorAction(Action):
    def perform(self, event):
        from pychron.pyscripts.hops_editor import HopEditorModel, HopEditorView

        application = event.task.window.application
        spec = application.get_service('pychron.spectrometer.spectrometer_manager.SpectrometerManager')
        dets = []
        if spec:
            dets = [di.name for di in spec.spectrometer.detectors]

        m = HopEditorModel(detectors=dets)
        h = HopEditorView(model=m)
        self._perform(m)
        h.edit_traits(kind='livemodal')

    def _perform(self, h):
        pass


class OpenHopsEditorAction(HopsEditorAction):
    description = 'Open existing peak hop editor'
    name = 'Open Peak Hops'
    image = icon('document-open')

    def _perform(self, m):
        m.open()


class NewHopsEditorAction(HopsEditorAction):
    description = 'Open new peak hop editor'
    name = 'New Peak Hops'
    # image = icon('document-new')

    def _perform(self, m):
        m.new()


class OpenPyScriptAction(FileOpenAction):
    """
    """
    id = 'pychron.open_pyscript'
    description = 'Open pyscript'
    name = 'Open Script...'
    # accelerator = 'Ctrl+Shift+O'
    image = icon('document-open')
    task_id = 'pychron.pyscript.task'
    # test_path = '/Users/ross/Pychrondata_dev/scripts/extraction/jan_pause.py'
    test_path = '/Users/ross/Pychrondata_dev/scripts/measurement/jan_unknown.py'
    # test_path = '/Users/argonlab2/Pychrondata_view/scripts/measurement/obama_analysis400_120.py'


class NewPyScriptAction(NewAction):
    """
    """
    description = 'New pyscript'
    name = 'New Script'
    task_id = 'pychron.pyscript.task'
    id = 'pychron.new_pyscript'
    #    accelerator = 'Shift+Ctrl+O'
    #     image = icon('script-new')
    # def perform(self, event):
    #     if event.task.id == 'pychron.pyscript':
    #         task = event.task
    #         task.new()
    #     else:
    #         application = event.task.window.application
    #         win = application.create_window(TaskWindowLayout('pychron.pyscript'))
    #         task = win.active_task
    #         if task.new():
    #             win.open()


class JumpToGosubAction(TaskAction):
    name = 'Jump to Gosub'
    image = icon('script_go')
    method = 'jump_to_gosub'
    tooltip = 'Jump to gosub defined at the current line. CMD+click on a gosub will also work.'

# ============= EOF =============================================
