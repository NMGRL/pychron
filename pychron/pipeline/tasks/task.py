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
from pyface.tasks.action.schema import SToolBar, SMenu
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter
from traits.api import Instance, Bool, on_trait_change
# ============= standard library imports ========================
from itertools import groupby
import os
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import list_gits
from pychron.core.pdf.save_pdf_dialog import save_pdf
from pychron.dvc import dvc_dump
from pychron.dvc.dvc import repository_has_staged, push_repositories
from pychron.envisage.tasks.actions import ToggleFullWindowAction
from pychron.globals import globalv
from pychron.paths import paths
from pychron.pipeline.engine import PipelineEngine
from pychron.pipeline.plot.editors.interpreted_age_editor import InterpretedAgeEditor
from pychron.pipeline.save_figure import SaveFigureView, SaveFigureModel
from pychron.pipeline.state import EngineState
from pychron.pipeline.tasks.actions import RunAction, SavePipelineTemplateAction, ResumeAction, ResetAction, \
    ConfigureRecallAction, TagAction, SetInterpretedAgeAction, ClearAction, SavePDFAction, SaveFigureAction, \
    SetInvalidAction, SetFilteringTagAction, TabularViewAction, EditAnalysisAction, RunFromAction
from pychron.pipeline.tasks.panes import PipelinePane, AnalysesPane
from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.tasks.select_repo import SelectExperimentIDView
from pychron.pipeline.tasks.interpreted_age_factory import InterpretedAgeFactoryView, \
    InterpretedAgeFactoryModel


class DataMenu(SMenu):
    id = 'data.menu'
    name = 'Data'


def select_experiment_repo():
    a = list_gits(paths.repository_dataset_dir)
    v = SelectExperimentIDView(available=a)
    info = v.edit_traits()
    if info.result:
        return v.selected


