# ===============================================================================
# Copyright 2012 Jake Ross
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
import time
from itertools import groupby

from pyface.timer.do_later import do_later
from traits.api import Any, on_trait_change, Int, List, Bool, \
    Instance, Property, Str, HasTraits, Event, Long
from traits.trait_types import Date
from traitsui.api import View, Item, UItem

from pychron.core.helpers.ctx_managers import no_update
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.qt.tabular_editor import MoveToRow
from pychron.envisage.view_util import open_view
from pychron.experiment.queue.base_queue import BaseExperimentQueue
from pychron.experiment.queue.select_attr_view import SelectAttrView
from pychron.experiment.utilities.human_error_checker import HumanErrorChecker
from pychron.experiment.utilities.identifier import make_runid
from pychron.experiment.utilities.uv_human_error_checker import UVHumanErrorChecker
from pychron.paths import paths
from pychron.pychron_constants import DVC_PROTOCOL


class RepeatRunBlockView(HasTraits):
    value = Int

    def traits_view(self):
        v = View(Item('value', label='Repeat'),
                 kind='modal',
                 title='Repeat Selected Run Block',
                 width=300,
                 buttons=['OK', 'Cancel'])
        return v


class NewRunBlockView(HasTraits):
    name = Str

    def traits_view(self):
        v = View(Item('name'),
                 kind='modal',
                 title='New Run Block',
                 buttons=['OK', 'Cancel'],
                 width=200)
        return v


