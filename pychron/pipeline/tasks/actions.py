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
from pyface.confirmation_dialog import confirm
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
    accelerator = 'Ctrl+R'


class ResumeAction(TaskAction):
    name = 'Resume'
    method = 'resume'
    image = icon('resume')
    visible_name = 'resume_enabled'


class RunFromAction(TaskAction):
    name = 'Run From'
    method = 'run_from'


class ResetAction(TaskAction):
    name = 'Reset'
    method = 'reset'
    image = icon('resume')
    # enabled_name = 'resume_enabled'


class ClearAction(TaskAction):
    name = 'Clear'
    method = 'clear'
    image = icon('clear')


class SwitchToBrowserAction(TaskAction):
    name = 'To Browser'
    method = 'switch_to_browser'
    image = icon('start')


class ConfigureRecallAction(TaskAction):
    name = 'Configure Recall'
    dname = 'Configure Recall'
    method = 'configure_recall'
    image = icon('cog')


class PipelineAction(Action):
    def perform(self, event):
        app = event.task.window.application
        task = app.get_task('pychron.pipeline.task')
        if hasattr(task, self.action):
            getattr(task, self.action)()


class ReductionAction(PipelineAction):
    pass


class BlanksAction(PipelineAction):
    name = 'Blanks'
    dname = 'Blanks'


class ICFactorAction(PipelineAction):
    name = 'ICFactor'
    dname = 'ICFactor'


# ============= Plotting Actions =============================================
class ResetFactoryDefaultsAction(Action):
    name = 'Reset Factory Defaults'

    def perform(self, event):
        from pychron.paths import paths
        if confirm(None, 'Are you sure you want to reset to Factory Default settings'):
            paths.reset_plot_factory_defaults()


class PlotAction(PipelineAction):
    pass


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


class SeriesAction(PlotAction):
    name = 'Series'
    dname = 'Series'
    action = 'set_series_template'
    id = 'pychron.series'


# ============= tag =============================================
class TagAction(TaskAction):
    name = 'Tag...'
    dname = 'Tag'
    # accelerator = 'Ctrl+Shift+t'
    method = 'set_tag'
    image = icon('tag-blue-add')
    id = 'pychron.tag'


# ============= Interperted Age =================================
class SetInterpretedAgeAction(TaskAction):
    name = 'Set Interpreted Age'
    method = 'set_interpreted_age'
    enabled_name = 'set_interpreted_enabled'


class SavePDFAction(TaskAction):
    name = 'Save PDF'
    method = 'save_figure_pdf'
    image = icon('file_pdf')

# ============= EOF =============================================
