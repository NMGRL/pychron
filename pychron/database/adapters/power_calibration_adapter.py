# ===============================================================================
# Copyright 2011 Jake Ross
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
from pychron.database.core.database_adapter import PathDatabaseAdapter
from pychron.database.orms.power_calibration_orm import PowerCalibrationTable, \
    PowerCalibrationPathTable
from pychron.database.selectors.power_calibration_selector import PowerCalibrationSelector


class PowerCalibrationAdapter(PathDatabaseAdapter):
    test_func = None
    selector_klass = PowerCalibrationSelector
    path_table = PowerCalibrationPathTable
# ==============================================================================
#    getters
# ==============================================================================

    def get_calibration_records(self, **kw):
        return self._get_items(PowerCalibrationTable, globals(), **kw)
# =============================================================================
#   adder
# =============================================================================
    def add_calibration_record(self, **kw):
        b = self._add_timestamped_item(PowerCalibrationTable, **kw)
        return b


if __name__ == '__main__':
#    db = PowerAdapter(name='co2laserdb',
#                            password='Argon')
    from pychron.paths import paths
    db = PowerCalibrationAdapter(name=paths.co2laser_db,
                            kind='sqlite')
    db.connect()

    dbs = PowerCalibrationSelector(_db=db)
    dbs.load_recent()
    dbs.configure_traits()
# ============= EOF =============================================
