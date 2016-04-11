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
from traits.api import Str, Event
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================

from pychron.database.core.database_selector import DatabaseSelector
from pychron.database.core.base_db_result import RIDDBResult
from pychron.mass_spec.database.massspec_orm import SampleTable


class MassSpecDBResult(RIDDBResult):
    rid = Str
    sample = Str

    def _set_metadata(self, dbr):
        #        self.rid = dbr.RID
        self.sample = dbr.Sample


class MassSpecDBResultsAdapter(TabularAdapter):
    columns = [
        #               ('RunID', 'rid'),
        ('Sample', 'sample'),
        # ('ID', '_id'),
        # ('Date', 'RunDateTime'),
        # ('Time', 'runtime')
    ]


# def get_bg_color(self, obj, trait, row, col):
#        print obj, trait, row, col
#        o = getattr(obj, trait)[row]

#        if 'group_marker' in o.rid:
#            return 'red'
#        else:
#            return 'white'
#
#    def get_text(self, obj, tr, row, column):
#
#        o = getattr(obj, tr)[row]
#        if 'group_marker' in o.rid:
#            return '----------'
#        else:
#            return getattr(o, self.columns[column][1])
#            return o

class MassSpecSelector(DatabaseSelector):
    date_str = 'RunDateTime'
    tabular_adapter = MassSpecDBResultsAdapter
    #    query_table = AnalysesTable
    query_table = SampleTable

    record_klass = MassSpecDBResult
    add_selection_changed = Event
    orm_path = 'pychron.database.orms.massspec_orm'
    open_button_label = 'Add'

    def _get_selector_records(self, **kw):
        return self._db.get_samples(**kw)

    def _open_button_fired(self):
        self.add_selection_changed = True

    def load_recent(self):
        self._execute_query(
            param='SampleTable.Sample',
            #                            param='AnalysesTable.RID',
            comp='=',
            criteria='J045'
        )

# def _get__parameters(self):
#        return ['AnalysesTable.RID',
#                'AnalysesTable.RunDateTime',
#                ]
#
#    def _search_(self):
#        db = self._db
#        if db is not None:
#            tablename, param = self.parameter.split('.')
#
#            c = self._convert_comparator(self.comparator)
#            results = db.get_results(tablename,
#                                 **{param:(c, self.criteria)}
#                                 )
#            for i, r in enumerate(results):
#                r = MassSpecDBResult(_db_result=r,
#                                     rid=r.RID,
# #                                     ridt=i
#                                     )
#                self.results.append(r)


# if __name__ == '__main__':
#    from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
#    m = MassSpecSelector(parameter='AnalysesTable.RID',
#                         criteria='21351-01')
#    m.load_recent()
#    m._db = db = MassSpecDatabaseAdapter(name='massspecdata_local')
#    db.connect()
#    m.configure_traits()
# ============= EOF =============================================
