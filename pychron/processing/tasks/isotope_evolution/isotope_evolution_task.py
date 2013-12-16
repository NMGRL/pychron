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
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import PaneItem, TaskLayout, Tabbed, HSplitter, \
    VSplitter

#from pychron.pychron_constants import MINNA_BLUFF_IRRADIATIONS
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.analysis_edit.panes import ControlsPane
from pychron.processing.tasks.actions.edit_actions import DatabaseSaveAction, FindAssociatedAction
from pychron.processing.tasks.figures.actions import SavePDFFigureAction


class IsotopeEvolutionTask(AnalysisEditTask):
    name = 'Isotope Evolutions'
    iso_evo_editor_count = 1
    id = 'pychron.analysis_edit.isotope_evolution',
    auto_select_analysis = False
    tool_bars = [SToolBar(DatabaseSaveAction(),
                          FindAssociatedAction(),
                              image_size=(16, 16)),
                     SToolBar(
                         SavePDFFigureAction())
                    ]

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.analysis_edit.isotope_evolution',
            left=HSplitter(
                Tabbed(PaneItem('pychron.browser'),
                       PaneItem('pychron.search.query')
                ),
                VSplitter(
                    Tabbed(
                        PaneItem('pychron.plot_editor'),
                        PaneItem('pychron.analysis_edit.unknowns')),
                    PaneItem('pychron.analysis_edit.controls'))))

    def create_dock_panes(self):
        self.unknowns_pane = self._create_unknowns_pane()
        self.controls_pane = ControlsPane()
        self.plot_editor_pane = PlotEditorPane()

        panes = [self.unknowns_pane,
                 self.controls_pane,
                 self.plot_editor_pane,
                 self._create_browser_pane()]

        return panes

    def new_isotope_evolution(self):
        from pychron.processing.tasks.isotope_evolution.isotope_evolution_editor import IsotopeEvolutionEditor

        editor = IsotopeEvolutionEditor(name='Iso Evo {:03n}'.format(self.iso_evo_editor_count),
                                        processor=self.manager)
        #selector = self.manager.db.selector

        #        selector.queries[0].criterion = 'NM-251'
        #        selector._search_fired()
        #         selector = self.manager.db.selector
        #         self.unknowns_pane.items = selector.records[150:160]
        #
        #         editor.unknowns = self.unknowns_pane.items
        self._open_editor(editor)
        self.iso_evo_editor_count += 1

    #_refit_thread = None

    #def refit_isotopes(self, dry_run=False):
    #    self.new_isotope_evolution()
    #
    #    #self.debug('refit disabled')
    #    #return
    #    #
    #    #from pychron.ui.thread import Thread
    #    #
    #    #if not self._refit_thread or not self._refit_thread.isRunning():
    #    #    pd = self.manager.open_progress()
    #    #    t = Thread(target=self._do_refit,
    #    #               name='refit_isotopes',
    #    #               args=(self._refit_isotopes_date_range, dry_run, pd))
    #    #    t.start()
    #    #    self._refit_thread = t
    #
    #def _gather_analyses(self, imports):
    #    db = self.manager.db
    #
    #    levels = (db.get_irradiation_level(irrad, level) \
    #              for irrad, levels in imports \
    #              for level in levels)
    #
    #    lns = (pi.labnumber for level in levels \
    #           for pi in level.positions \
    #           if pi.labnumber.sample.project.name in ('j', 'Minna Bluff', 'Mina Bluff') \
    #        )
    #    ans = [ai for ln in lns
    #           for ai in ln.analyses
    #           if ai.status == 0]
    #    return ans
    #
    #def _do_refit(self, fit_func, *args, **kw):
    #    self.info('Started refit')
    #    st = time.time()
    #
    #    fit_func(*args, **kw)
    #
    #    self.info('Refit finished {}s'.format(int(time.time() - st)))
    #
    #def _refit_analyses(self, ans, dry_run, pd):
    #    for ai in ans:
    #        if ai.status == 0:
    #            try:
    #                self.manager.refit_isotopes(ai, pd=pd)
    #            except Exception:
    #                import traceback
    #
    #                traceback.print_exc()
    #                ai.status = 10
    #
    #    db = self.manager.db
    #    if not dry_run:
    #        msg = 'changes committed'
    #        db.commit()
    #    else:
    #        msg = 'dry run- not changes committed'
    #        db.rollback()
    #
    #    self.info(msg)
    #
    #def _refit_isotopes_date_range(self, dry_run, pd):
    #    '''
    #        refit all analyses in date range
    #    '''
    #
    #    start = '1/1/2006'
    #    end = '1/1/2014'
    #
    #    ans = self.manager.db.selector.get_date_range(start, end, limit=-1)
    #    pd.max = len([ai for ai in ans if ai.status == 0]) - 1
    #    self._refit_analyses(ans, dry_run, pd)

    #     def _refit_isotopes_levels(self, dry_run, pd):
    #         imports = MINNA_BLUFF_IRRADIATIONS
    #         imports = [('NM-205', ['E', 'F' ]),
    #                    ('NM-256', ['F', ])]
    #         ans = self._gather_analyses(imports)
    #         pd.max = len(ans)
    #
    #         db = self.manager.db
    #
    #         for irrad, levels in imports:
    #             for level in levels:
    #                 self.info('extracting positions from {} {}'.format(irrad, level))
    #                 level = db.get_irradiation_level(irrad, level)
    #                 for pi in level.positions:
    #                     ln = pi.labnumber
    #                     sample = ln.sample
    #                     if sample.project.name in ('j', 'Minna Bluff', 'Mina Bluff'):
    #                         self.info('extracting analyses from {}'.format(ln.identifier))
    #                         self._refit_analyses(ln.analyses, dry_run, pd)


    #===============================================================================
    # equilibration tools
    #===============================================================================
    def calculate_optimal_eqtime(self):
        if self.active_editor:
            self.active_editor.calculate_optimal_eqtime()

            #===============================================================================
            # handlers
            #===============================================================================

    def do_easy_fit(self):
        self._do_easy(self._do_easy_fit)

    def _do_easy_fit(self, db, ep):

        doc = ep.doc('iso_fits')
        projects = doc['projects']
        unks = (ai for proj in projects \
                for si in db.get_samples(project=proj) \
                for ln in si.labnumbers \
                for ai in ln.analyses)
        found = []
        while 1:
            u = []
            for _ in xrange(100):
                try:
                    u.append(unks.next())
                except StopIteration:
                    pass
            if u:
                self.active_editor.set_items(u)
                # self.active_editor.unknowns=u
                # self.active_editor.unknowns.append(unks.next())
                found = self.find_associated_analyses(found=found)
                fits = doc['fit_isotopes']
                filters = doc['filter_isotopes']

                self.active_editor.save_fits(fits, filters)
                db.sess.commit()

        return True

        #def _dclicked_sample_changed(self, new):
        #    if self.active_editor:
        #        sa = self.selected_samples[0]
        #        ans = self._get_sample_analyses(sa)
        #        print ans
        #        self.unknowns_pane.items = ans

        #for sa in self.selected_samples:
        #    ans = self._get_sample_analyses(sa)
        #                 ans = man.make_analyses(ans)
        #self.unknowns_pane.items = ans

#============= EOF =============================================
