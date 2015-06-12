# ===============================================================================
# Copyright 2015 Jake Ross
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
from pyface.tasks.action.task_action import TaskAction
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.menu import Action
from pychron.envisage.resources import icon


class GitRollbackAction(TaskAction):
    name = 'Git Undo'
    method = 'git_rollback'


class SavePipelineTemplateAction(TaskAction):
    name = 'Save Pipeline Template'
    method = 'save_pipeline_template'


class RunAction(TaskAction):
    name = 'Run'
    method = 'run'
    image = icon('start')
    visible_name = 'run_enabled'


class ResumeAction(TaskAction):
    name = 'Resume'
    method = 'run'
    image = icon('resume')
    visible_name = 'resume_enabled'


class ResetAction(TaskAction):
    name = 'Reset'
    method = 'reset'
    image = icon('resume')
    # enabled_name = 'resume_enabled'


class SwitchToBrowserAction(TaskAction):
    name = 'To Browser'
    method = 'switch_to_browser'
    image = icon('start')


class ConfigureRecallAction(TaskAction):
    name = 'Configure Recall'
    dname = 'Configure Recall'
    method = 'configure_recall'
    image = icon('cog')


# ============= Plotting Actions =============================================
class PlotAction(Action):
    def perform(self, event):
        app = event.task.window.application
        task = app.get_task('pychron.pipeline.task')
        if hasattr(task, self.action):
            getattr(task, self.action)()


class IdeogramAction(PlotAction):
    name = 'Ideogram'
    action = 'set_ideogram_template'
    image = icon('histogram')


class SpectrumAction(PlotAction):
    name = 'Spectrum'
    action = 'set_spectrum_template'
    # image = icon('histogram')


class IsochronAction(PlotAction):
    name = 'Isochron'
    action = 'set_isochron_template'
    # image = icon('histogram')

# ============= EOF =============================================
