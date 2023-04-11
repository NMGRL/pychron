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

from pyface.timer.do_later import do_later
from traits.api import (
    Any,
    on_trait_change,
    Int,
    List,
    Bool,
    Instance,
    Property,
    Str,
    HasTraits,
    Event,
    Long,
)
from traits.trait_types import Date
from traitsui.api import View, Item, UItem

from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import add_extension
from pychron.core.helpers.iterfuncs import groupby_key, partition
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.select_same import SelectSameMixin
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.qt.tabular_editor import MoveToRow
from pychron.envisage.view_util import open_view
from pychron.experiment.queue.base_queue import BaseExperimentQueue
from pychron.experiment.queue.value_editor import ValueEditor
from pychron.experiment.utilities.human_error_checker import HumanErrorChecker
from pychron.experiment.utilities.runid import make_runid
from pychron.experiment.utilities.uv_human_error_checker import UVHumanErrorChecker
from pychron.paths import paths
from pychron.pychron_constants import DVC_PROTOCOL
from pychron.stage.maps.laser_stage_map import LaserStageMap


class RepeatRunBlockView(HasTraits):
    value = Int

    def traits_view(self):
        v = okcancel_view(
            Item("value", label="Repeat"),
            kind="modal",
            title="Repeat Selected Run Block",
            width=300,
        )
        return v


class NewRunBlockView(HasTraits):
    name = Str

    def traits_view(self):
        v = okcancel_view(Item("name"), kind="modal", title="New Run Block", width=200)
        return v


