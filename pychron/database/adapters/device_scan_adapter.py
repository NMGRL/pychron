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
# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = "qt4"
#============= enthought library imports =======================
#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.database.core.database_adapter import PathDatabaseAdapter
from pychron.database.selectors.device_scan_selector import DeviceScanSelector
from pychron.database.orms.hardware_orm import ScanTable, DeviceTable, \
    ScanPathTable
# from pychron.database.core.functions import delete_one

class DeviceScanAdapter(PathDatabaseAdapter):
    test_func = None
    selector_klass = DeviceScanSelector
    path_table = ScanPathTable
#==============================================================================
#    getters
#==============================================================================

    def get_device(self, value):
        return self._retrieve_item(DeviceTable, value)

    def get_scan(self, value):
        return self._retrieve_item(DeviceTable, value, key='id')

    def get_devices(self, **kw):
        return self._retrieve_items(DeviceTable, **kw)

    def get_scans(self, **kw):
        return self._retrieve_items(ScanTable, **kw)
#=============================================================================
#   adder
#=============================================================================
    def add_scan(self, device, **kw):
        b = ScanTable(**kw)
        device = self.get_device(device)
        if device:
            device.scans.append(b)

        return b
#
    def add_device(self, name, unique=True, **kw):
        c = DeviceTable(name=name, **kw)
        return self._add_unique(c, 'name', name)


if __name__ == '__main__':

    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup('dvs')

    from pychron.paths import paths
    db = DeviceScanAdapter(name=paths.device_scan_db,
                            kind='sqlite')
    db.connect()

    dbs = DeviceScanSelector(_db=db)
    dbs._execute_query()

    dbs.configure_traits()



#============= EOF =============================================