class ExperimentQueue(BaseExperimentQueue):
    executed_selected = Any
    dclicked = Any
    database_identifier = Long
    display_executed_runs = Property(depends_on='executed_runs[]')
    n_executed_display = Int(5)
    executed_runs = List
    executed_runs_scroll_to_row = Int
    automated_runs_scroll_to_row = Int
    # linked_copy_cache = List
    start_timestamp = Date
    # queue_actions = List
    auto_save_detector_ic = Bool

    executed = Bool(False)

    human_error_checker = Instance(HumanErrorChecker, ())
    execution_ratio = Property

    refresh_blocks_needed = Event
    _auto_save_time = 0
    _temp_analysis = None

    def auto_save(self):
        if self._auto_save_time and time.time() - self._auto_save_time < 0.25:
            return

        self._auto_save_time = time.time()
        path = self.path
        if os.path.isfile(path):
            bk = os.path.join(paths.auto_save_experiment_dir, '{}.bak'.format(self.name))
        else:
            bk = os.path.join(paths.auto_save_experiment_dir, 'Untitled.bak')

        self.debug('Autosaving to {}'.format(bk))
        with open(bk, 'w') as wfile:
            self.dump(wfile)

    def toggle_skip(self):
        self.debug('Toggle skip')
        for si in self.selected:
            si.skip = not si.skip
        self.selected = []
        self.refresh_table_needed = True

    def toggle_end_after(self):
        self.debug('Toggle end after')
        sel = self.selected
        for ai in self.automated_runs:
            if ai not in sel:
                ai.end_after = False

        si = sel[-1]

        idx = self.automated_runs.index(si)

        si.end_after = not si.end_after

        self.debug('setting {} end_after to {}'.format(idx, si.end_after))

        self.selected = []
        self.refresh_table_needed = True

    def repeat_block(self):
        rbv = RepeatRunBlockView()
        info = rbv.edit_traits()
        if info.result:
            self.add_runs(self.selected, freq=rbv.value, is_repeat_block=True)

    def make_run_block(self):
        nrbv = NewRunBlockView()
        info = nrbv.edit_traits()
        if info.result:
            p = os.path.join(paths.run_block_dir, '{}.txt'.format(nrbv.name))
            with open(p, 'w') as wfile:
                self.dump(wfile, runs=self.selected, include_meta=False)
            self.refresh_blocks_needed = True

    def move_selected_to_row(self):
        e = MoveToRow()
        info = e.edit_traits()
        if info.result:
            self._move_selected(e.row - 1)

    def move_selected_first(self):
        self._move_selected(0)

    def move_selected_last(self):
        with no_update(self):
            for si in self.selected:
                self.automated_runs.remove(si)
            self.automated_runs.extend(self.selected)

    def copy_selected_first(self):
        self._copy_selected(0)

    def copy_selected_last(self):
        self.information_dialog('"Copy to End" Not Implemented')

    def jump_to_end(self):
        self.automated_runs_scroll_to_row = len(self.automated_runs) - 1

    def jump_to_start(self):
        self.automated_runs_scroll_to_row = 0

    def select_unknowns(self):
        def test(ss):
            return ss.analysis_type == 'unknown'

        self.selected = [si for si in self.cleaned_automated_runs if test(si)]

    def select_same(self):
        ident = self.selected[0].identifier
        self._select_same(lambda si: si.identifier == ident)

    def select_same_attr(self):

        hs, attrs = self._get_dump_attrs()
        hs = list(attrs)

        ev = SelectAttrView(available_attributes=hs)
        info = ev.edit_traits()
        if info.result:
            if ev.attributes:

                s = self.selected[0]
                def test(v):
                    return all([getattr(v, k) == getattr(s, k) for k in ev.attributes])

                self._select_same(test)

    def _select_same(self, test):
        self.selected = [si for si in self.cleaned_automated_runs if test(si)]

    def count_labnumber(self, ln):
        ans = [ai for ai in self.automated_runs if ai.labnumber == ln]
        i = 0
        for _ in groupby(ans, key=lambda x: x.user_defined_aliquot):
            i += 1
        return i

    # def count_labnumber(self, ln):
    # ans = [ai for ai in self.automated_runs if ai.labnumber == ln]
    # i = 0
    # for args in groupby(ans, key=lambda x: x.user_defined_aliquot):
    # i += 1
    # return i

    def select_run_idx(self, idx):
        if self.automated_runs:
            self.selected = self.automated_runs[idx:idx + 1]

    def show_evolutions(self, isotopes=None, **kw):
        if self.executed_selected:
            dvc = self.application.get_service(DVC_PROTOCOL)
            if dvc:
                spec = self.executed_selected[0]

                analysis = None
                if self._temp_analysis and spec.uuid == self._temp_analysis[0].uuid:
                    analysis = self._temp_analysis

                with dvc.session_ctx(use_parent_session=False):
                    if analysis is None:
                        analysis = dvc.get_analysis(spec.uuid)

                    if analysis:
                        for ai in analysis:
                            ai.show_isotope_evolutions(isotopes=isotopes, **kw)

                self._temp_analysis = analysis

    def show_summary(self):
        """
        show a summary view for ``spec`` using its ``result``
        :return:
        """
        if self.executed_selected:
            from pychron.core.ui.text_editor import myTextEditor
            v = View(UItem('summary', style='custom', editor=myTextEditor(editable=False,
                                                                          fontsize=14)),
                     title='Summary',
                     width=900,
                     kind='livemodal',
                     resizable=True)
            open_view(self.executed_selected[0].result, view=v)

    def reset(self):
        """
            clear the step from the run. increment the aliquot if a step heat and experiment completed.
        """

        ens = self.executed_runs

        self._no_update = True

        finished = len(self.automated_runs) == 0
        nans = []
        # for ei in reversed(ens):
        for ei in ens:
            ei.state = 'not run'
            if not ei.is_step_heat():
                ei.aliquot = 0
            elif finished and ei.user_defined_aliquot:
                ei.user_defined_aliquot += 1

            ei.reset()
            nans.append(ei)
            # nans.insert(0, ei)

        nans.extend(self.automated_runs)
        self.automated_runs = nans

        self.executed_runs = []
        self.executed = False
        self._no_update = False

    def set_run_inprogress(self, aid):
        run = self._find_run(aid)

        # using the no_update ctx manager was not working
        # have to manually toggle _no_update

        self._no_update = True
        if run is not None:

            self.automated_runs.remove(run)
            self.executed_runs.append(run)

            idx = len(self.executed_runs) - 1
            invoke_in_main_thread(do_later, lambda: self.trait_set(executed_runs_scroll_to_row=idx))
            # self.debug('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ set ex scroll to {}'.format(idx))
        else:
            self.debug('Problem removing {}'.format(aid))

        self._no_update = False

    def executed_paste_function(self, obj):
        ci = self.paste_function(obj)
        return ci

    def paste_function(self, obj):

        ci = obj.clone_traits()
        ci.state = 'not run'
        ci.aliquot = 0
        ci.step = -1
        ci.conflicts_checked = False

        if ci.is_step_heat():
            ci.user_defined_aliquot = ci.aliquot

        return ci

    # def _load_meta(self, meta):
    #     super(ExperimentQueue, self)._load_meta(meta)
    #     if 'actions' in meta:
    #         self.queue_actions = [ExperimentQueueAction(astr)
    #                               for astr in meta['actions']]
    #     else:
    #         self.debug('no actions provided for this queue')

    def is_executable(self):
        if self.check_runs():
            # test scripts
            return all([ai.executable for ai in self.cleaned_automated_runs])

    def check_runs(self):
        hec = self.human_error_checker
        err = hec.check_runs(self.cleaned_automated_runs, test_all=True)
        if err:
            hec.report_errors(err)
            return

        return True

    def new_runs_generator(self):
        runs = self.cleaned_automated_runs
        runs = [ri for ri in runs if ri.executable]
        rgen = (r for r in runs)
        return rgen, len(runs)

    # private
    def _find_run(self, aid):
        return next((a for a in self.automated_runs
                     if make_runid(a.labnumber, a.aliquot, a.step) == aid), None)

    def _load_actions(self):
        pass

    def _load_meta_hook(self, meta):
        bool_default = lambda x: bool(x) if x else False
        self._set_meta_param('auto_save_detector_ic', meta, bool_default)
        self.debug('$$$$$$$$$$$$$$$$$$$$$ auto_save_detector_ic={}'.format(self.auto_save_detector_ic))

    def _get_display_executed_runs(self):
        return self.executed_runs[-self.n_executed_display:]

    def _get_execution_ratio(self):
        ex = len(self.executed_runs)
        tc = len(self.cleaned_automated_runs) + ex
        return '{}/{}'.format(ex, tc)

    def _copy_selected(self, idx):
        with no_update(self):
            for si in reversed(self.selected):
                self.automated_runs.insert(idx, si.tocopy())

    def _move_selected(self, idx):
        with no_update(self):
            for si in self.selected:
                self.automated_runs.remove(si)

            for si in reversed(self.selected):
                self.automated_runs.insert(idx, si)

    def _extract_device_changed(self):
        self.debug('extract device changed {}'.format(self.extract_device))
        if 'uv' in self.extract_device.lower():
            k = UVHumanErrorChecker
        else:
            k = HumanErrorChecker

        self.human_error_checker = k()

    @on_trait_change('automated_runs[]')
    def _refresh_info(self, new):
        if new and not self._no_update:
            idx = self.automated_runs.index(new[-1])
            self.debug('SSSSSSSSSSSSSS set AR scroll to {}'.format(idx))
            self.refresh_info_needed = True
            invoke_in_main_thread(do_later, lambda: self.trait_set(automated_runs_scroll_to_row=idx))

    @on_trait_change('automated_runs:state')
    def _refresh_table1(self):
        self.refresh_table_needed = True