class ExperimentQueue(BaseExperimentQueue, SelectSameMixin):
    executed_selected = Any
    dclicked = Any
    database_identifier = Long
    display_executed_runs = Property(depends_on="executed_runs[]")
    n_executed_display = Int(5)
    executed_runs = List
    executed_runs_scroll_to_row = Int
    automated_runs_scroll_to_row = Int
    start_timestamp = Date
    auto_save_detector_ic = Bool
    patterns = List

    executed = Bool(False)

    human_error_checker = Instance(HumanErrorChecker)
    execution_ratio = Property

    refresh_blocks_needed = Event

    default_attr = "identifier"
    patterns = List

    _auto_save_time = 0
    _temp_analysis = None

    def auto_save(self):
        if self._auto_save_time and time.time() - self._auto_save_time < 0.25:
            return

        self._auto_save_time = time.time()
        path = self.path
        if os.path.isfile(path):
            bk = os.path.join(
                paths.auto_save_experiment_dir, "{}.bak".format(self.name)
            )
        else:
            bk = os.path.join(paths.auto_save_experiment_dir, "Untitled.bak")

        self.debug("hAutosaving to {}".format(bk))
        with open(bk, "w") as wfile:
            self.dump(wfile)

    def toggle_skip(self):
        self.debug("Toggle skip")
        for si in self.selected:
            si.skip = not si.skip
        self.selected = []
        self.refresh_table_needed = True

    def toggle_end_after(self):
        self.debug("Toggle end after")
        sel = self.selected
        for ai in self.automated_runs:
            if ai not in sel:
                ai.end_after = False

        si = sel[-1]

        idx = self.automated_runs.index(si)

        si.end_after = not si.end_after

        self.debug("setting {} end_after to {}".format(idx, si.end_after))

        self.selected = []
        self.refresh_table_needed = True

    def open_value_editor(self):
        ve = ValueEditor(self)
        open_view(ve)

    def motion_saver(self):
        stage_map_klass = LaserStageMap

        t = self.tray
        path = os.path.join(paths.map_dir, add_extension(t, ".txt"))
        sm = stage_map_klass(file_path=path)
        if sm.load():
            new_pos = []
            ans = self.automated_runs[:]
            for holes in sm.motion_saver_holes():
                for hi in holes:
                    a = next((ai for ai in ans if ai.position == hi.id), None)
                    if a:
                        new_pos.append(a)
                        ans.remove(a)

            self.automated_runs = ans
            self.refresh_table_needed = True

    def order_from_file(self):
        """
        open a txt file that contains the positions in execution order
        :return:
        """
        self.warning_dialog("Order from file not yet implemented")
        return

        p = self.open_file_dialog()
        if p is not None:
            with open(p, "r") as rfile:
                positions = reversed(rfile.readlines())
                for cpos in positions:
                    arun = next(
                        (a for a in self.automated_runs if a.position == cpos.strip()),
                        None,
                    )
                    if arun:
                        self.automated_runs.remove(arun)
                        self.automated_runs.insert(0, arun)

    def randomize_all(self):
        from random import shuffle

        aruns = self.automated_runs[:]
        shuffle(aruns)
        self.automated_runs = aruns
        self.refresh_table_needed = True

    def randomize_unknowns(self):
        """
        1. get indices of non unknowns
        2. partition into two lists unks, non-unks
        3. randomize unks
        4. insert non-unks back in using original indices

        :return:
        """

        aruns = self.automated_runs[:]

        def predicate(x):
            return not x.skip

        skip_idx = [i for i, a in enumerate(aruns) if not predicate(a)]

        aruns, skipped = partition(aruns, predicate=predicate)

        def predicate(x):
            return x.analysis_type == "unknown"

        idx = [i for i, a in enumerate(aruns) if not predicate(a)]

        unks, refs = partition(aruns, predicate=predicate)

        unks = list(unks)
        refs = list(refs)
        for i, r in list(zip(idx, refs)):
            unks.insert(i, r)

        for i, r in list(zip(skip_idx, skipped)):
            unks.insert(i, r)

        self.automated_runs = unks
        self.refresh_table_needed = True

    def group_extractions2(self):
        """
        group using ABC, ABC, ABC
        :return:
        """
        sel = self.selected
        evs = sorted({s.extract_value for s in sel})
        n = len(evs)

        with no_update(self):
            gs = []
            for i, a in enumerate(self.automated_runs):
                if a.extract_value == evs[0]:
                    gs.extend(self.automated_runs[i : i + n])

            if gs:
                for gi in gs:
                    self.automated_runs.remove(gi)

                for gi in reversed(gs):
                    self.automated_runs.insert(0, gi)

    def group_extractions(self):
        """
        group using AAA, BBB, CCC
        :return:
        """
        sel = self.selected

        evs = {s.extract_value for s in sel}

        with no_update(self):
            gs = []
            for ev in sorted(evs):
                for a in self.automated_runs:
                    if a.extract_value == ev:
                        gs.append(a)

            if gs:
                for gi in gs:
                    self.automated_runs.remove(gi)

                for gi in reversed(gs):
                    self.automated_runs.insert(0, gi)

    def repeat_block(self):
        if self.selected:
            rbv = RepeatRunBlockView()
            info = rbv.edit_traits()
            if info.result:
                self.add_runs(self.selected, freq=rbv.value, is_repeat_block=True)
        else:
            self.information_dialog("Please select a set of analyses to repeat")

    def make_run_block(self):
        nrbv = NewRunBlockView()
        info = nrbv.edit_traits()
        if info.result:
            p = os.path.join(paths.run_block_dir, "{}.txt".format(nrbv.name))
            with open(p, "w") as wfile:
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

    def move(self, step):
        if self.selected:
            with no_update(self):
                run = self.selected[0]
                idx = self.automated_runs.index(run)

                idx = max(min(0, idx + step), len(self.automated_runs) - 1)
                self._move_selected(idx + step)

    def copy_selected_first(self):
        self._copy_selected(0)

    def copy_selected_last(self):
        self.information_dialog('"Copy to End" Not Implemented')

    def jump_to_end(self):
        self.automated_runs_scroll_to_row = len(self.automated_runs) - 1

    def jump_to_start(self):
        self.automated_runs_scroll_to_row = 0

    def select_special(self):
        def test(ss):
            return ss.analysis_type != "unknown"

        self.selected = [si for si in self.cleaned_automated_runs if test(si)]

    def select_unknowns(self):
        def test(ss):
            return ss.analysis_type == "unknown"

        self.selected = [si for si in self.cleaned_automated_runs if test(si)]

    def select_same(self):
        ident = self.selected[0].identifier
        self._select_same(lambda si: si.identifier == ident)

    def _get_records(self):
        return self.cleaned_automated_runs

    def _get_selection_attrs(self):
        hs, attrs = self._get_dump_attrs()
        return list(attrs)

    def count_labnumber(self, ln):
        ans = [
            ai for ai in self.automated_runs if ai.labnumber == ln and ai.is_step_heat()
        ]
        i = 0

        for _ in groupby_key(ans, "user_defined_aliquot"):
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
            self.selected = self.automated_runs[idx : idx + 1]

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

            v = View(
                UItem(
                    "summary",
                    style="custom",
                    editor=myTextEditor(editable=False, fontsize=14),
                ),
                title="Summary",
                width=900,
                kind="livemodal",
                resizable=True,
            )
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
            ei.state = "not run"
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
            invoke_in_main_thread(
                do_later, lambda: self.trait_set(executed_runs_scroll_to_row=idx)
            )
            # self.debug('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ set ex scroll to {}'.format(idx))
        else:
            self.debug("Problem removing {}".format(aid))

        self._no_update = False

    def executed_paste_function(self, obj):
        ci = self.paste_function(obj)
        return ci

    def paste_function(self, obj):
        ci = obj.clone_traits()
        ci.state = "not run"
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
    def _human_error_checker_default(self):
        return self._human_error_checker_factory()

    def _human_error_checker_factory(self, klass=None):
        if klass is None:
            klass = HumanErrorChecker

        spec_man = None
        if self.application:
            from pychron.spectrometer.base_spectrometer_manager import (
                BaseSpectrometerManager,
            )

            spec_man = self.application.get_service(BaseSpectrometerManager)

        hec = klass(spectrometer_manager=spec_man)
        return hec

    def _find_run(self, aid):
        return next(
            (
                a
                for a in self.automated_runs
                if make_runid(a.labnumber, a.aliquot, a.step) == aid
            ),
            None,
        )

    def _load_actions(self):
        pass

    def _load_meta_hook(self, meta):
        bool_default = lambda x: bool(x) if x else False
        self._set_meta_param("auto_save_detector_ic", meta, bool_default)
        self.debug(
            "$$$$$$$$$$$$$$$$$$$$$ auto_save_detector_ic={}".format(
                self.auto_save_detector_ic
            )
        )

    def _get_display_executed_runs(self):
        return self.executed_runs[-self.n_executed_display :]

    def _get_execution_ratio(self):
        ex = len(self.executed_runs)
        tc = len(self.cleaned_automated_runs) + ex
        return "{}/{}".format(ex, tc)

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
        self.debug("extract device changed {}".format(self.extract_device))
        if "uv" in self.extract_device.lower():
            k = UVHumanErrorChecker
        else:
            k = HumanErrorChecker

        self.human_error_checker = self._human_error_checker_factory(k)

    @on_trait_change("automated_runs[]")
    def _refresh_info(self, new):
        if new and not self._no_update:
            idx = self.automated_runs.index(new[-1])
            self.debug("SSSSSSSSSSSSSS set AR scroll to {}".format(idx))
            self.refresh_info_needed = True
            self.automated_runs_scroll_to_row = idx
            # invoke_in_main_thread(do_later, lambda: self.trait_set(automated_runs_scroll_to_row=idx))

    @on_trait_change("automated_runs:state")
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
