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
from __future__ import absolute_import

from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.browser.browser_model import BrowserModel
from pychron.envisage.browser.interpreted_age_table import InterpretedAgeTable


class InterpretedAgeBrowserModel(BrowserModel):
    table = Instance(InterpretedAgeTable)
    persistence_name = "ia_browser_options"
    selection_persistence_name = "ia_browser_selection"

    def get_interpreted_age_records(self):
        records = self.table.selected
        if not records:
            records = self.table.interpreted_ages
        return records

    def _selected_samples_changed_hook(self, new):
        self.table.selected = []

        ias = []
        if new:
            ias = self._retrieve_interpreted_ages(new)

        self.table.set_interpreted_ages(ias)

    def _retrieve_interpreted_ages(self, identifiers):
        # ses = self.selected_repositories
        # if not ses:
        #     ses = self.repositories
        ses = self.repositories
        if not ses:
            self.load_repositories()
            ses = self.repositories

        idns = [idn.identifier for idn in identifiers]
        # repos = {idn.repository_identifier for idn in identifiers}
        repos = [e.name for e in ses]
        ias = self.db.find_interpreted_ages(idns, repos)

        return ias

    def _table_default(self):
        return InterpretedAgeTable(dvc=self.dvc)


# ============= EOF =============================================
