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

import os

from pyface.tasks.action.schema import SToolBar, SMenu
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter

# ============= enthought library imports =======================
from traits.api import Instance, Bool, on_trait_change, Any

from pychron.core.pdf.save_pdf_dialog import save_pdf

# from pychron.core.printer.printer import print_component
from pychron.dvc import dvc_dump
from pychron.dvc.func import repository_has_staged
from pychron.dvc.simple_recaller import SimpleDVCRecaller
from pychron.dvc.util import DVCInterpretedAge
from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.envisage.browser.recall_editor import RecallEditor
from pychron.envisage.browser.view import InterpretedAgeBrowserView
from pychron.globals import globalv
from pychron.options.options_manager import options_load_json
from pychron.paths import paths
from pychron.pipeline.engine import PipelineEngine, Pipeline, NodeGroup
from pychron.pipeline.nodes.figure import FigureNode
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.editors.interpreted_age_editor import InterpretedAgeEditor
from pychron.pipeline.save_figure import SaveFigureView, SaveFigureModel
from pychron.pipeline.state import EngineState
from pychron.pipeline.tasks.actions import (
    RunAction,
    ResumeAction,
    ResetAction,
    ConfigureRecallAction,
    TagAction,
    SetInterpretedAgeAction,
    ClearAction,
    SavePDFAction,
    SetInvalidAction,
    SetFilteringTagAction,
    EditAnalysisAction,
    RunFromAction,
    PipelineRecallAction,
    LoadReviewStatusAction,
    DiffViewAction,
    SaveTableAction,
    PrintFigureAction,
    PlayVideoAction,
)
from pychron.pipeline.tasks.interpreted_age_factory import set_interpreted_age
from pychron.pipeline.tasks.panes import (
    PipelinePane,
    AnalysesPane,
    RepositoryPane,
    EditorOptionsPane,
)
from pychron.pychron_constants import PLATEAU, ISOCHRON, WEIGHTED_MEAN, MSEM


class DataMenu(SMenu):
    id = "data.menu"
    name = "Data"


