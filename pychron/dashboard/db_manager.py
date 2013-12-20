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
from datetime import datetime

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.adapters.dashboard_adapter import DashboardAdapter
from pychron.database.isotope_database_manager import BaseIsotopeDatabaseManager


class DashboardDBManager(BaseIsotopeDatabaseManager):
    _db_klass=DashboardAdapter

    def start(self):
        db=self.db
        with db.session_ctx():
            db.add_time_table(start=datetime.now())

    def stop(self):
        db=self.db
        with db.session_ctx():
            tt=db.get_last_time_table()
            tt.end=datetime.now()

    def publish_device(self, new):
        db = self.db
        with db.session_ctx():
            tt = db.get_last_time_table()

            for dev in tt.devices:
                if dev.name==new.name:
                    nb, fmt=new.new_scan_blob(dev.scan_blob)
                    dev.scan_blob=nb
                    dev.scan_fmt=fmt
                    break
            else:
                db.add_device(new.name)

            tt.end=datetime.now()



#============= EOF =============================================

