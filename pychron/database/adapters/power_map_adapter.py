# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
# ============= local library imports  ==========================

from pychron.database.selectors.power_map_selector import PowerMapSelector
from pychron.database.orms.power_map_orm import PowerMapTable, PowerMapPathTable
from pychron.database.core.database_adapter import PathDatabaseAdapter
from pychron.paths import paths
from pychron.database.migrate.manage_database import manage_database


class PowerMapAdapter(PathDatabaseAdapter):
    test_func = None
    selector_klass = PowerMapSelector
    path_table = PowerMapPathTable

    def manage_database(self):
        manage_database(self.url, 'powermapdb')

# ==============================================================================
#    getters
# ==============================================================================

    def get_powermaps(self, **kw):
        return self._retrieve_items(PowerMapTable)
#        return self._get_items(PowerMapTable, globals(), **kw)

# =============================================================================
#   adder
# =============================================================================
    def add_powermap(self, **kw):
        b = PowerMapTable(**kw)
        self._add_item(b)
#        b = self._add_timestamped_item(PowerMapTable, **kw)
        return b

if __name__ == '__main__':
    paths.build('_diode')
    db = PowerMapAdapter(name=paths.powermap_db,
                         kind='sqlite')
    db.connect()

    dbs = PowerMapSelector(db=db)
    dbs.load_recent()
    dbs.configure_traits()


# ============= EOF =============================================