class PipelineTask(BaseBrowserTask):
    name = 'Pipeline Processing'
    engine = Instance(PipelineEngine)
    tool_bars = [SToolBar(ConfigureRecallAction(),
                          ToggleFullWindowAction()),
                 SToolBar(RunAction(),
                          ResumeAction(),
                          RunFromAction(),
                          ResetAction(),
                          ClearAction(),
                          SavePipelineTemplateAction(),
                          name='Pipeline'),
                 SToolBar(SavePDFAction(),
                          SaveFigureAction(),
                          name='Save'),
                 SToolBar(EditAnalysisAction(),
                          name='Edit'),
                 # SToolBar(GitRollbackAction(), label='Git Toolbar'),
                 SToolBar(TagAction(),
                          SetInvalidAction(),
                          SetFilteringTagAction(),
                          SetInterpretedAgeAction(),
                          TabularViewAction(),
                          name='Misc')]

    state = Instance(EngineState)
    resume_enabled = Bool(False)
    run_enabled = Bool(True)
    set_interpreted_enabled = Bool(False)
    # run_to = None

    modified = False
    projects = None

    def activated(self):
        super(PipelineTask, self).activated()

        self.engine.dvc = self.dvc
        self.engine.browser_model = self.browser_model
        self.engine.interpreted_age_browser_model = self.interpreted_age_browser_model

        # self.engine.add_data()

    def _debug(self):
        self.engine.add_data()
        if globalv.select_default_data:
            self.engine.select_default()

        if globalv.pipeline_template:
            self.engine.set_template(globalv.pipeline_template)
            if globalv.run_pipeline:
                self.run()

    def prepare_destroy(self):
        super(PipelineTask, self).prepare_destroy()
        self.interpreted_age_browser_model.dump_browser()

    def create_dock_panes(self):
        panes = [PipelinePane(model=self.engine),
                 AnalysesPane(model=self.engine)]
        return panes

    # toolbar actions
    def tabular_view(self):
        self.debug('open tabular view')
        if not self.has_active_editor():
            return

        ed = self.active_editor
        from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor
        if isinstance(ed, IdeogramEditor):
            from pychron.pipeline.editors.fusion.fusion_table_editor import FusionTableEditor
            ted = FusionTableEditor()
            ted.items = ed.analyses
            self._open_editor(ted)

    def set_filtering_tag(self):
        ans = self.engine.selected.unknowns
        refs = self.engine.selected.references
        ans.extend(refs)

        omit_ans = [ai for ai in ans if ai.temp_status == 'omit' and ai.tag != 'omit']
        outlier_ans = [ai for ai in ans if ai.temp_status == 'outlier' and ai.tag != 'outlier']
        invalid_ans = [ai for ai in ans if ai.temp_status == 'invalid' and ai.tag != 'invalid']
        self.set_tag('omit', omit_ans, use_filter=False)
        self.set_tag('outlier', outlier_ans, use_filter=False)
        self.set_tag('invalid', invalid_ans)

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
                    self.warning_dialog('No analyses selected to Tag')
                return

        if items:
            if tag is None:
                a = self._get_tagname(items)
                if a:
                    tag, items, use_filter = a

            # tags stored as lowercase
            tag = tag.lower()

            # set tags for items
            if tag and items:
                dvc = self.dvc
                db = dvc.db
                key = lambda x: x.repository_identifier

                for expid, ans in groupby(sorted(items, key=key), key=key):
                    cs = []
                    with db.session_ctx():
                        for it in ans:
                            self.debug('setting {} tag= {}'.format(it.record_id, tag))
                            db.set_analysis_tag(it.uuid, tag)

                            it.set_tag(tag)
                            if dvc.update_tag(it):
                                cs.append(it)
                                # it.refresh_view()

                    if cs:
                        cc = [c.record_id for c in cs]
                        if len(cc) > 1:
                            cstr = '{} - {}'.format(cc[0], cc[-1])
                        else:
                            cstr = cc[0]
                        dvc.repository_commit(expid, '<TAG> {:<6s} {}'.format(tag, cstr))
                        for ci in cs:
                            ci.refresh_view()

                if use_filter:
                    for e in self.editor_area.editors:
                        if isinstance(e, FigureEditor):
                            e.set_items([ai for ai in e.analyses if ai.tag != 'invalid'])
                #
                if self.active_editor:
                    self.active_editor.refresh_needed = True

                self.browser_model.analysis_table.set_tags(tag, items)
                self.browser_model.analysis_table.remove_invalid()
                self.browser_model.analysis_table.refresh_needed = True
                self.engine.refresh_table_needed = True
                # else:
                #     # edit tags
                #     self._get_tagname([])

    def set_invalid(self):
        items = self._get_selection()
        self._set_invalid(items)

    def save_figure(self):
        self.debug('save figure')
        if not self.has_active_editor():
            return

        ed = self.active_editor
        root = paths.figure_dir
        path = os.path.join(root, 'test.json')
        obj = self._make_save_figure_object(ed)
        dvc_dump(obj, path)

    def save_figure_pdf(self):
        self.debug('save figure pdf')
        if not self.has_active_editor():
            return

        ed = self.active_editor
        sfm = SaveFigureModel(ed.analyses)
        sfv = SaveFigureView(model=sfm)
        info = sfv.edit_traits()
        if info.result:
            path = sfm.prepare_path(make=True)
            save_pdf(ed.component,
                     path=path,
                     options=sfm.pdf_options,
                     # path='/Users/ross/Documents/test.pdf',
                     view=True)

    def run(self):
        self._run_pipeline()

    def resume(self):
        self._resume_pipeline()

    def run_from(self):
        self._run_from_pipeline()

    def set_interpreted_age(self):
        ias = self.active_editor.get_interpreted_ages()

        repository_identifiers = self.dvc.get_local_repositories()
        model = InterpretedAgeFactoryModel(groups=ias)

        iaf = InterpretedAgeFactoryView(model=model,
                                        repository_identifiers=repository_identifiers)
        info = iaf.edit_traits()
        if info.result:
            self._add_interpreted_ages(ias)

    def git_rollback(self):
        # select experiment
        expid = select_experiment_repo()
        if expid:
            self.dvc.rollback_repository(expid)

    def clear(self):
        self.reset()
        self.engine.clear()
        self.close_all()

    def reset(self):
        self.run_enabled = True
        self.resume_enabled = False
        # self._temp_state = None
        # self.state = None
        self.engine.reset()

    def save_pipeline_template(self):
        path = self.save_file_dialog(default_directory=paths.user_pipeline_template_dir)
        # path = '/Users/ross/Sandbox/template.yaml'
        # path = os.path.join(paths.pipeline_template_dir, 'test.yaml')
        if path:
            self.engine.save_pipeline_template(path)

    # action handlers
    def set_flux_template(self):
        self.engine.selected_plipeline_template = 'Flux'
        self.run()

    def set_ideogram_template(self):
        self.engine.selected_pipeline_template = 'Ideogram'
        self.run()

    def set_spectrum_template(self):
        self.engine.selected_pipeline_template = 'Spectrum'
        self.run()

    def set_isochron_template(self):
        self.engine.selected_pipeline_template = 'Isochron'
        self.run()

    def set_series_template(self):
        self.engine.selected_pipeline_template = 'Series'
        self.run()

    def set_vertical_flux_template(self):
        self.engine.selected_pipeline_template = 'VerticalFlux'
        self.run()

    def set_last_n_analyses_template(self):
        self.engine.selected_pipeline_template = 'Series'
        # get n analyses from user
        n = 10

        # get the unknowns node
        node = self.engine.get_unknowns_node()
        if node:
            # get last n analyses as unks
            # set node.unknowns = unks
            node.set_last_n_analyses(n)

            self.run()

    def _set_last_nhours(self, n):
        node = self.engine.get_unknowns_node()
        if node:
            node.set_last_n_hours_analyses(n)
            self.run()

    def set_last_n_hours_template(self):
        self.engine.selected_pipeline_template = 'Series'
        # get last n hours from user
        n = 10
        self._set_last_nhours(n)

    def set_last_day_template(self):
        self.engine.selected_pipeline_template = 'Series'
        self._set_last_nhours(24)

    def set_last_week_template(self):
        self.engine.selected_pipeline_template = 'Series'
        self._set_last_nhours(24 * 7)

    def set_last_month_template(self):
        self.engine.selected_pipeline_template = 'Series'
        self._set_last_nhours(24 * 7 * 30.5)

    # private
    def _make_save_figure_object(self, editor):
        po = editor.plotter_options
        plotter_options = po.to_dict()

        for k, v in plotter_options.iteritems():
            print k, v
        obj = {}
        obj['plotter_options'] = plotter_options
        obj['analyses'] = [{'record_id': ai.record_id,
                            'uuid': ai.uuid,
                            # 'status': ai.temp_status,
                            'group_id': ai.group_id} for ai in editor.analyses]
        return obj

    def _add_interpreted_ages(self, ias):
        dvc = self.dvc
        db = dvc.db
        with db.session_ctx():
            for ia in ias:
                if ia.use:
                    dvc.add_interpreted_age(ia)

    def _close_editor(self, editor):
        for e in self.editor_area.editors:
            if e.name == editor.name:
                self.close_editor(e)
                break

    def _run(self, message, func, close_all=False):
        self.debug('{} started'.format(message))
        if close_all:
            self.close_all()

        if not getattr(self.engine, func)():
            self.resume_enabled = True
            self.run_enabled = False
            self.debug('false {} {}'.format(message, func))
        else:
            self.run_enabled = True
            self.resume_enabled = False
            self.debug('true {} {}'.format(message, func))

        for editor in self.engine.state.editors:
            self._open_editor(editor)

        self.debug('{} finished'.format(message))

    def _run_from_pipeline(self):
        self._run('run from', 'run_from_pipeline')

    def _resume_pipeline(self):
        self._run('resume pipeline', 'resume_pipeline')

    def _run_pipeline(self):
        self._run('run pipeline', 'run_pipeline', close_all=True)

    def _toggle_run(self, v):
        self.resume_enabled = v
        self.run_enabled = not v

    def _sa_factory(self, path, factory, **kw):
        return SchemaAddition(path=path, factory=factory, **kw)

    def _set_invalid(self, items):
        self.set_tag(tag='invalid', items=items, warn=True)

    # defaults
    def _default_layout_default(self):
        return TaskLayout(left=Splitter(PaneItem('pychron.pipeline.pane',
                                                 width=200),
                                        PaneItem('pychron.pipeline.analyses',
                                                 width=200)))

    def _extra_actions_default(self):
        sas = (('MenuBar/data.menu', RunAction, {}),)
        return [self._sa_factory(path, factory, **kw) for path, factory, kw in sas]

    def _help_tips_default(self):
        return ['Use <b>Data>Ideogram</b> to plot an Ideogram',
                'Use <b>Data>Spectrum</b> to plot a Spectrum',
                'Use <b>Data>Series</b> to plot a Time series of Analyses',

                # 'Use <b>Data>XY Scatter</b> to plot a XY Scatter plot of '
                # 'any Analysis value versus any other Analysis value',
                # 'Use <b>Data>Recall</b> to view analytical data for individual analyses',
                ]

    # handlers
    @on_trait_change('engine:reset_event')
    def _handle_reset(self):
        self.reset()

    def _active_editor_changed(self, new):
        if new:
            self.engine.select_node_by_editor(new)

        self.set_interpreted_enabled = isinstance(new, InterpretedAgeEditor)

    # @on_trait_change('active_editor:save_needed')
    # def _handle_save_needed(self):
    #     self.engine.run_persist(self._temp_state)

    @on_trait_change('engine:[tag_event, invalid_event, recall_event]')
    def _handle_analysis_tagging(self, name, new):
        if name == 'tag_event':
            self.set_tag(items=new)
        elif name == 'invalid_event':
            self._set_invalid(new)
        elif name == 'recall_event':
            self.recall(new)

    @on_trait_change('engine:run_needed')
    def _handle_run_needed(self, new):
        self.debug('run needed for {}'.format(new))
        self.run()

    @on_trait_change('engine:recall_analyses_needed')
    def _handle_recall(self, new):
        self.recall(new)

    def _prompt_for_save(self):
        if globalv.ignore_shareable:
            return True

        ret = True
        ps = self.engine.get_experiment_ids()

        if ps:
            changed = repository_has_staged(ps)
            self.debug('task has changes to {}'.format(changed))
            if changed:
                m = 'You have changes to analyses. Would you like to share them?'
                ret = self._handle_prompt_for_save(m, 'Share Changes')
                if ret == 'save':
                    push_repositories(changed)

        return ret

    def _opened_hook(self):
        super(PipelineTask, self)._opened_hook()
        if globalv.pipeline_debug:
            self._debug()

    def _get_selection(self):
        items = self.engine.selected.unknowns
        items.extend(self.engine.selected.references)
        items = [i for i in items if i.temp_selected]
        items.extend(self.engine.selected_unknowns)
        items.extend(self.engine.selected_references)
        return items

    def _get_tagname(self, items):
        from pychron.pipeline.tagging.analysis_tags import AnalysisTagModel
        from pychron.pipeline.tagging.views import AnalysisTagView

        tv = AnalysisTagView(model=AnalysisTagModel())

        db = self.dvc.db
        with db.session_ctx():
            # tv.model.db = db
            tv.model.items = items
            # tv.model.load()

        info = tv.edit_traits()
        if info.result:
            tag = tv.model.tag
            return tag, tv.model.items, tv.model.use_filter

    # def _get_dr_tagname(self, items):
    #     from pychron.pipeline.tagging.data_reduction_tags import DataReductionTagModel
    #     from pychron.pipeline.tagging.views import DataReductionTagView
    #
    #     tv = DataReductionTagView(model=DataReductionTagModel(items=items))
    #     info = tv.edit_traits()
    #     if info.result:
    #         return tv.model

    def _engine_default(self):
        e = PipelineEngine(application=self.application)
        return e

# ============= EOF =============================================
