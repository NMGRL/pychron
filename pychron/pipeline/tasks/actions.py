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
import os

from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.message_dialog import information
from pyface.tasks.action.task_action import TaskAction
from traitsui.menu import Action

from pychron.envisage.resources import icon
from pychron.envisage.ui_actions import UIAction, UITaskAction
from pychron.pipeline.data_reduction_logbook import DataReductionLogbook
from pychron.pychron_constants import DVC_PROTOCOL


class EditorAction(TaskAction):
    enabled_name = "active_editor"


class FigureAction(TaskAction):
    enabled_name = "is_figure_editor"


class IdentifyPeaksDemoAction(TaskAction):
    name = "Id peaks"
    method = "identify_peaks"


class SignalEstimatorAction(Action):
    name = "Signal Estimator"

    def perform(self, event):
        app = event.task.window.application
        v = app.preferences.get("pychron.entry.j_multiplier", 0.0002)

        from pychron.processing.signal_estimator import SignalEstimator

        s = SignalEstimator()
        s.j_per_hour = float(v)
        s.edit_traits()


class IsochronSandboxAction(UIAction):
    name = "Isochron Sandbox"

    def perform(self, event):
        from pychron.pipeline.isochron_sandbox import IsochronSandbox

        s = IsochronSandbox()
        s.init()
        s.edit_traits()


class SavePipelineTemplateAction(TaskAction):
    name = "Save Pipeline Template"
    method = "save_pipeline_template"


class RunAction(TaskAction):
    name = "Run"
    method = "run"
    image = icon("start")
    visible_name = "engine.run_enabled"
    accelerator = "Ctrl+R"


class ResumeAction(TaskAction):
    name = "Resume"
    method = "resume"
    image = icon("edit-redo-3")
    visible_name = "engine.resume_enabled"


class RunFromAction(TaskAction):
    name = "Run From"
    method = "run_from"
    image = icon("start")


class ResetAction(TaskAction):
    name = "Reset"
    method = "reset"
    image = icon("arrow_refresh")


class ClearAction(TaskAction):
    name = "Clear"
    method = "clear"
    image = icon("clear")


class SwitchToBrowserAction(TaskAction):
    name = "To Browser"
    method = "switch_to_browser"
    image = icon("start")


class ConfigureRecallAction(UITaskAction):
    name = "Recall Configuration..."
    method = "configure_recall"
    image = icon("cog")


class PlayVideoAction(UITaskAction):
    name = "Video"
    method = "play_analysis_video"
    # image = icon('cog')


# class ConfigureAnalysesTableAction(TaskAction):
#     name = 'Configure Analyses Table'
#     dname = 'Configure Analyses Table'
#     method = 'configure_analyses_table'
#     image = icon('cog')
#
#
# class ConfigureSampleTableAction(TaskAction):
#     name = 'Configure Sample Table'
#     dname = 'Configure Sample Table'
#     method = 'configure_sample_table'
#     image = icon('cog')


class LoadReviewStatusAction(TaskAction):
    name = "Review Status"
    method = "load_review_status"
    image = icon("check_boxes")


class EditAnalysisAction(TaskAction):
    name = "Edit Analysis"
    method = "edit_analysis"
    image = icon("application-form-edit")


class DiffViewAction(TaskAction):
    name = "Diff View"
    method = "diff_analysis"
    image = icon("edit_diff")
    enabled_name = "diff_enabled"


class TabularViewAction(TaskAction):
    name = "Tabular View"
    method = "tabular_view"
    image = icon("table")


class PipelineAction(UIAction):
    def perform(self, event):
        app = event.task.window.application
        task = app.get_task("pychron.pipeline.task")
        if hasattr(task, self.action):
            getattr(task, self.action)()


class BrowserAction(Action):
    _task_id = "pychron.browser.task"

    def perform(self, event):
        task = self._get_task(event)
        if hasattr(task, self.action):
            getattr(task, self.action)()

    def _get_task(self, event):
        app = event.task.window.application
        task = app.get_task(self._task_id)
        return task


class RecallAction(PipelineAction):
    name = "Recall..."
    action = "pipeline_recall"


class DVCRecallAction(PipelineAction):
    name = "DVC Recall..."
    action = "pipeline_dvc_recall"


class InterpretedAgeRecallAction(PipelineAction):
    name = "Interpreted Age Recall..."
    action = "pipeline_interpreted_age_recall"


class TimeViewBrowserAction(BrowserAction):
    name = "Time View Recall..."
    action = "open_time_view_browser"


class ReductionAction(PipelineAction):
    pass


class IsoEvolutionAction(PipelineAction):
    name = "Isotope Evolutions"
    action = "set_isotope_evolutions_template"


class BlanksAction(PipelineAction):
    name = "Blanks"
    action = "set_blanks_template"


class ICFactorAction(PipelineAction):
    name = "ICFactor"
    action = "set_icfactor_template"


class FluxAction(PipelineAction):
    name = "Flux"
    action = "set_flux_template"


class FreezeProductionRatios(PipelineAction):
    name = "Freeze Production Ratios"
    action = "freeze_production_ratios"


class FreezeFlux(PipelineAction):
    name = "Freeze Flux"
    action = "freeze_flux"


