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
from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.browser_model import BrowserModel
from pychron.envisage.browser.interpreted_age_table import InterpretedAgeTable


class InterpretedAgeBrowserModel(BrowserModel):
    interpreted_age_table = Instance(InterpretedAgeTable)
    persistence_name = 'ia_browser_options'
    selection_persistence_name = 'ia_browser_selection'

    def _selected_samples_changed_hook(self, new):
        self.interpreted_age_table.selected = []

        ias = []
        if new:
            ias = self._retrieve_interpreted_ages(new)
            # uuids = [ai.uuid for ai in self.analysis_table.analyses]
            #
            # kw = dict(limit=lim,
            #           include_invalid=not at.omit_invalid,
            #           mass_spectrometers=self._recent_mass_spectrometers,
            #           exclude_uuids=uuids,
            #           experiments=[e.name for e in self.selected_experiments] if self.selected_experiments else None)
            #
            # lp, hp = self.low_post, self.high_post
            # ans = self._retrieve_sample_analyses(new,
            #                                      low_post=lp,
            #                                      high_post=hp,
            #                                      **kw)
            #
            # self.debug('selected samples changed. loading analyses. '
            #            'low={}, high={}, limit={} n={}'.format(lp, hp, lim, len(ans)))

        # self.analysis_table.set_analyses(ans, selected_identifiers={ai.identifier for ai in new})
        self.interpreted_age_table.set_interpreted_ages(ias)

    def _retrieve_interpreted_ages(self, identifiers):
        ses = self.selected_experiments
        if not ses:
            ses = self.experiments

        idns = [idn.identifier for idn in identifiers]
        experiments = [e.name for e in ses]
        ias = self.db.find_interpreted_ages(idns, experiments)

        return ias

    def _interpreted_age_table_default(self):
        return InterpretedAgeTable()

# ============= EOF =============================================
