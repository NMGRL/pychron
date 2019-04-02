# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
import os

from traits.api import List, Any, Bool, Event, Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.envisage.browser.adapters import InterpretedAgeAdapter


def sort_items(ans):
    return sorted(ans, key=lambda x: x.timestampf)


class InterpretedAgeTable(ColumnSorterMixin):
    interpreted_ages = List
    ointerpreted_ages = List
    selected = Any
    dclicked = Any

    context_menu_event = Event

    no_update = False
    scroll_to_row = Event
    refresh_needed = Event
    tabular_adapter = Instance(InterpretedAgeAdapter)
    append_replace_enabled = Bool(True)

    dvc = Instance('pychron.dvc.dvc.DVC')

    def set_interpreted_ages(self, ias):
        self.interpreted_ages = self.ointerpreted_ages = ias

    def delete(self):
        if self.selected:
            def key(s):
                return os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(s.path))))

            dvc = self.dvc
            for repo, records in groupby_key(self.selected, key):
                ps = []
                ns = []
                for r in records:
                    if os.path.isfile(r.path):
                        os.remove(r.path)
                        ps.append(r.path)
                        ns.append(r.name)
                        self.interpreted_ages.remove(r)

                if dvc.repository_add_paths(repo, ps):
                    dvc.repository_commit(repo, 'Removed interpreted ages {}'.format(','.join(ns)))

    # handlers
    def _interpreted_ages_items_changed(self, old, new):
        if self.sort_suppress:
            return

        if new.removed:
            for ai in new.removed:
                self.ointerpreted_ages.remove(ai)

    def _tabular_adapter_default(self):
        # adapter = AnalysisAdapter()
        # self.table_configurer.adapter = adapter
        # self.table_configurer.load()
        adapter = InterpretedAgeAdapter()
        return adapter

# ============= EOF =============================================
