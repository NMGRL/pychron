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
import os
import pickle
from apptools.preferences.preference_binding import bind_preference
from traits.api import List, Str, Bool, Any, String, \
    on_trait_change, Date, Int, Time, Instance, Button
from pyface.tasks.action.schema import SToolBar
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.orms.isotope.gen import gen_MassSpectrometerTable, gen_LabTable, gen_ExtractionDeviceTable, \
    gen_AnalysisTypeTable
from pychron.database.orms.isotope.meas import meas_MeasurementTable, meas_AnalysisTable, meas_ExtractionTable
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.experiment.tasks.browser.browser_mixin import BrowserMixin
from pychron.paths import paths
from pychron.processing.tasks.browser.actions import NewBrowserEditorAction
from pychron.processing.tasks.browser.analysis_table import AnalysisTable
from pychron.processing.tasks.browser.panes import BrowserPane

'''
add toolbar action to open another editor tab


'''

"""
@todo: how to fit cocktail/air blanks. make special project called references.
added sample to air, cocktail. added samples to references project
"""

DEFAULT_SPEC = 'Spectrometer'
DEFAULT_AT = 'Analysis Type'
DEFAULT_ED = 'Extraction Device'


class BaseBrowserTask(BaseEditorTask, BrowserMixin):
    analysis_table = Instance(AnalysisTable, ())
    danalysis_table = Instance(AnalysisTable, ())

    analysis_filter = String(enter_set=True, auto_set=False)

    tool_bars = [SToolBar(NewBrowserEditorAction(),
                          image_size=(16, 16))]

    auto_select_analysis = Bool(True)

    mass_spectrometer = Str(DEFAULT_SPEC)
    mass_spectrometers = List
    analysis_type = Str(DEFAULT_AT)
    analysis_types = List
    extraction_device = Str(DEFAULT_ED)
    extraction_devices = List
    start_date = Date
    start_time = Time

    end_date = Date
    end_time = Time
    days_pad = Int(0)
    hours_pad = Int(18)

    #clear_selection_button = Button

    browser_pane = Any

    advanced_query=Button

    #def set_projects(self, ps, sel):
    #    self.oprojects = ps
    #    self.projects = ps
    #    self.trait_set(selected_project=sel)
    #
    #def set_samples(self, s, sel):
    #    self.samples = s
    #    self.osamples = s
    #    self.trait_set(selected_sample=sel)
    def load_browser_selection(self):
        self.debug('$$$$$$$$$$$$$$$$$$$$$ Loading browser selection')
        p=os.path.join(paths.hidden_dir, 'browser_selection')
        if os.path.isfile(p):
            try:
                with open(p, 'rb') as fp:
                    sel=pickle.load(fp)
            except (pickle.PickleError, EOFError, OSError),e:
                self.debug('Failed loaded previous browser selection. {}'.format(e))
                return

            self._load_browser_selection(sel)

    def _load_browser_selection(self, selection):
        def load(attr, values):
            def get(n):
                return next((p for p in values if p.name==n), None)
            try:
                sel=selection[attr]
            except KeyError:
                return

            vs=[get(pp) for pp in sel]
            vs=[pp for pp in vs if pp is not None]
            setattr(self, 'selected_{}'.format(attr), vs)

        load('projects', self.projects)
        load('samples', self.samples)

    def dump_browser_selection(self):
        self.debug('$$$$$$$$$$$$$$$$$$$$$ Dumping browser selection')

        ps=[]
        if self.selected_projects:
            ps=[p.name for p in self.selected_projects]

        ss=[]
        if self.selected_samples:
            ss=[p.name for p in self.selected_samples]

        obj=dict(projects=ps,
                 samples=ss)

        p=os.path.join(paths.hidden_dir, 'browser_selection')
        try:
            with open(p, 'wb') as fp:
                pickle.dump(obj, fp)
        except (pickle.PickleError, EOFError, OSError),e:
            self.debug('Failed dumping previous browser selection. {}'.format(e))
            return

    def prepare_destroy(self):
        self.dump_browser_selection()

    def activated(self):
        self.load_projects()

        db = self.manager.db
        with db.session_ctx():
            self._load_mass_spectrometers()
            self._load_analysis_types()
            self._load_extraction_devices()
        self._set_db()

        bind_preference(self.search_criteria, 'recent_hours', 'pychron.processing.recent_hours')
        self.load_browser_selection()

    def _set_db(self):
        #self.analysis_table.db = self.manager.db
        self.danalysis_table.db = self.manager.db

    def _load_mass_spectrometers(self):
        db = self.manager.db
        ms = [mi.name for mi in db.get_mass_spectrometers()]
        self.mass_spectrometers = ['Spectrometer', 'None'] + ms

    def _load_analysis_types(self):
        db = self.manager.db
        ms = [mi.name for mi in db.get_analysis_types()]
        self.analysis_types = ['Analysis Type', 'None'] + ms

    def _load_extraction_devices(self):
        db = self.manager.db
        ms = [mi.name for mi in db.get_extraction_devices()]
        self.extraction_devices = ['Extraction Device', 'None'] + ms

    def _create_browser_pane(self, **kw):
        self.browser_pane = BrowserPane(model=self, **kw)
        self.analysis_table.tabular_adapter = self.browser_pane.analysis_tabular_adapter

        return self.browser_pane

    def _ok_query(self):
        ms = self.mass_spectrometer not in (DEFAULT_SPEC, 'None')
        at = self.analysis_type not in (DEFAULT_AT, 'None')

        return ms and at

    def _ok_ed(self):
        return self.extraction_device not in (DEFAULT_ED, 'None')

    def _advanced_query_fired(self):

        app=self.window.application
        win, task, is_open = app.get_open_task('pychron.advanced_query')
        if is_open:
            win.activate()
        else:
            win.open()

    @on_trait_change('mass_spectrometer, analysis_type, extraction_device')
    def _query(self):
        if self._ok_query():

            db = self.manager.db
            with db.session_ctx() as sess:
                q = sess.query(meas_AnalysisTable)
                q = q.join(gen_LabTable)
                q = q.join(meas_MeasurementTable)
                q = q.join(gen_MassSpectrometerTable)
                q = q.join(gen_AnalysisTypeTable)

                if self._ok_ed():
                    q = q.join(meas_ExtractionTable)
                    q = q.join(gen_ExtractionDeviceTable)

                name = self.mass_spectrometer
                q = q.filter(gen_MassSpectrometerTable.name == name)
                if self._ok_ed():
                    q = q.filter(gen_ExtractionDeviceTable.name == self.extraction_device)

                q = q.filter(gen_AnalysisTypeTable.name == self.analysis_type)
                q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
                q = q.limit(200)

                ans = q.all()

                aa = [self._record_view_factory(ai) for ai in ans]

                self.danalysis_table.analyses = aa
                self.danalysis_table.oanalyses = aa
        else:
            if self.mass_spectrometer == 'None':
                self.mass_spectrometer = DEFAULT_SPEC
            if self.extraction_device == 'None':
                self.extraction_device = DEFAULT_ED
            if self.analysis_type == 'None':
                self.analysis_type = DEFAULT_AT

    @on_trait_change('analysis_table:selected')
    def _selected_analysis_changed(self, new):
        self._set_selected_analysis(new)

    def _set_selected_analysis(self, new):
        pass

    @on_trait_change('analysis_table:omit_invalid')
    def _omit_invalid_changed(self):
        self._selected_sample_changed(self.selected_samples)

    def _dclicked_sample_changed(self):
        ans = self._get_sample_analyses(self.selected_samples,
                                        include_invalid=not self.analysis_table.omit_invalid)
        print self.active_editor
        if self.active_editor:
            self.active_editor.unknowns = ans
            #self.unknowns_pane.items = self.active_editor.unknowns

    def _selected_samples_changed(self, new):
        if new:
            self._set_page(-1, reset_page=True)
            #include_invalid = not self.analysis_table.omit_invalid
            #
            #aa, tc = self._get_sample_analyses(new,
            #                                   include_invalid=include_invalid,
            #                                   page_width=self.analysis_table.page_width,
            #                                   page=-1)
            #
            #ans = self.analysis_table.set_analyses(aa,
            #                                       tc,
            #                                       reset_page=True)
            #
            ans=self.analysis_table.analyses
            if ans and self.auto_select_analysis:
                self.analysis_table.selected = ans[0]

    @on_trait_change('analysis_table:page')
    def _page_changed(self, new):
        self._set_page(new)

    def _set_page(self, page, reset_page=False):
        if not self.analysis_table.no_update:
            include_invalid = not self.analysis_table.omit_invalid
            page_width = self.analysis_table.page_width

            ans, tc = self._get_sample_analyses(self.selected_samples,
                                                include_invalid=include_invalid,
                                                page_width=page_width,
                                                page=page)

            self.analysis_table.set_analyses(ans, tc, page, reset_page=reset_page)

    def _analysis_table_default(self):
        at = AnalysisTable(db=self.manager.db)
        return at

    def _danalysis_table_default(self):
        at = AnalysisTable(db=self.manager.db)
        return at

