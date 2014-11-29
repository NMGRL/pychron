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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.orms.isotope.dash import dash_TimeTable, dash_DeviceTable


class DashboardAdapter(DatabaseAdapter):
    def add_time_table(self, start):
        obj=dash_TimeTable(start=start)
        self._add_item(obj)

    def add_device(self, time_table, device_name):
        obj=dash_DeviceTable(name=device_name, time_table=time_table)
        return obj

    def get_last_time_table(self):
        return self._retrieve_first(dash_TimeTable, order_by=dash_TimeTable.start.desc())

# ============= EOF =============================================

