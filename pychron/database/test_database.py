# ===============================================================================
# Copyright 2014 Jake Ross
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
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager

class Record(object):
    analysis_type = 'unknown'

    def __init__(self, uuid):
        self.uuid = uuid


def isotope_manager_factory(name='pychrondata_dev'):
    man = IsotopeDatabaseManager(connect=False, bind=False)
    man.db.kind = 'mysql'
    man.db.name = name
    man.db.password = 'Argon'
    man.db.username = 'root'
    man.db.host = 'localhost'
    man.connect()
    return man


def get_test_analysis(uuid=None, man=None, calculate_age=True, **kw):
    if man is None:
        man=isotope_manager_factory()

    if uuid is None:
        uuid = 'f51a8ed2-5ab3-4df7-a7a9-84b3ea8a1555'

    rec=Record(uuid)
    a = man.make_analysis(rec, calculate_age=calculate_age, **kw)
    return a, man
#============= EOF =============================================



