# ===============================================================================
# Copyright 2014 Jake Ross
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
import csv
from itertools import groupby
import os

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path
from pychron.loggable import Loggable
from pychron.paths import paths


class TASWriter(Loggable):
    def write(self, db, ias):
        data = self._assemble_data(db, ias)

        root = os.path.join(paths.dissertation, 'data', 'minnabluff', 'interpreted_ages')
        p, _ = unique_path(root, 'tas.csv')

        with open(p, 'w') as fp:
            writer = csv.writer(fp)

            header = ['sample', 'sio2', 'total_alk', 'age']
            writer.writerow(header)
            for b, rs in groupby(data, key=lambda x: int(x[-1])):
                writer.writerows(rs)
                writer.writerow([])

    def _assemble_data(self, db, ias):

        with db.session_ctx():
            data = []
            for ia in ias:
                ln = db.get_labnumber(ia.identifier)
                dbsample = ln.sample
                # dbsample = db.get_sample(ia.sample, project='Minna Bluff')

                sio2 = dbsample.sio2
                n = dbsample.na2o
                k = dbsample.k2o
                if sio2:
                    total_alk = n + k
                    d = [ia.sample, sio2, total_alk, ia.age]
                    data.append(d)

            data = sorted(data, key=lambda x: x[-1], reverse=True)

            return data

# ============= EOF =============================================