# ============= EOF =============================================
# rgen = (r for r in newruns)
# runs = self.executed_runs+self.cleaned_automated_runs
#
# runs = [ri for ri in runs if ri.executable]
#
# n = len(runs)
#        rgen = (r for r in runs)
#        if last_ran is not None:
#            # get index of last run in self.automated_runs
#            if self._cached_runs:
#                startid = self._cached_runs.index(last_ran) + 1
#                # for graphic clarity load the finished runs back in
# #                cnts = {}
#                for ci, ai in zip(self._cached_runs[:startid], runs[:startid]):
#                    ai.trait_set(state=ci.state, aliqupt=ci.aliquot,
#                                 step=ci.step,
#                                 skip=ci.skip)
#
#                newruns = runs[startid:]
#
#                run = newruns[0]
# #                runid = run.runid
#                runid = make_runid(run.labnumber, run.aliquot, run.step)
#
#                self.info('starting at analysis {} (startid={} of {})'.format(runid, startid + 1, n))
#                n = len(newruns)
#                rgen = (r for r in newruns)
#            else:
#                self.info('last ran analysis {} does not exist in modified experiment set. starting from the beginning')
#
#        return rgen, n


#     def test_runs(self):
#         pass
#         runs = self.cleaned_automated_runs
#
#         if runs:
#             ar = runs[0].make_run(new_uuid=False)
#
#             failed = False
# #             hec = HumanErrorChecker()
# #
# #             err = hec.check(runs, test_all=True)
# #             if err:
# #                 hec.report_errors(err)
# #                 failed = True
# #             else:
#             for ri in runs:
#                 for si in SCRIPT_NAMES:
#                     sn = getattr(ri, si)
#                     script = getattr(ar, si)
#                     if script:
#                         shash = hashlib.md5(script.text).digest()
#
#                         setattr(ar.script_info, '{}_name'.format(si), sn)
#                         nscript = getattr(ar, si)
#                         nhash = hashlib.md5(nscript.text).digest()
#                         if shash != nhash:
#                             if not nscript.syntax_ok():
#                                 failed = True
# #                                 return 'Error in script {}'.format(script.name)
#
#
#             self.executable = not failed
