#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Any, on_trait_change, Int, List, Bool, Property, Instance
from pyface.timer.do_later import do_later
#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.experiment.queue.base_queue import BaseExperimentQueue
from pychron.experiment.utilities.identifier import make_runid
from pychron.experiment.utilities.human_error_checker import HumanErrorChecker
from pychron.experiment.queue.experiment_queue_action import ExperimentQueueAction
from pychron.experiment.utilities.uv_human_error_checker import UVHumanErrorChecker
from pychron.ui.gui import invoke_in_main_thread


class ExperimentQueue(BaseExperimentQueue):
#     current_run = Any
    selected = Any
    executed_selected = Any
    dclicked = Any
    database_identifier = Int
    executed_runs = List
    executed_runs_scroll_to_row = Int
    automated_runs_scroll_to_row = Int
    linked_copy_cache = List
    queue_actions = List

    executed = Bool(False)

    human_error_checker=Instance(HumanErrorChecker, ())

    def select_run_idx(self, idx):
        if self.automated_runs:
            self.selected = self.automated_runs[idx:idx + 1]

    def reset(self):
        ans = self.automated_runs
        ens = self.executed_runs
        self._no_update = True
        for ei in reversed(ens):
            ei.state = 'not run'
            #             ei.aliquot = 0
            #             ei.assigned_aliquot=0
            #             ei.step = ''
            ans.insert(0, ei)

        self.executed_runs = []
        self.executed = False
        self._no_update = False

    #         self.update_needed = True
    #         self.refresh_table_needed = True

    def set_run_inprogress(self, aid):
        run = self._find_run(aid)

        # using the no_update ctx manager was not working
        # have to manually toggle _no_update

        self._no_update = True
        if run is not None:
            self.automated_runs.remove(run)
            self.executed_runs.append(run)
            idx = len(self.executed_runs) - 1
            #             self.trait_set(executed_runs_scroll_to_row=idx)
            #             do_later(self.trait_set, executed_runs_scroll_to_row=idx)
            #             invoke_in_main_thread(do_later, lambda:self.trait_set(executed_runs_scroll_to_row=idx))
            invoke_in_main_thread(do_later, lambda: self.trait_set(executed_runs_scroll_to_row=idx))
            #             invoke_in_main_thread(self.trait_set, executed_runs_scroll_to_row=idx)
            self.debug('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ set ex scroll to {}'.format(idx))
        else:
            self.debug('Problem removing {}'.format(aid))

        self._no_update = False

    def _find_run(self, aid):
        return next((a for a in self.automated_runs
                     if make_runid(a.labnumber, a.aliquot, a.step) == aid), None)

    def executed_paste_function(self, obj):
        return

    def paste_function(self, obj):

        ci = obj.clone_traits()
        ci.state = 'not run'
        if obj.user_defined_aliquot:
            ci.aliquot = obj.aliquot
        else:
            ci.aliquot = 0
        return ci

    #     _test = True

    @on_trait_change('automated_runs[]')
    def _refresh_info(self, new):

    #             do_later(self.trait_set, automated_runs_scroll_to_row=idx)

    #         if new > 1:
    #             if self._test:
    #                 self.executed_runs.append(new[0])
    #                 self._test = False

        if not self._no_update:
            self.debug('automated runs len changed {}'.format(len(new)))
            if new:
                idx = self.automated_runs.index(new[-1])
                self.debug('SSSSSSSSSSSSSS set AR scroll to {}'.format(idx))
                invoke_in_main_thread(do_later, lambda: self.trait_set(automated_runs_scroll_to_row=idx))

            if self.automated_runs:
                self.update_needed = True
                #                self.refresh_button = True

    @on_trait_change('automated_runs:state')
    def _refresh_table1(self):
        self.refresh_table_needed = True

    def _load_meta(self, meta):
        super(ExperimentQueue, self)._load_meta(meta)
        if 'actions' in meta:
            self.queue_actions = [ExperimentQueueAction(astr)
                                  for astr in meta['actions']
            ]

        else:
            self.debug('no actions provided for this queue')

    def _load_actions(self):
        pass

    def isExecutable(self):
        if self.check_runs():
            # test scripts
            return all([ai.executable for ai in self.automated_runs])

    def check_runs(self):
        hec=self.human_error_checker
        err = hec.check_runs(self.automated_runs, test_all=True)
        if err:
            hec.report_errors(err)
            return

        return True

    def new_runs_generator(self):
        runs = self.cleaned_automated_runs
        runs = [ri for ri in runs if ri.executable]
        rgen = (r for r in runs)
        return rgen, len(runs)

    def _extract_device_changed(self):
        self.debug('extract device changed {}'.format(self.extract_device))
        if 'uv' in self.extract_device.lower():
            k=UVHumanErrorChecker
        else:
            k=HumanErrorChecker

        self.human_error_checker=k()

#============= EOF =============================================
#        rgen = (r for r in newruns)
#        runs = self.executed_runs+self.cleaned_automated_runs
#
#        runs = [ri for ri in runs if ri.executable]
#
#        n = len(runs)
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
