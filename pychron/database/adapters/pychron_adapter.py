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
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.orms.pychron_orm import Analyses, Paths, Intercepts, \
     AnalysisTypes, Spectrometers


class PychronAdapter(DatabaseAdapter):
    test_func = 'get_rids'

# ===============================================================================
#    getters
# ===============================================================================
    def get_analyses_path(self):
#        sess = self.get_session()
#        q = sess.query(Paths)
#        s = q.filter_by(name='analyses')
        q = self._get_query(Paths, name='analyses')
        p = q.one()
        p = p.path
        return p

    def get_intercepts(self, analysis_id):
        q = self._get_query(Intercepts, analysis_id=analysis_id)
        return q.all()

    def get_analysis_type(self, **kw):
        q = self._get_query(AnalysisTypes, **kw)
        return q.one()

    def get_spectrometer(self, **kw):
        q = self._get_query(Spectrometers, **kw)
        return q.one()

    def _get_query(self, klass, **clause):
        sess = self.get_session()
        q = sess.query(klass)
        q = q.filter_by(**clause)
        return q

# ==============================================================================
#   adder
# ==============================================================================
    def add_intercepts(self, **kw):
        o = Intercepts(**kw)
        self._add_item(o)

    def add_analysis(self, atype=None, spectype=None, **kw):
        if atype is not None:
            a = self.get_analysis_type(name=atype)
            kw['type_id'] = a.id

        if spectype is not None:
            s = self.get_spectrometer(name=spectype)
            kw['spectrometer_id'] = s.id

        o = Analyses(**kw)
        self._add_item(o)
        return o.id

#    def _add_item(self, obj):
#        sess = self.get_session()
#        sess.add(obj)
#        sess.commit()



#======== EOF ================================