#class BrowserTask(BaseBrowserTask):
#    name = 'Analysis Browser'
#
#
#    def activated(self):
#        editor = RecallEditor()
#        self._open_editor(editor)
#        self.load_projects()
#
#    def new_editor(self):
#        editor = RecallEditor()
#        self._open_editor(editor)
#
#    def _default_layout_default(self):
#        return TaskLayout(left=PaneItem('pychron.browser'))
#
#    def _set_selected_analysis(self, an):
#        if an and isinstance(self.active_editor, RecallEditor):
#        #             l, a, s = strip_runid(s)
#        #             an = self.manager.db.get_unique_analysis(l, a, s)
#            an = self.manager.make_analyses([an], calculate_age=True)[0]
#            #             an.load_isotopes(refit=False)
#            #self.active_editor.analysis_summary = an.analysis_summary
#            self.active_editor.analysis_view = an.analysis_view
#
#    def create_dock_panes(self):
#        return [self._create_browser_pane(multi_select=False)]
#
#    def _analysis_table_default(self):
#        at = AnalysisTable(db=self.manager.db)
#        return at
#
#    def _danalysis_table_default(self):
#        at = AnalysisTable(db=self.manager.db)
#        return at
#
#    def _dclicked_sample_changed(self):
#        pass

#===============================================================================
# handlers
#===============================================================================

#============= EOF =============================================
