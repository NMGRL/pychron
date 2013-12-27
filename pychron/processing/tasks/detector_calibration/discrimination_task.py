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
from pychron.processing.tasks.analysis_edit.adapters import ReferencesAdapter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.analysis_edit.interpolation_task import InterpolationTask


class DiscrimintationTask(InterpolationTask):
    id = 'pychron.analysis_edit.discrimination'
    ic_factor_editor_count = 1
    references_adapter = ReferencesAdapter

    def do_easy_discrimination(self):
        self._do_easy(self._easy_discrimination)

    def _easy_discrimination(self, db, ep, prog):
        doc = ep.doc('disc')
        projects = doc['projects']
        disc, disc_err = doc['discrimination']
        det = doc['detector']

        ans = [ai for proj in projects
               for si in db.get_samples(project=proj)
               for ln in si.labnumbers
               for ai in ln.analyses]

        prog.increase_max(len(ans))
        # prog = self.manager.open_progress(len(ans) + 1)
        for ai in ans:
            if prog.canceled:
                return
            elif prog.accepted:
                break

            rid = '{}-{:02n}{}'.format(ai.labnumber.identifier, ai.aliquot, ai.step)
            prog.change_message('Setting discrimination={} +/-{} detector={} analysis={}'.format(disc, disc_err,
                                                                                                 det, rid))

            history = db.add_detector_parameter_history(ai)
            db.add_detector_parameter(history,
                                      detector=det,
                                      disc=disc,
                                      disc_error=disc_err)

            ai.selected_histories.selected_detector_param = history

            #an=self.manager.make_analysis(ai, calculate_age=True)
            #self.manager.save_arar(an, ai)

        # prog.close()
        return True

        #def _default_layout_default(self):
        #    return TaskLayout(
        #id='pychron.analysis_edit.ic_factor',
        #left=Splitter(
        #           PaneItem('pychron.analysis_edit.unknowns'),
        #           PaneItem('pychron.analysis_edit.references'),
        #           PaneItem('pychron.analysis_edit.controls'),
        #           orientation='vertical'
        #           ),
        #right=Splitter(
        #               PaneItem('pychron.search.query'),
        #               orientation='vertical'
        #               )
        #)

        #def new_ic_factor(self):
        #    from pychron.processing.tasks.detector_calibration.intercalibration_factor_editor import IntercalibrationFactorEditor
        #    editor = IntercalibrationFactorEditor(name='ICFactor {:03n}'.format(self.ic_factor_editor_count),
        #                                          processor=self.manager
        #                                          )
        #    self._open_editor(editor)
        #    self.ic_factor_editor_count += 1
        #
        #    selector = self.manager.db.selector
        #    self.unknowns_pane.items = selector.records[156:159]
        #    self.references_pane.items = selector.records[150:155]

#============= EOF =============================================
