# ===============================================================================
# Copyright 2016 Jake Ross
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
import os

# ============= standard library imports ========================
# ============= local library imports  ==========================
os.environ['MassSpecDBVersion'] = '16'
from pychron.mass_spec.database.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.mass_spec.database.massspec_orm import AnalysesTable, IsotopeTable, DetectorTable

db = MassSpecDatabaseAdapter(bind=False)
db.host =
db.name = 'massspecdata'
db.username =
db.password =
db.kind = 'mysql'
db.connect(test=False)


def fix_reference_detector(rd, aid):
    with db.session_ctx() as sess:
        q = sess.query(AnalysesTable)
        q = q.filter(AnalysesTable.AnalysisID == aid)
        record = q.one()

        q = sess.query(DetectorTable)
        q = q.join(IsotopeTable)
        q = q.join(AnalysesTable)

        q = q.filter(AnalysesTable.AnalysisID == aid)

        for r in q.all():
            if r.Label == rd:
                print 'setting refid current={}  new={}'.format(record.RefDetID, r.DetectorID)
                record.RefDetID = r.DetectorID


def fix_reference_detectors(path):
    with open(path) as rfile:
        for line in rfile:
            line = line.strip()
            if line:
                aid = int(line)
                fix_reference_detector('H2', aid)
                # break


path = '/Users/ross/Desktop/Untitled.csv'
fix_reference_detectors(path)
# ============= EOF =============================================
