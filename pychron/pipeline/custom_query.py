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
from traits.api import HasTraits
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.dvc_orm import ProjectTbl, AnalysisTbl, SampleTbl, IrradiationPositionTbl

TABLES = {'project': ProjectTbl,
          'sample': SampleTbl}


class CustomAnalysisQuery(HasTraits):
    def execute_query(self, filters):
        q = self.session.query(AnalysisTbl)
        q = q.join(IrradiationPositionTbl)
        q = q.join(SampleTbl)
        q = q.join(ProjectTbl)
        for fi in filters:
            q = q.filter(fi)
        results = self.db._query_all(q)
        print len(results)

    def load_query(self):
        pass

    def generate_query(self, txt):
        filters = []
        for line in txt.split('\n'):
            tbl, val = map(str.strip, line.split(':'))

            if '.' in tbl:
                tbl, attr = tbl.split('.')
            else:
                tbl = tbl
                attr = 'name'

            tbl = TABLES.get(tbl)
            if tbl:
                attr = getattr(tbl, attr)

                if ',' in val:
                    f = attr.in_(val.split('.'))
                else:
                    f = attr == val
                filters.append(f)
            else:
                print 'invalid table {}'.format(tbl)

        return filters


if __name__ == '__main__':
    db = DVCDatabase(host='localhost',
                     username=os.environ.get('LOCALHOST_DB_USER'),
                     password=os.environ.get('LOCALHOST_DB_PWD'),
                     kind='mysql',
                     # echo=True,
                     name='pychrondvc_dev')
    txt = '''project.name: Irradiation-NM-274
sample: FC-2'''
    # txt = '''sample: FC-2'''
    db.connect()
    c = CustomAnalysisQuery(db=db)
    q = c.generate_query(txt)
    c.execute_query(q)

# ============= EOF =============================================
