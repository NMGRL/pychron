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
from itertools import groupby
import traceback
from datetime import timedelta

from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import PaneItem, TaskLayout, Tabbed, HSplitter, \
    VSplitter





#from pychron.pychron_constants import MINNA_BLUFF_IRRADIATIONS
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane
from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.analysis_edit.panes import ControlsPane
from pychron.processing.tasks.actions.edit_actions import DatabaseSaveAction, FindAssociatedAction
from pychron.processing.tasks.browser.util import browser_pane_item
from pychron.processing.tasks.figures.actions import SavePDFFigureAction
from pychron.processing.tasks.isotope_evolution.find_associated_parameters import FindAssociatedParametersDialog
from pychron.processing.tasks.isotope_evolution.isotope_evolution_editor import IsotopeEvolutionEditor


class IsotopeEvolutionTask(AnalysisEditTask):
    name = 'Isotope Evolutions'
    iso_evo_editor_count = 1
    id = 'pychron.processing.isotope_evolution',
    auto_select_analysis = False
    tool_bars = [SToolBar(DatabaseSaveAction(),
                          FindAssociatedAction(),
                          image_size=(16, 16)),
                 SToolBar(
                     SavePDFFigureAction())
    ]

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.processing.isotope_evolution',
            left=HSplitter(
                browser_pane_item(),
                # Tabbed(PaneItem('pychron.browser'),
                #        PaneItem('pychron.search.query')
                # ),
                VSplitter(
                    Tabbed(
                        PaneItem('pychron.plot_editor'),
                        PaneItem('pychron.processing.unknowns')),
                    PaneItem('pychron.processing.controls'))))

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

    def find_associated_analyses(self):
        """
        """
        if not self.has_active_editor():
            return

        if not isinstance(self.active_editor, IsotopeEvolutionEditor):
            self.warning_dialog('Find associated only available from Isotope Evolution tab.')
            return

        db = self.manager.db
        ret = self._get_find_parameters()
        if not ret:
            return
        model = ret

        uuids = [ai.uuid for ai in self.unknowns_pane.items]
        tans = []
        atypes = model.get_atypes()
        ms = model.get_mass_spectrometers()
        if not (ms and atypes):
            self.information_dialog('Select a set of Analysis Types and Spectrometers')
            return

        with db.session_ctx():
            progress = self.manager.open_progress(len(atypes))
            found = []
            for name, atype in atypes:
                progress.change_message('Finding associated {}'.format(atype))
                lpost, hpost = model.get_posts()
                for mi in ms:
                    ans = self._find_associated_analyses(db, lpost, hpost, atype, mi)
                    ans = [ai for ai in ans if ai.uuid not in uuids]
                    uuids.extend([ai.uuid for ai in ans])
                    tans.extend(ans)
                    found.append((mi, name, len(ans)))
            progress.close()

            m = '\n'.join(['{} {} = {}'.format(*f) for f in found])
            msg = 'Found Associated Analyses\n{}\n Continue?'.format(m)
            if self.confirmation_dialog(msg):
                # tans = [IsotopeRecordView(ai) for ai in tans]
                # ans = self.active_editor.analyses
                # ans.extend(tans)
                self.active_editor.set_items(tans, is_append=True)

    def _get_find_parameters(self):
        f = FindAssociatedParametersDialog()

        ais = self.active_editor.analyses
        if ais:
            unks = ais
        elif self.analysis_table.selected:
            ans = self.analysis_table.selected
            unks = ans[:]
        elif self.selected_samples:
            ans = self.analysis_table.analyses
            unks = ans[:]
        elif self.selected_projects:
            with self.manager.db.session_ctx():
                ans = self._get_projects_analyzed_analyses(self.selected_projects)
                unks = [IsotopeRecordView(ai) for ai in ans]
        else:
            self.information_dialog('Select a list of projects, samples or analyses')
            return

        ts = [get_datetime(ai.timestamp) for ai in unks]
        lpost, hpost = min(ts), max(ts)
        f.model.nominal_lpost_date = lpost.date()
        f.model.nominal_hpost_date = hpost.date()

        f.model.nominal_lpost_time = lpost.time()
        f.model.nominal_hpost_time = hpost.time()

        ms = list(set([ai.mass_spectrometer for ai in unks]))
        f.model.available_mass_spectrometers = ms
        f.model.mass_spectrometers = ms

        info = f.edit_traits(kind='livemodal')
        if info.result:
            return f.model

    def _find_associated_analyses(self, db, lpost, hpost, atype, ms):
        ans = db.get_date_range_analyses(lpost, hpost,
                                         atype=atype,
                                         spectrometer=ms)
        if ans:
            self.debug('{} {} to {}. nanalyses={}'.format(atype, lpost, hpost, len(ans)))
            # ans = [ai for ai in ans if ai.uuid not in uuids]
            self.debug('new ans {}'.format(len(ans)))
        return ans

    def _get_projects_analyzed_analyses(self, projects):
        db = self.manager.db
        if not hasattr(projects, '__iter__'):
            projects = (projects,)

        ans = []
        test = lambda x: len(x.analyses)
        with db.session_ctx():
            for pp in projects:
                ss = db.get_samples(project=pp.name)
                ans.extend([ai for s in ss
                            for li in s.labnumbers if test(li)
                            for ai in li.analyses])
        return ans

    #===============================================================================
    # equilibration tools
    #===============================================================================
    def calculate_optimal_eqtime(self):
        if self.active_editor:
            self.active_editor.calculate_optimal_eqtime()

    #===============================================================================
    # handlers
    #===============================================================================
    #===============================================================================
    # easy
    #===============================================================================
    def do_easy_fit(self):
        self._do_easy(self._do_easy_fit)

    def _do_easy_fit(self, db, ep, prog):

        doc = ep.doc('iso_fits')
        projects = doc['projects']
        unks = (ai for proj in projects \
                for si in db.get_samples(project=proj) \
                for ln in si.labnumbers \
                for ai in ln.analyses)
        found = []
        while 1:
            u = []

            for _ in xrange(200):
                try:
                    u.append(unks.next())
                except (Exception, StopIteration), e:
                    self.debug(traceback.print_exc())
                    break

            if u:
                self.active_editor.set_items(u, use_cache=False, progress=prog)

                found = self._easy_find_associated_analyses(found=found, use_cache=False, progress=prog)
                fits = doc['fit_isotopes']
                filters = doc['filter_isotopes']

                self.active_editor.save_fits(fits, filters, progress=prog)
                db.sess.commit()
            else:
                break

        return True

    def _easy_find_associated_analyses(self, found=None, use_cache=True, progress=None):
        if self.active_editor:
            unks = self.active_editor.analyses

            key = lambda x: x.labnumber
            unks = sorted(unks, key=key)

            db = self.manager.db
            with db.session_ctx():
                tans = []
                if found is None:
                    uuids = []
                else:
                    uuids = found

                ngroups = len(list(groupby(unks, key=key)))
                if progress is None:
                    progress = self.manager.open_progress(ngroups + 1)
                else:
                    progress.increase_max(ngroups + 1)

                for ln, ais in groupby(unks, key=key):
                    msg = 'find associated analyses for labnumber {}'.format(ln)
                    self.debug(msg)
                    progress.change_message(msg)

                    ais = list(ais)
                    ts = [get_datetime(ai.timestamp) for ai in ais]
                    ref = ais[0]
                    ms = ref.mass_spectrometer
                    ed = ref.extract_device
                    self.debug("{} {}".format(ms, ed))
                    for atype in ('blank_unknown', 'blank_air', 'blank_cocktail',
                                  'air', 'cocktail'):
                        for i in range(10):
                            td = timedelta(hours=6 * (i + 1))
                            lpost, hpost = min(ts) - td, max(ts) + td

                            ans = db.get_date_range_analyses(lpost, hpost,
                                                             atype=atype,
                                                             spectrometer=ms)

                            if ans:
                                self.debug('{} {} to {}. nanalyses={}'.format(atype, lpost, hpost, len(ans)))
                                ans = [ai for ai in ans if ai.uuid not in uuids]
                                self.debug('new ans {}'.format(len(ans)))
                                if ans:
                                    tans.extend(ans)
                                    uuids.extend([ai.uuid for ai in ans])
                                break

                progress.soft_close()

                self.active_editor.set_items(tans, is_append=True,
                                             use_cache=use_cache, progress=progress)
                return uuids
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
#_refit_thread = None

#def refit_isotopes(self, dry_run=False):
#    self.new_isotope_evolution()
#
#    #self.debug('refit disabled')
#    #return
#    #
#    #from pychron.core.ui.thread import Thread
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
