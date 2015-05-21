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
from datetime import timedelta

from pyface.timer.do_later import do_later
from traits.api import Instance, on_trait_change
from enable.component import Component
from pyface.tasks.action.schema import SToolBar
from pyface.qt.QtGui import QTabBar


# ============= standard library imports ========================
import binascii
# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.iterfuncs import partition
from pychron.core.progress import progress_iterator
from pychron.easy_parser import EasyParser
from pychron.core.ui.table_configurer import RecallTableConfigurer
from pychron.envisage.tasks.actions import ToggleFullWindowAction
from pychron.processing.analyses.view.adapters import IsotopeTabularAdapter, IntermediateTabularAdapter
from pychron.processing.k3739_edit import K3739EditModel, K3739EditView
from pychron.processing.tasks.actions.edit_actions import DatabaseSaveAction
from pychron.processing.tasks.analysis_edit.named_analysis_grouping import AnalysisGroupEntry, AnalysisGroupDelete
from pychron.processing.tasks.analysis_edit.panes import UnknownsPane, ControlsPane, \
    TablePane

from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.processing.plot.editors.figure_editor import FigureEditor
from pychron.processing.tasks.recall.recall_editor import RecallEditor
from pychron.processing.tasks.analysis_edit.adapters import UnknownsAdapter

# from pyface.tasks.task_window_layout import TaskWindowLayout
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane
from pychron.processing.analyses.analysis import Analysis


