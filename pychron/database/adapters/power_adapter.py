#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.core.database_adapter import PathDatabaseAdapter
from pychron.database.orms.power_orm import PowerTable, PowerPathTable
from pychron.database.selectors.power_selector import PowerSelector


class PowerAdapter(PathDatabaseAdapter):
    test_func = None
    selector_klass = PowerSelector
    path_table = PowerPathTable
#==============================================================================
#    getters
#==============================================================================

    def get_power_records(self, **kw):
        return self._get_items(PowerTable, globals(), **kw)
#=============================================================================
#   adder
#=============================================================================
    def add_power_record(self, **kw):
        b = self._add_timestamped_item(PowerTable, **kw)
        return b

if __name__ == '__main__':
#    db = PowerAdapter(name='co2laserdb',
#                            password='Argon')
    from pychron.paths import paths
    db = PowerAdapter(name=paths.co2laser_db,
                            kind='sqlite')
    db.connect()

    dbs = PowerSelector(_db=db)
    dbs.load_recent()
#    dbs._execute_query()
    dbs.configure_traits()
#    print db.get_bakeouts(join_table='ControllerTable',
#                    filter_str='ControllerTable.script="---"'
#                    )
#============= EOF =============================================
#    def get_analyses_path(self):
# #        sess = self.get_session()
# #        q = sess.query(Paths)
# #        s = q.filter_by(name='analyses')
#        q = self._get_query(Paths, name='analyses')
#        p = q.one()
#        p = p.path
#        return p
#
#    def get_intercepts(self, analysis_id):
#        q = self._get_query(Intercepts, analysis_id=analysis_id)
#        return q.all()
#
#    def get_analysis_type(self, **kw):
#        q = self._get_query(AnalysisTypes, **kw)
#        return q.one()
#
#    def get_spectrometer(self, **kw):
#        q = self._get_query(Spectrometers, **kw)
#        return q.one()
#    def add_intercepts(self, **kw):
#        o = Intercepts(**kw)
#        self._add_item(o)
#
#    def add_analysis(self, atype=None, spectype=None, **kw):
#        if atype is not None:
#            a = self.get_analysis_type(name=atype)
#            kw['type_id'] = a._id
#
#        if spectype is not None:
#            s = self.get_spectrometer(name=spectype)
#            kw['spectrometer_id'] = s._id
#
#        o = Analyses(**kw)
#        self._add_item(o)
#        return o._id