class PipelineTask(BaseBrowserTask):
    name = "Pipeline Data Processing"
    engine = Instance(PipelineEngine)

    tool_bars = [
        SToolBar(
            PipelineRecallAction(),
            ConfigureRecallAction(),
            PlayVideoAction(),
            name="Recall",
        ),
        SToolBar(
            RunAction(),
            ResumeAction(),
            RunFromAction(),
            ResetAction(),
            ClearAction(),
            # SavePipelineTemplateAction(),
            name="Pipeline",
        ),
        SToolBar(
            SavePDFAction(),
            # SaveFigureAction(),
            PrintFigureAction(),
            name="Save",
        ),
        SToolBar(EditAnalysisAction(), name="Edit"),
        SToolBar(LoadReviewStatusAction(), DiffViewAction(), name="View"),
        SToolBar(
            TagAction(),
            SetInvalidAction(),
            SetFilteringTagAction(),
            SetInterpretedAgeAction(),
            SaveTableAction(),
            name="Misc",
        ),
    ]

    state = Instance(EngineState)
    set_interpreted_enabled = Bool(False)
    active_editor_options = Any

    modified = False
    projects = None
    diff_enabled = Bool
    is_figure_editor = Bool

    _browser_info = None
    _interpreted_age_browser_info = None

    def activated(self):
        # 2=a
        self.debug("activating pipeline")
        super(PipelineTask, self).activated()

        self.engine.dvc = self.dvc
        self.browser_model.dvc = self.dvc
        self.browser_model.table.dvc = self.dvc

        self.engine.browser_model = self.browser_model
        self.engine.interpreted_age_browser_model = self.interpreted_age_browser_model

    def _debug(self):
        # self.engine.add_data()
        # if globalv.select_default_data:
        #     self.engine.select_default()

        if globalv.pipeline_template:
            self.engine.set_template(globalv.pipeline_template)
            if globalv.run_pipeline:
                self.run()

    def prepare_destroy(self):
        self.interpreted_age_browser_model.dump_browser()
        self.engine.reset()

        super(PipelineTask, self).prepare_destroy()

    def create_dock_panes(self):
        self.analyses_pane = AnalysesPane(model=self.engine)

        panes = [
            PipelinePane(model=self.engine),
            self.analyses_pane,
            RepositoryPane(model=self.engine),
            EditorOptionsPane(model=self),
        ]
        return panes

    def identify_peaks(self):
        ps = [924]
        self.engine.identify_peaks(ps)

    # toolbar actions
    # def run_script(self):
    #     path = self.open_file_dialog()
    #     if path is not None:
    #         script = DataReductionScript()
    #         script.dvc = self.dvc
    #         script.run(path)

    def diff_analysis(self):
        self.debug("diff analysis")
        if not self.has_active_editor():
            return

        active_editor = self.active_editor
        if not isinstance(active_editor, RecallEditor):
            self.warning_dialog("Active tab must be a Recall tab")
            return

        left = active_editor.analysis

        recaller = self.application.get_service(
            "pychron.mass_spec.mass_spec_recaller.MassSpecRecaller"
        )
        if recaller is None:
            self.warning_dialog("Could not access MassSpec database")
            return

        if not recaller.connect():
            self.warning_dialog(
                "Could not connect to MassSpec database. {}".format(
                    recaller.db.datasource_url
                )
            )
            return

        from pychron.pipeline.editors.diff_editor import DiffEditor

        editor = DiffEditor(recaller=recaller)

        if not left.check_has_n():
            left.load_raw_data(n_only=True)

        if editor.setup(left):
            editor.set_diff(left)
            self._open_editor(editor)
        else:
            self.warning_dialog(
                "Failed to locate analysis {} in MassSpec database".format(
                    left.record_id
                )
            )

    def pipeline_dvc_recall(self):
        v = SimpleDVCRecaller()
        while 1:
            info = v.edit_traits()
            if info.result:
                record = v.record
                potential = self.dvc.find_record(record)
                if potential:
                    if len(potential) > 1:
                        self.warning_dialog(
                            'More than one analysis matches the entered uuid "{}".'
                            "Please enter more characters of the uuid".format(
                                record.uuid
                            )
                        )
                    else:
                        self.debug(
                            "Found record. RunID={}, UUID={}".format(
                                record.record_id, record.uuid
                            )
                        )
                        self.recall((record,), use_quick=False)
                        break
                else:
                    self.warning_dialog(
                        "No records found matching {}".format(record.uuid)
                    )
            else:
                break

    def pipeline_recall(self):
        if self._browser_info:
            if self._browser_info.control:
                self._browser_info.control.raise_()
                return

        self.dvc.create_session(force=True)

        self.browser_model.activated()

        # browser_view = SampleBrowserView(model=self.browser_model)

        info = self.browser_model.browser_view.edit_traits(kind="live")
        self._browser_info = info

    def pipeline_interpreted_age_recall(self):
        if self._interpreted_age_browser_info:
            if self._interpreted_age_browser_info.control:
                self._interpreted_age_browser_info.control.raise_()
                return

        self.interpreted_age_browser_model.activated()
        browser_view = InterpretedAgeBrowserView(
            model=self.interpreted_age_browser_model
        )
        info = browser_view.edit_traits(kind="live")
        self._interpreted_age_browser_info = info

    def tabular_view(self):
        self.debug("open tabular view")
        if not self.has_active_editor():
            return

        ed = self.active_editor
        from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor

        if isinstance(ed, IdeogramEditor):
            from pychron.pipeline.editors.fusion.fusion_table_editor import (
                FusionTableEditor,
            )

            ted = FusionTableEditor()
            ted.items = ed.analyses
            self._open_editor(ted)

    def set_filtering_tag(self):
        ans = self.engine.selected.unknowns
        refs = self.engine.selected.references
        ans.extend(refs)

        omit_ans = [ai for ai in ans if ai.temp_status == "omit" and ai.tag != "omit"]
        outlier_ans = [
            ai for ai in ans if ai.temp_status == "outlier" and ai.tag != "outlier"
        ]
        invalid_ans = [
            ai for ai in ans if ai.temp_status == "invalid" and ai.tag != "invalid"
        ]
        self.set_tag("omit", omit_ans, use_filter=False)
        self.set_tag("outlier", outlier_ans, use_filter=False)
        self.set_tag("invalid", invalid_ans)

    def set_tag(self, tag=None, items=None, use_filter=True, warn=True):
        """
        set tag for either
        analyses selected in unknowns pane
        or
        analyses selected in figure e.g temp_status!=0

        """
        if items is None:
            items = self._get_selection()
            if not items:
                if warn:
                    self.warning_dialog("No analyses selected to Tag")
                return

        note = ""
        if items:
            if tag is None:
                a = self._get_tagname(items)
                if a:
                    tag, items, use_filter, note = a

            # set tags for items
            if tag and items:
                # tags stored as lowercase
                tag = tag.lower()
                try:
                    self.dvc.tag_items(tag, items, note)
                except BaseException as e:
                    self.debug_exception()
                    if self.confirmation_dialog(
                        "Any error occurred trying to tag the analyses. You may not have "
                        "sufficient privileges to UPDATE the database. Contact your DB "
                        "administrator. Would you like to try to report the error to Pychron "
                        "developers?"
                    ):
                        raise e

                if use_filter:
                    for e in self.editor_area.editors:
                        if hasattr(e, "set_items"):
                            try:
                                ans = e.items
                            except AttributeError:
                                ans = e.analyses

                            if ans:
                                fans = [ai for ai in ans if ai.tag.lower() != "invalid"]
                                e.set_items(fans)

                if self.active_editor:
                    self.active_editor.figure_model = None
                    self.active_editor.refresh_needed = True

                self.browser_model.table.set_tags(tag, items)
                self.browser_model.table.remove_invalid()
                self.engine.remove_invalid()

    def set_invalid(self):
        items = self._get_selection()
        self._set_invalid(items)

    def save_figure(self):
        self.debug("save figure")
        if not self.has_active_editor():
            return

        ed = self.active_editor
        root = paths.figure_dir
        path = os.path.join(root, "test.json")
        obj = self._make_save_figure_object(ed)
        dvc_dump(obj, path)

    def save_table(self):
        self.debug("save table")
        if not self.has_active_editor():
            return

        ed = self.active_editor
        if isinstance(ed, InterpretedAgeEditor):
            from pychron.pipeline.tables.xlsx_table_options import (
                XLSXAnalysisTableWriterOptions,
            )
            from pychron.pipeline.tables.xlsx_table_writer import (
                XLSXAnalysisTableWriter,
            )

            from pychron.pipeline.plot.editors.isochron_editor import (
                InverseIsochronEditor,
            )
            from pychron.pipeline.plot.editors.spectrum_editor import SpectrumEditor

            ek = ed.plotter_options.error_calc_method
            pk = WEIGHTED_MEAN
            if isinstance(ed, SpectrumEditor):
                pk = PLATEAU
            elif isinstance(ed, InverseIsochronEditor):
                pk = ISOCHRON

            options = XLSXAnalysisTableWriterOptions()
            ri = tuple({ai.repository_identifier for ai in ed.analyses})
            options.root_name = ri[0]
            info = options.edit_traits(kind="modal")
            if info.result:
                writer = XLSXAnalysisTableWriter()
                gs = ed.get_analysis_groups()

                # convert each group to an InterpretedAgeGroup
                from pychron.processing.analyses.analysis_group import (
                    InterpretedAgeGroup,
                )

                ggs = []
                for gi in gs:
                    gg = InterpretedAgeGroup(analyses=gi.analyses)
                    gg.set_preferred_age(pk, ek)
                    gg.set_preferred_kind("kca", WEIGHTED_MEAN, MSEM)
                    ggs.append(gg)

                run_groups = {"unknowns": ggs, "machine_unknowns": ggs}
                writer.build(run_groups, options=options)

    def print_figure(self):
        self.debug("print figure")
        if not self.has_active_editor():
            return

        self.warning_dialog("Printing is not supported in this version")
        # ed = self.active_editor
        # if isinstance(ed, FigureEditor):
        #     print_component(ed.component)

    def save_figure_pdf(self):
        self.debug("save figure pdf")
        if not self.has_active_editor():
            return

        ed = self.active_editor
        if isinstance(ed, FigureEditor):
            sfm = SaveFigureModel(ed.analyses)
            sfv = SaveFigureView(model=sfm)
            info = sfv.edit_traits()
            if info.result:
                path = sfm.prepare_path(make=True)
                save_pdf(ed.component, path=path, options=sfm.pdf_options, view=True)

    def run(self):
        self._run_pipeline()

    def resume(self):
        self._resume_pipeline()

    def run_from(self):
        self._run_from_pipeline()

    def set_interpreted_age(self):
        ias = self.active_editor.get_interpreted_ages()
        set_interpreted_age(self.dvc, ias)

    def clear(self):
        self.reset()
        self.engine.clear()
        self.close_all()

    def reset(self):
        self.engine.run_enabled = True
        self.engine.resume_enabled = False
        self.engine.reset()

    def save_pipeline_template(self):
        self.engine.save_pipeline_template()

    # action handlers
    def import_options(self):
        p = self.open_file_dialog(
            default_directory=os.path.join(paths.home, "Desktop"),
            wildcard_args=("JSON", "*.json"),
        )
        if p and os.path.isfile(p):
            try:
                obj = options_load_json(p)
            except BaseException as e:
                self.debug("invalid options json file. {}".format(e))
                self.information_dialog("Failed adding {}".format(p))
                return

            if obj.manager_id:
                op = os.path.join(
                    paths.plotter_options_dir,
                    globalv.username,
                    obj.manager_id,
                    "{}.json".format(obj.name),
                )
                self.debug("dumping to {}".format(op))
                with open(op, "w") as wfile:
                    obj.dump(wfile)
                self.information_dialog(
                    "Options {} added successfully".format(obj.name)
                )
            else:
                self.information_dialog(
                    "Failed adding {}. Manager ID missing from file".format(p)
                )

    def edit_runid(self):
        self._set_action_template("Edit RunID")

    def mass_spec_reduced_transfer(self):
        self._set_action_template("Mass Spec Reduced")

    def freeze_flux(self):
        ans = self._get_active_analyses()
        if ans:
            self.dvc.freeze_flux()
        else:
            self._set_action_template("FreezeFlux")

    def freeze_production_ratios(self):
        ans = self._get_active_analyses()
        if ans:
            self.dvc.freeze_production_ratios(ans)
        else:
            self._set_action_template("FreezeProductionRatios")

    def set_isotope_evolutions_template(self):
        self._set_action_template("Iso Evo")

    def set_icfactor_template(self):
        self._set_action_template("IC Factor")

    def set_blanks_template(self):
        self._set_action_template("Blanks")

    def set_flux_template(self):
        self._set_action_template("Flux")

    def set_ideogram_template(self):
        self._set_action_template("Ideogram", "Plot")

    def set_spectrum_template(self):
        self._set_action_template("Spectrum", "Plot")

    def set_isochron_template(self):
        self._set_action_template("Isochron")

    def set_inverse_isochron_template(self):
        self._set_action_template("InverseIsochron")

    def set_series_template(self):
        self._set_action_template("Series")

    def set_vertical_flux_template(self):
        self._set_action_template("VerticalFlux")

    def set_xy_scatter_template(self):
        self._set_action_template("XYScatter")

    def set_subgroup_ideogram_template(self):
        self._set_action_template("SubGroup Ideogram")

    def set_hybrid_ideogram_template(self):
        self._set_action_template("Hybrid Ideogram")

    def set_history_ideogram_template(self):
        self._set_action_template("Ideogram", "History")

    def set_last_n_analyses_template(self):
        self.engine.selected_pipeline_template = "Series"
        # get n analyses from user
        n = 10

        # get the unknowns node
        node = self.engine.get_unknowns_node()
        if node:
            # get last n analyses as unks
            node.set_last_n_analyses(n)

            self.run()

    def set_last_n_hours_template(self):
        self.engine.selected_pipeline_template = "Series"
        # get last n hours from user
        n = 10
        self._set_last_nhours(n)

    def set_last_day_template(self):
        self.engine.selected_pipeline_template = "Series"
        self._set_last_nhours(24)

    def set_last_week_template(self):
        self.engine.selected_pipeline_template = "Series"
        self._set_last_nhours(24 * 7)

    def set_last_month_template(self):
        self.engine.selected_pipeline_template = "Series"
        self._set_last_nhours(24 * 7 * 30.5)

    def set_analysis_table_template(self):
        self.engine.selected_pipeline_template = "Analysis"
        self.run()

    # private
    def _get_active_analyses(self):
        if self.active_editor:
            return self.active_editor.analyses

    def _set_last_nhours(self, n):
        node = self.engine.get_unknowns_node()
        if node:
            node.set_last_n_hours_analyses(n)
            self.run()

    def _set_action_template(self, name, group=None):
        self.activated()
        self.engine.selected_pipeline_template = (name, group)
        self.run()

    def _make_save_figure_object(self, editor):
        po = editor.plotter_options
        plotter_options = po.to_dict()
        obj = {
            "plotter_options": plotter_options,
            "analyses": [
                {
                    "record_id": ai.record_id,
                    "uuid": ai.uuid,
                    # 'status': ai.temp_status,
                    "group_id": ai.group_id,
                }
                for ai in editor.analyses
            ],
        }
        return obj

    def _close_editor(self, editor):
        for e in self.editor_area.editors:
            if e.name == editor.name:
                self.close_editor(e)
                break

    def _run(self, message, func, close_all=False):
        if self.engine.pre_run_check(func):
            self.debug("{} started".format(message))
            if close_all:
                self.close_all()

            self.dvc.db.session = None
            self.dvc.create_session()

            if not getattr(self.engine, func)():
                self.engine.resume_enabled = True
                self.engine.run_enabled = False
                self.debug("false {} {}".format(message, func))
            else:
                self.engine.run_enabled = True
                self.engine.resume_enabled = False
                self.debug("true {} {}".format(message, func))

            for editor in self.engine.state.editors:
                self._open_editor(editor)

            self.debug("{} finished".format(message))

    def _run_from_pipeline(self):
        self._run("run from", "run_from_pipeline")

    def _resume_pipeline(self):
        self._run("resume pipeline", "resume_pipeline")

    def _run_pipeline(self):
        self._run("run pipeline", "run_pipeline")

    def _toggle_run(self, v):
        self.engine.resume_enabled = v
        self.engine.run_enabled = not v

    def _sa_factory(self, path, factory, **kw):
        return SchemaAddition(path=path, factory=factory, **kw)

    def _set_invalid(self, items):
        self.set_tag(tag="invalid", items=items, warn=True)

    def _set_omit(self, items):
        self.set_tag(tag="omit", items=items, warn=True)

    # defaults
    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                Splitter(
                    PaneItem("pychron.pipeline.pane", width=200),
                    PaneItem("pychron.pipeline.analyses", width=200),
                ),
                PaneItem("pychron.pipeline.repository"),
                orientation="vertical",
            )
        )

    def _extra_actions_default(self):
        sas = (
            ("MenuBar/data.menu", RunAction, {}),
            ("MenuBar/data.menu", ResumeAction, {}),
            ("MenuBar/data.menu", RunFromAction, {}),
            ("MenuBar/data.menu", ResetAction, {}),
            ("MenuBar/data.menu", ClearAction, {}),
        )
        return [self._sa_factory(path, factory, **kw) for path, factory, kw in sas]

    def _help_tips_default(self):
        return [
            "Use <b>Data>Ideogram</b> to plot an Ideogram",
            "Use <b>Data>Spectrum</b> to plot a Spectrum",
            "Use <b>Data>Series</b> to plot a Time series of Analyses",
            "Use <b>Data>XY Scatter</b> to plot a XY Scatter plot of "
            "any Analysis value versus any other Analysis value",
            "Use <b>Data>Recall</b> to view analytical data for individual analyses",
        ]

    # handlers
    @on_trait_change("editor_area:editors[]")
    def _handle_editors(self):
        self.engine.editors = self.editor_area.editors

    @on_trait_change("engine:reset_event")
    def _handle_reset(self):
        self.reset()

    def _active_editor_changed(self, new):
        self.is_figure_editor = False
        if new:
            self.engine.select_node_by_editor(new)
            if isinstance(new, FigureEditor):
                self.is_figure_editor = True
                if hasattr(new.plotter_options, "get_group_colors"):
                    self.analyses_pane.unknowns_adapter.set_colors(
                        new.plotter_options.get_group_colors()
                    )
                    self.engine.refresh_table_needed = True

        self.set_interpreted_enabled = isinstance(new, InterpretedAgeEditor)
        if hasattr(new, "editor_options"):
            self.active_editor_options = new.editor_options
        else:
            self.active_editor_options = None

    @on_trait_change("engine:selected")
    def _handle_engine_selected(self, obj, name, old, new):
        if isinstance(new, Pipeline):
            self.engine.pipeline = new
        elif isinstance(new, NodeGroup):
            pass
        else:
            # self.engine.selected_node = new
            if old:
                old.on_trait_change(
                    self._handle_tag,
                    "unknowns:tag_event,references:tag_event",
                    remove=True,
                )
                old.on_trait_change(
                    self._handle_invalid,
                    "unknowns:invalid_event,references:invalid_event",
                    remove=True,
                )
                old.on_trait_change(
                    self._handle_omit,
                    "unknowns:omit_event,references:omit_event",
                    remove=True,
                )
                old.on_trait_change(
                    self._handle_recall,
                    "unknowns:recall_event,references:recall_event",
                    remove=True,
                )
                old.on_trait_change(
                    self.engine.handle_len_unknowns, "unknowns_items", remove=True
                )
                old.on_trait_change(
                    self.engine.handle_len_references, "references_items", remove=True
                )
                old.on_trait_change(
                    self.engine.handle_status,
                    "unknowns:temp_status,references:temp_status",
                    remove=True,
                )

            if new:
                new.on_trait_change(
                    self._handle_tag, "unknowns:tag_event,references:tag_event"
                )
                new.on_trait_change(
                    self._handle_invalid,
                    "unknowns:invalid_event,references:invalid_event",
                )
                new.on_trait_change(
                    self._handle_omit, "unknowns:omit_event,references:omit_event"
                )
                new.on_trait_change(
                    self._handle_recall, "unknowns:recall_event,references:recall_event"
                )
                new.on_trait_change(
                    self.engine.handle_status,
                    "unknowns:temp_status,references:temp_status",
                )
                new.on_trait_change(self.engine.handle_len_unknowns, "unknowns_items")
                new.on_trait_change(
                    self.engine.handle_len_references, "references_items"
                )

            if isinstance(new, FigureNode):
                if new.editor:
                    editor = new.editor
                    self.engine.selected_editor = editor
                    self.engine.active_editor = editor

    @on_trait_change("engine:tag_event")
    def _handle_engine_tag(self, new):
        self.set_tag(items=new)

    def _handle_tag(self, name, new):
        self.set_tag(items=new)

    def _handle_invalid(self, name, new):
        self._set_invalid(new)

    def _handle_omit(self, name, new):
        self._set_omit(new)

    @on_trait_change("engine:run_needed")
    def _handle_run_needed(self, new):
        self.debug("run needed for {}".format(new))
        if self.engine.resume_enabled:
            self.resume()
        else:
            self.run()

    @on_trait_change("engine:recall_analyses_needed")
    def _handle_recall(self, new):
        if not isinstance(new, DVCInterpretedAge):
            self.recall(new, use_quick=False)

    @on_trait_change("engine:play_analysis_video_needed")
    def _handle_video(self, new):
        if not isinstance(new, DVCInterpretedAge):
            self.play_analysis_video(new)

    def _prompt_for_save(self):
        if globalv.ignore_shareable:
            return True

        ret = True
        ps = self.engine.get_experiment_ids()

        if ps:
            changed = repository_has_staged(ps)
            self.debug("task has changes to {}".format(changed))
            if changed:
                m = "You have changes to analyses. Would you like to share them?"
                ret = self._handle_prompt_for_save(m, "Share Changes")
                if ret == "save":
                    self.dvc.push_repositories(changed)

        return ret

    def _opened_hook(self):
        super(PipelineTask, self)._opened_hook()
        if globalv.pipeline_debug:
            self._debug()

    def _get_selection(self):
        selected = self.engine.selected
        if selected and not isinstance(selected, Pipeline):
            items = selected.unknowns
            items.extend(selected.references)
            items = [i for i in items if i.temp_selected]

            uuids = [i.uuid for i in items]
            for ans in (self.engine.selected_unknowns, self.engine.selected_references):
                for i in ans:
                    if i.uuid not in uuids:
                        items.append(i)

            return items

    def _get_tagname(self, items):
        from pychron.pipeline.tagging.analysis_tags import AnalysisTagModel
        from pychron.pipeline.tagging.views import AnalysisTagView

        model = AnalysisTagModel()
        tv = AnalysisTagView(model=model)

        tv.model.items = items

        info = tv.edit_traits()
        if info.result:
            return model.tag, model.get_items(), model.use_filter, model.note

    def _engine_default(self):
        e = PipelineEngine(application=self.application)
        return e


# ============= EOF =============================================