class AnalysisEditTask(BaseBrowserTask):
    id = 'pychron.processing'
    unknowns_pane = Instance(TablePane)
    controls_pane = Instance(ControlsPane)
    plot_editor_pane = Instance(PlotEditorPane)
    unknowns_adapter = UnknownsAdapter
    unknowns_pane_klass = UnknownsPane

    ic_factor_editor_count = 0

    tool_bars = [SToolBar(DatabaseSaveAction(),
                          ToggleFullWindowAction(),
                          # FindAssociatedAction(),
                          image_size=(16, 16))]

    external_recall_window = False
    _tag_table_view = None

    analysis_group_edit_klass = AnalysisGroupEntry
    auto_show_unknowns_pane = True

    isotope_adapter = Instance(IsotopeTabularAdapter, ())
    intermediate_adapter = Instance(IntermediateTabularAdapter, ())
    recall_configurer = Instance(RecallTableConfigurer)

    _no_update = False

    def activate_isoevo_task(self):
        tid = 'pychron.processing.isotope_evolution'
        self._activate_task(tid)

    def activate_blanks_task(self):
        tid = 'pychron.processing.blanks'
        self._activate_task(tid)

    def activate_icfactor_task(self):
        tid = 'pychron.processing.ic_factor'
        self._activate_task(tid)

    def activate_recall_task(self):
        tid = 'pychron.recall'
        self._activate_task(tid)

    def activate_ideogram_task(self):
        task = self._activate_figure_task()
        if task:
            task.activate_ideogram_editor()

    def activate_spectrum_task(self):
        task = self._activate_figure_task()
        if task:
            task.activate_spectrum_editor()

    def split_editor_area_hor(self):
        """
            horizontal splitting not currently working
        """
        self.debug('splitting editor area')
        self.split_editors(0, 1)

    def split_editor_area_vert(self):

        self.debug('splitting editor area')
        self.split_editors(0, 1, 'vertical')

    def add_iso_evo(self, name=None, rec=None):
        if rec is None:
            if self.active_editor is not None:
                rec = self.active_editor.model
                name = self.active_editor.name

        if rec is None:
            return

        self.manager.load_raw_data(rec)

        name = 'IsoEvo {}'.format(name)
        editor = self.get_editor(name)
        if editor:
            self.activate_editor(editor)
        else:
            from pychron.processing.plot.editors.isotope_evolution_editor import IsotopeEvolutionEditor

            ieditor = IsotopeEvolutionEditor(name=name, processor=self.manager)
            ieditor.set_items([rec])
            self.editor_area.add_editor(ieditor)

    def delete_analysis_group(self):
        v = AnalysisGroupDelete(task=self)
        v.projects = self.browser_model.projects
        v.selected_projects = self.browser_model.selected_projects
        # v.groups=self.analysis_groups
        v.edit_traits(kind='livemodal')
        self.browser_model.analysis_groups = v.groups

    def make_analysis_group(self):
        ans = self._get_analyses_to_group()

        if not ans:
            self.information_dialog('No analyses selected to group')
            return

        a = self.analysis_group_edit_klass()
        # print ans
        a.set_items(ans)

        info = a.edit_traits()
        if info.result:
            name = a.name

            db = self.manager.db

            uuids = [ai.uuid for ais, k in ans
                     for ai in ais]

            with db.session_ctx():
                aa = db.get_analyses(pred=lambda m, l: (m.uuid.in_(uuids), ))
                set_id = binascii.crc32(''.join([ai.uuid for ai in aa]))

                dbg = db.get_analysis_group(set_id, key='id')
                if dbg is not None:
                    msg = 'Analysis Group of these analyses already exists. Name={}'.format(dbg.name)
                    self.information_dialog(msg)
                    return

                group = db.add_analysis_group(name, id=set_id)
                self._make_analysis_group(db, group, a.analyses)
                self.db_save_info()

                self.browser_model.load_associated_groups(self.browser_model.selected_projects)

    def append_unknown_analyses(self, ans):
        pane = self.unknowns_pane
        if pane:
            pane.items.extend(ans)

    def replace_unknown_analyses(self, ans):
        pane = self.unknowns_pane
        if pane:
            pane.items = ans

    def get_recall_editors(self):
        es = self.editor_area.editors
        return [e for e in es if isinstance(e, RecallEditor)]

    def configure_recall(self):
        tc = self.recall_configurer
        info = tc.edit_traits()
        if info.result:
            for e in self.get_recall_editors()[:]:
                if tc.show_intermediate != e.analysis_view.main_view.show_intermediate:
                    e.close()
                    self.recall(e.model)

            for e in self.get_recall_editors():
                tc.set_fonts(e.analysis_view)

    # def recall(self, records, open_copy=False):
    #     """
    #         if analysis is already open activate the editor
    #         otherwise open a new editor
    #
    #         if open_copy is True, allow multiple instances of the same analysis
    #     """
    #     self.debug('recalling records {}'.format(records))
    #
    #     if not isinstance(records, (list, tuple)):
    #         records = [records]
    #     elif isinstance(records, tuple):
    #         records = list(records)
    #
    #     if not open_copy:
    #         records = self._open_existing_recall_editors(records)
    #         if records:
    #             ans = None
    #             if self.browser_model.use_workspace:
    #                 ans = self.workspace.make_analyses(records)
    #             elif self.dvc:
    #                 ans = self.dvc.make_analyses(records)
    #             # else:
    #             # ans = self.manager.make_analyses(records, calculate_age=True, load_aux=True)
    #             if ans:
    #                 self._open_recall_editors(ans)
    #             else:
    #                 self.warning('failed making records')
    #     else:
    #         ans = self.manager.make_analyses(records, use_cache=False, calculate_age=True, load_aux=True)
    #         self._open_recall_editors(ans)

    # def new_ic_factor(self):
    #     from pychron.processing.tasks.detector_calibration.intercalibration_factor_editor import \
    #         IntercalibrationFactorEditor
    #
    #     editor = IntercalibrationFactorEditor(name='ICFactor {:03d}'.format(self.ic_factor_editor_count),
    #                                           processor=self.manager)
    #     self._open_editor(editor)
    #     self.ic_factor_editor_count += 1

    def save_as(self):
        self.save()

    def save(self, path=None):
        self.warning_dialog('Please use "Data -> Database Save" to save changes to the database')

    def save_to_db(self):
        db = self.manager.db
        with db.session_ctx():
            self._save_to_db()
        self.db_save_info()

    def save_pdf_figure(self):
        if self.active_editor:

            from chaco.pdf_graphics_context import PdfPlotGraphicsContext

            p = self.save_file_dialog(ext='.pdf')
            if p:
                gc = PdfPlotGraphicsContext(filename=p,
                                            dest_box=(1.5, 1, 6, 9))

                # pc.do_layout(force=True)
                # pc.use_backbuffer=False
                comp = self.active_editor.component
                if not issubclass(type(comp), Component):
                    comp = comp.plotcontainer
                gc.render_component(comp, valign='center')
                gc.save()

    def select_data_reduction_tag(self):
        from pychron.processing.tagging.data_reduction_tags import SelectDataReductionTagModel
        from pychron.processing.tagging.views import SelectDataReductionTagView

        model = SelectDataReductionTagModel()
        db = self.manager.db
        with db.session_ctx():
            items = self._get_selection()
            uuids = [it.uuid for it in items] if items else None
            tags = db.get_data_reduction_tags(uuids=uuids)
            model.load_tags(tags)

        v = SelectDataReductionTagView(model=model)
        info = v.edit_traits()
        if info.result:
            stag = model.selected
            self.debug('setting data reduction tag {}'.format(stag.name))
            with db.session_ctx():
                dbtag = db.get_data_reduction_tag(stag.id)

                def func(ai, prog, i, n):
                    if prog:
                        prog.change_message('setting data reduction tag for {}'.format(ai.record_id))

                    dban = ai.analysis
                    dban.data_reduction_tag = dbtag

                progress_iterator(dbtag.analyses, func)

                # for ai in dbtag.analyses:
                # dban = ai.analysis
                # dban.data_reduction_tag = dbtag

    def set_data_reduction_tag(self):
        items = self._get_analyses_to_tag()
        if items:
            model = self._get_dr_tagname(items)
            if model is not None:
                db = self.manager.db
                with db.session_ctx():
                    dbtag = db.add_data_reduction_tag(model.tagname, model.comment)
                    self.debug('added data reduction tag: {}'.format(model.tagname))

                    def func(ai, prog, i, n):
                        dban = db.get_analysis_uuid(ai.uuid)
                        db.add_data_reduction_tag_set(dbtag, dban, dban.selected_histories.id)
                        dban.data_reduction_tag = dbtag
                        if prog:
                            prog.change_message(
                                'Applying data reduction tag "{}" to {}'.format(model.tagname, ai.record_id))

                    progress_iterator(model.items, func)

    def set_tag(self, tag=None, items=None, use_filter=True):
        """
            set tag for either
            analyses selected in unknowns pane
            or
            analyses selected in figure e.g temp_status!=0

        """
        if items is None:
            items = self._get_analyses_to_tag()

        if items:
            db = self.manager.db
            name = None
            if tag is None:
                a = self._get_tagname(items)
                if a:
                    tag, items, use_filter = a
                    if tag:
                        name = tag.name
            else:
                name = tag.name

            if name and items:
                with db.session_ctx():
                    for it in items:
                        self.debug('setting {} tag= {}'.format(it.record_id, name))

                        ma = db.get_analysis_uuid(it.uuid)
                        ma.tag = name
                        it.set_tag(tag)

                if use_filter:
                    for e in self.editor_area.editors:
                        if isinstance(e, FigureEditor):
                            e.analyses = [ai for ai in e.analyses if ai.tag != 'invalid']

                if self.active_editor:
                    self.active_editor.rebuild()

                self.browser_model.analysis_table.refresh_needed = True
                if self.unknowns_pane:
                    self.unknowns_pane.refresh_needed = True
                self._set_tag_hook()

    def modify_k3739(self):
        if self.active_editor:
            ans = self.unknowns_pane.selected
            apply_new_value = True
        else:
            apply_new_value = False
            ans = self.browser_model.analysis_table.selected

        if not ans:
            self.information_dialog('Please select a set of analyses from the Unknowns.')
        else:
            m = K3739EditModel(analyses=ans)
            v = K3739EditView(model=m)
            info = v.edit_traits()
            if info.result and m.analyses:
                if m.save_to_db:
                    db = self.manager.db
                    prog = self.manager.open_progress(n=len(m.analyses))
                    with db.session_ctx():
                        for ai in m.analyses:
                            dban = db.get_analysis_uuid(ai.uuid)

                            msg = 'setting {} for {}'.format(m.value_str, ai.record_id)
                            self.debug(msg)
                            prog.change_message(msg)

                if apply_new_value:
                    m.apply_modified()

                if self.active_editor:
                    self.active_editor.clear_aux_plot_limits()
                    self.active_editor.rebuild()

    def prepare_destroy(self):
        if self.unknowns_pane:
            self.unknowns_pane.dump()

        super(AnalysisEditTask, self).prepare_destroy()

    def create_dock_panes(self):

        self.unknowns_pane = self._create_unknowns_pane()

        # self.controls_pane = ControlsPane()
        self.plot_editor_pane = PlotEditorPane()
        panes = [
            self.unknowns_pane,
            #                 self.controls_pane,
            self.plot_editor_pane,
            #                self.results_pane,
            self._create_browser_pane()]
        cp = self._create_control_pane()
        if cp:
            self.controls_pane = cp
            panes.append(cp)

        return panes

    # private
    def _activate_figure_task(self):
        tid = 'pychron.processing.figures'
        task = self._activate_task(tid)
        return task

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

    def _selector_dclick(self, new):
        self.debug('selector {}'.format(new))
        self.recall(new)

    def _open_existing_recall_editors(self, records):
        editor = None
        # check if record already is open
        for r in records:
            editor = self._get_editor_by_uuid(r.uuid)
            if editor:
                records.remove(r)

        # activate editor if open
        if editor:
            self.activate_editor(editor)
        return records

    def _open_recall_editors(self, ans):
        existing = [e.basename for e in self.get_recall_editors()]
        if ans:
            for rec in ans:
                av = rec.analysis_view
                mv = av.main_view
                mv.isotope_adapter = self.isotope_adapter
                mv.intermediate_adapter = self.intermediate_adapter
                mv.show_intermediate = self.recall_configurer.show_intermediate

                self.recall_configurer.set_fonts(av)

                editor = RecallEditor(manager=self.manager)
                editor.set_items(rec)
                if existing and editor.basename in existing:
                    editor.instance_id = existing.count(editor.basename)

                try:
                    self.editor_area.add_editor(editor)
                except AttributeError:
                    pass
        else:
            self.warning('could not load records')

    def _create_control_pane(self):
        return ControlsPane()

    def _create_unknowns_pane(self):
        up = self.unknowns_pane_klass(adapter_klass=self.unknowns_adapter)
        up.load()
        return up

    def _make_analysis_group(self, db, group, ans):
        # db=self.manager.db
        for ais, at in ans:
            at = db.get_analysis_type(at)
            self.debug('set analysis group for {} {}'.format(at, group))
            for ai in ais:
                ai = db.get_analysis_uuid(ai.uuid)
                db.add_analysis_group_set(group, ai, analysis_type=at)

    def _get_editor_by_uuid(self, uuid):
        return next((editor for editor in self.editor_area.editors
                     if isinstance(editor, RecallEditor) and
                     editor.model and editor.model.uuid == uuid), None)

    def _get_tagname(self, items):
        from pychron.processing.tagging.analysis_tags import AnalysisTagModel
        from pychron.processing.tagging.views import AnalysisTagView

        tv = self._tag_table_view
        if not tv:
            tv = AnalysisTagView(model=AnalysisTagModel())

        db = self.manager.db
        with db.session_ctx():
            # tv = TagTableView(items=items)
            tv.model.db = db
            tv.model.items = items
            tv.model.load()

        info = tv.edit_traits()
        if info.result:
            tag = tv.model.selected
            self._tag_table_view = tv
            return tag, tv.model.items, tv.model.use_filter

    def _get_dr_tagname(self, items):
        from pychron.processing.tagging.data_reduction_tags import DataReductionTagModel
        from pychron.processing.tagging.views import DataReductionTagView

        tv = DataReductionTagView(model=DataReductionTagModel(items=items))
        info = tv.edit_traits()
        if info.result:
            return tv.model

    def _save_to_db(self):
        if self.active_editor:
            if hasattr(self.active_editor, 'save'):
                self.active_editor.save()

    def _set_previous_selection(self, pane, new):
        if new and new.name != 'Previous Selection':
            man = self.manager
            db = man.db
            with db.session_ctx():
                lns = set([si.labnumber for si in new.analysis_ids])
                ids = [si.uuid for si in new.analysis_ids]
                if ids:
                    def f(t, t2):
                        return t2.identifier.in_(lns), t.uuid.in_(ids)

                    ans = db.get_analyses(uuid=f)
                    # func = self._record_view_factory
                    # ans = [func(si) for si in ans]
                    ans = self.browser_model.make_records(ans)
                    for ti in new.analysis_ids:
                        a = next((ai for ai in ans if ai.uuid == ti.uuid), None)
                        if a:
                            a.group_id = ti.group_id
                            a.graph_id = ti.graph_id
                            # (group_id=ti.group_id, graph_id=ti.graph_id)

                    pane.items = ans

    def _save_file(self, path):
        if self.active_editor:
            self.active_editor.save_file(path)
            return True

    def _recall_item(self, item, open_copy=False):
        if not self.external_recall_window:
            self.recall(item, open_copy=open_copy)
        else:
            self._open_external_recall_editor(item, open_copy=open_copy)

    def _open_external_recall_editor(self, sel, open_copy=False):
        tid = 'pychron.recall'
        app = self.window.application

        win, task, is_open = app.get_open_task(tid)

        if is_open:
            win.activate()
        else:
            win.open()

        task.activated()
        task.recall(sel)
        # task.load_projects()

        # print self.selected_project, 'ffff'
        # task.set_projects(self.oprojects, self.selected_projects)
        # task.set_samples(self.osamples, self.selected_samples)

    def _append_replace_unknowns(self, is_append, items=None):
        if self.active_editor:
            if not isinstance(self.active_editor, RecallEditor):
                self.active_editor.auto_find = True

                if not items:
                    unks = None
                    if is_append:
                        unks = self.active_editor.analyses
                    items = self._get_selected_analyses(unks=unks)

                if items:
                    self.active_editor.set_items(items, is_append)

                    self._add_unknowns_hook()

    def _do_easy(self, func):
        ep = EasyParser()
        db = self.manager.db

        prog = self.manager.open_progress(n=10, close_at_end=False)
        with db.session_ctx() as sess:
            ok = func(db, ep, prog)
            if not ok:
                sess.rollback()

        prog.close()
        if ok:
            self.db_save_info()

    def _get_analyses_to_group(self):
        items = None
        if self.unknowns_pane:
            items = self.unknowns_pane.selected

        if not items:
            if self.unknowns_pane:
                items = self.unknowns_pane.items
        if not items:
            items = self.browser_model.analysis_table.selected

        if items:
            return ((items, 'unknown'),)  # unknown analysis type

    def _get_selection(self):
        items = None

        if self.unknowns_pane:
            if not items:
                items = self.unknowns_pane.selected

            if not items:
                items = [i for i in self.unknowns_pane.items
                         if i.is_temp_omitted()]
                self.debug('Temp omitted analyses {}'.format(len(items)))

        if not items:
            items = self.browser_model.analysis_table.selected
        return items

    def _get_analyses_to_tag(self):
        items = self._get_selection()
        if not items:
            self.warning_dialog('No analyses selected to Tag')

        return items

    def _find_refs(self, ref):

        from pychron.processing.tasks.analysis_edit.selection_view import ReferenceSelectionView, AnalysisSelectionView

        rsd = ReferenceSelectionView()
        rsd.load()
        info = rsd.edit_traits(kind='livemodal')
        if info.result:
            rsd.dump()
            td = timedelta(hours=rsd.hours)
            db = self.manager.db
            with db.session_ctx():
                mi = ref.rundate - td
                ma = ref.rundate + td
                ans = db.get_analyses_date_range(mi, ma,
                                                 analysis_type=list(rsd.analysis_types),
                                                 mass_spectrometers=[ref.mass_spectrometer])

                ans = self.browser_model.make_records(ans)
                ans.append(ref)
                ans = sorted(ans, key=lambda x: x.rundate)

                asv = AnalysisSelectionView(analyses=ans,
                                            ref=ref)
                info = asv.edit_traits(kind='livemodal')
                if info.result:
                    if asv.selected:
                        self._recall_item(asv.selected)

    # hooks
    def _dclicked_analysis_group_hook(self, unks, b):
        pass

    def _add_unknowns_hook(self, *args, **kw):
        pass

    def _set_tag_hook(self):
        pass

    def _graphical_filter_hook(self, ans, is_append):
        if self.active_editor:
            self.active_editor.set_items(ans, is_append)

    def _setup_browser_model(self):
        super(AnalysisEditTask, self)._setup_browser_model()
        # self.browser_model.on_trait_change(self._current_task_name_changed, 'current_task_name')
        # self.browser_model.on_trait_change(self._dclicked_sample_changed, 'dclicked_sample')

    def _destroy_browser_model(self):
        super(AnalysisEditTask, self)._destroy_browser_model()
        # self.browser_model.on_trait_change(self._current_task_name_changed,
        #                                    'current_task_name', remove=True)
        # self.browser_model.on_trait_change(self._dclicked_sample_changed,
        #                                    'dclicked_sample', remove=True)

    def _set_current_task(self):
        with no_update(self):
            editor = self.active_editor
            if isinstance(editor, RecallEditor):
                self.browser_model.current_task_name = 'Recall'
    # ===============================================================================
    # handlers
    # ===============================================================================

    @on_trait_change('browser_model:current_task_name')
    def _current_task_name_changed(self, new):
        print 'task change {} {}, no_update {}'.format(id(self), new, self._no_update)
        if self._no_update:
            return

        func = getattr(self, 'activate_{}_task'.format(new.lower()))
        do_later(func)

    def _dclicked_analysis_group_changed(self):
        if self.active_editor:
            if self.browser_model.selected_analysis_groups:
                g = self.browser_model.selected_analysis_groups[0]
                db = self.manager.db

                with db.session_ctx():
                    dbg = db.get_analysis_group(g.id, key='id')
                    unks, b = partition(dbg.analyses, lambda x: x.analysis_type.name == 'unknown')

                    self.active_editor.auto_find = False
                    self.active_editor.set_items([ai.analysis for ai in unks])
                    self._dclicked_analysis_group_hook(unks, b)

    def _dclicked_sample_hook(self):
        if self.unknowns_pane:
            self.debug('Dumping UnknownsPane selection')
            self.unknowns_pane.dump_selection()
            self.unknowns_pane.load_previous_selections()

        super(AnalysisEditTask, self)._dclicked_sample_hook()

    def _active_editor_changed(self, new):
        if new:
            if self.controls_pane:
                tool = None
                if hasattr(new, 'tool'):
                    tool = new.tool
                elif isinstance(new, RecallEditor):
                    tool = new.analysis_view.selection_tool
                self.controls_pane.tool = tool

            if self.unknowns_pane:

                if hasattr(new, 'analyses'):
                    with no_update(self):
                        self.unknowns_pane.trait_set(items=new.analyses)
                    # self.unknowns_pane.items = self.active_editor.analyses

    @on_trait_change('active_editor:save_event')
    def _handle_save_event(self):
        self.save_to_db()

    @on_trait_change('active_editor:component_changed')
    def _update_component(self):
        if self.plot_editor_pane:
            self.plot_editor_pane.component = self.active_editor.component
            if hasattr(self.active_editor, 'plotter_options_manager'):
                opt = self.active_editor.plotter_options_manager.plotter_options
                if hasattr(opt, 'index_attr'):
                    index_attr = opt.index_attr
                    self.plot_editor_pane.index_attr = index_attr

    @on_trait_change('unknowns_pane:[items, update_needed, dclicked, refresh_editor_needed]')
    def _update_unknowns_runs(self, obj, name, old, new):
        self.debug('update_unknowns_runs: obj:{}, name:{}, new:{}'.format(obj, name, new))

        if name == 'dclicked':
            if new:
                if isinstance(new.item, (IsotopeRecordView, Analysis)):
                    self._recall_item(new.item)
        elif name == 'refresh_editor_needed':
            self.active_editor.rebuild()
        else:
            # required for drag and drop. prevents excessive updates.
            if not obj.no_update:
                if self.active_editor:
                    self.debug('Setting auto find to True')
                    if hasattr(self.active_editor, 'set_auto_find'):
                        self.active_editor.set_auto_find(True)
                    self.active_editor.set_items(obj.items)

                if self.plot_editor_pane:
                    self.plot_editor_pane.analyses = obj.items

    @on_trait_change('plot_editor_pane:current_editor')
    def _update_current_plot_editor(self, obj, name, new):
        if new:
            if not obj.suppress_pane_change:
                self._show_pane(self.plot_editor_pane)

    @on_trait_change('browser_model:[analysis_table:selected, time_view_model:selected]')
    def _handle_analysis_selected(self, new):
        # if self.browser_model.use_focus_switching:
        #     self.browser_model.filter_focus = not bool(new)

        if self.auto_show_unknowns_pane:
            if hasattr(self, 'unknowns_pane'):
                show = bool(new)
                if hasattr(self, 'references_pane'):
                    ref = self.references_pane
                    ch = ref.control.parent().children()
                    for ci in ch:
                        if isinstance(ci, QTabBar):
                            idx = ci.currentIndex()
                            text = ci.tabText(idx)
                            if text == 'References':
                                show = False
                                break
                if show:
                    self._show_pane(self.unknowns_pane)

    @on_trait_change('browser_model:[analysis_table:dclicked, time_view_model:dclicked]')
    def _dclicked_analysis_changed(self, obj, name, old, new):
        if new:
            self._recall_item(new.item)

    # @on_trait_change('analysis_table:[append_event,replace_event]')
    # @on_trait_change('sample_table:context_menu_event')
    # def _handle_analysis_table_context_menu(self, new):

    @on_trait_change('browser_model:[analysis_table:context_menu_event, time_view_model:context_menu_event]')
    def _handle_analysis_table_context_menu(self, new):
        if new:
            sel = self.browser_model.analysis_table.selected

            action, modifiers = new
            if action in ('append', 'replace'):
                self._append_replace_unknowns(action == 'append')
            elif action == 'open':
                if sel:
                    open_copy = False
                    if modifiers:
                        open_copy = modifiers.get('open_copy')

                    for it in sel:
                        self._recall_item(it, open_copy=open_copy)
            elif action == 'find_refs':
                if sel:
                    self._find_refs(sel[-1])

    @on_trait_change('unknowns_pane:previous_selection')
    def _update_up_previous_selection(self, obj, name, old, new):
        self._set_previous_selection(obj, new)

    @on_trait_change('unknowns_pane:[append_button, replace_button]')
    def _handle_unknowns_events(self, name, new):
        is_append = name == 'append_button'
        self._append_replace_unknowns(is_append)

    @on_trait_change('active_editor:analyses')
    def _ac_unknowns_changed(self):
        if self.unknowns_pane:
            # with no_update(self.unknowns_pane):
            #     self.unknowns_pane.items = self.active_editor.analyses
            self.unknowns_pane._no_update = True
            self.unknowns_pane.items = self.active_editor.analyses
            self.unknowns_pane._no_update = False

        # self.unknowns_pane._no_update = True
        # self.unknowns_pane.trait_set(items=self.active_editor.analyses, trait_change_notify=True)
        # self.unknowns_pane._no_update = False
        # self.unknowns_pane.trait_set(items=self.active_editor.analyses, trait_change_notify=False)

    @on_trait_change('active_editor:recall_event')
    def _handle_recall(self, new):
        self._recall_item(new)

    @on_trait_change('active_editor:tag_event')
    def _handle_tag(self, new):
        self.set_tag(items=new)

    @on_trait_change('active_editor:invalid_event')
    def _handle_invalid(self, new):
        from pychron.processing.tagging.analysis_tags import Tag

        self.set_tag(tag=Tag(name='invalid'),
                     items=new)

    def _recall_configurer_default(self):
        rc = RecallTableConfigurer()
        rc.intermediate_table_configurer.adapter = self.intermediate_adapter
        rc.isotope_table_configurer.adapter = self.isotope_adapter
        rc.load()
        return rc


# ============= EOF =============================================