class AnalysisTableAction(PipelineAction):
    name = "Analysis Table"
    action = "set_analysis_table_template"


class PipelineRecallAction(TaskAction):
    name = "Recall"
    method = "pipeline_recall"


class ClearAnalysisSetsAction(UIAction):
    name = "Clear Analysis Sets"

    def perform(self, event):
        from pychron.paths import paths

        p = paths.hidden_path("analysis_sets")
        if os.path.isfile(p):
            if (
                confirm(None, "Are you sure you want to clear the Analysis Sets?")
                == YES
            ):
                os.remove(p)
        else:
            information(None, "No Analysis Sets to remove")


# ============= Plotting Actions =============================================
class ResetFactoryDefaultsAction(UIAction):
    name = "Reset Factory Defaults"

    def perform(self, event):
        from pychron.paths import paths

        if confirm(None, "Are you sure you want to reset to Factory Default settings"):
            paths.reset_plot_factory_defaults()


class PlotAction(PipelineAction):
    pass


class IdeogramAction(PlotAction):
    name = "Ideogram"
    action = "set_ideogram_template"
    image = icon("histogram")
    accelerator = "Ctrl+i"


class SubgroupIdeogramAction(PlotAction):
    name = "SubGroup Ideogram"
    action = "set_subgroup_ideogram_template"
    image = icon("histogram")


class HybridIdeogramAction(PlotAction):
    name = "Hybrid Ideogram"
    action = "set_hybrid_ideogram_template"
    image = icon("histogram")


class HistoryIdeogramAction(PlotAction):
    name = "History Ideogram"
    action = "set_history_ideogram_template"
    image = icon("histogram")


class SpectrumAction(PlotAction):
    name = "Spectrum"
    action = "set_spectrum_template"
    accelerator = "Ctrl+D"
    # image = icon('histogram')


class IsochronAction(PlotAction):
    name = "Isochron"
    action = "set_isochron_template"
    # image = icon('histogram')


class InverseIsochronAction(PlotAction):
    name = "InverseIsochron"
    action = "set_inverse_isochron_template"


class SeriesAction(PlotAction):
    name = "Series"
    action = "set_series_template"
    id = "pychron.series"


class VerticalFluxAction(PipelineAction):
    name = "Vertical Flux"
    action = "set_vertical_flux_template"


class ExtractionAction(UIAction):
    name = "Extraction Results..."

    def perform(self, event):
        app = event.task.window.application
        windows = app.windows
        for tid in ("pychron.browser.task", "pychron.pipeline.task"):
            for win in windows:
                task = win.active_task
                if task and task.id == tid:
                    getattr(task, "show_extraction_graph")()
                    break


class MassSpecReducedAction(PipelineAction):
    name = "Mass Spec Reduced Transfer"
    action = "mass_spec_reduced_transfer"


class ImportOptionsActions(PipelineAction):
    name = "Import Options..."
    action = "import_options"


class DataReductionLogAction(UIAction):
    name = "Data Reduction Log"

    def perform(self, event):
        app = event.task.window.application
        dvc = app.get_service(DVC_PROTOCOL)
        d = DataReductionLogbook(dvc=dvc)
        d.populate()
        d.edit_traits()


# ============= Quick Series ====================================
# class LastNAnalysesSeriesAction(PipelineAction):
#     name = 'Last N...'
#     action = 'set_last_n_analyses_template'
#
#
# class LastNHoursSeriesAction(PipelineAction):
#     name = 'Last N Hours...'
#     action = 'set_last_n_hours_template'
#
#
# class LastDaySeriesAction(PipelineAction):
#     name = 'Last Day'
#     action = 'set_last_day_template'
#
#
# class LastWeekSeriesAction(PipelineAction):
#     name = 'Last Week'
#     action = 'set_last_week_template'
#
#
# class LastMonthSeriesAction(PipelineAction):
#     name = 'Last Month'
#     action = 'set_last_month_template'


# ============= tag =============================================
class TagAction(TaskAction):
    name = "Tag..."
    dname = "Tag"
    # accelerator = 'Ctrl+Shift+t'
    method = "set_tag"
    image = icon("tag-blue-add")
    id = "pychron.tag"


class SetInvalidAction(TaskAction):
    name = "Set Invalid"
    method = "set_invalid"
    image = icon("edit-delete-2")


class SetFilteringTagAction(TaskAction):
    name = "Set Filtering Tag"
    method = "set_filtering_tag"
    image = icon("flag")


# ============= Interperted Age =================================
class SetInterpretedAgeAction(TaskAction):
    name = "Set Interpreted Age"
    method = "set_interpreted_age"
    enabled_name = "set_interpreted_enabled"
    image = icon("brick-add")


class SavePDFAction(FigureAction):
    name = "Save PDF"
    method = "save_figure_pdf"
    image = icon("file_pdf")


class SaveFigureAction(FigureAction):
    name = "Save Figure"
    method = "save_figure"


class PrintFigureAction(FigureAction):
    name = "Print"
    method = "print_figure"
    image = icon("printer")


class SaveTableAction(TaskAction):
    name = "Save Table"
    method = "save_table"
    image = icon("table_save")
    enabled_name = "set_interpreted_enabled"


# ============= EOF =============================================
