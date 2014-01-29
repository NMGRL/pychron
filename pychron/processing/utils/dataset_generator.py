#===============================================================================
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
#===============================================================================
from pychron.core.ui import set_toolkit

set_toolkit('qt4')
#============= enthought library imports =======================
import os
from traits.api import HasTraits, Instance

#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.experiment.utilities.identifier import strip_runid
from pychron.database.offline_bridge import DatabaseBridge
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.paths import paths
paths.build('_dev')


class DataSetGenerator(HasTraits):
    dest=Instance(IsotopeDatabaseManager)
    source=Instance(IsotopeDatabaseManager)

    def _source_default(self):
        r=IsotopeDatabaseManager(connect=False, bind=False)
        r.db.trait_set(kind='mysql',
                       host='localhost',
                       username='root',
                       password='Argon',
                       name='pychrondata_dev')
        r.db.connect()
        return r

    def _dest_default(self):
        return IsotopeDatabaseManager(connect=False, bind=False)

    def generate_from_file(self):
        p = os.path.join(paths.data_dir, 'dataset.yaml')

        with open(p, 'r') as fp:
            yd = yaml.load(fp)
            print yd

        self._connect_dest(yd['connection'][0])
        # self._make_blank_database(yd['connection'][0])

        rids=self._assemble_runids(yd)
        self._transfer_analyses(rids)
        # self._transfer_irradiation(rids)
        # self._transfer_runids(rids)

    def _connect_dest(self, connection):
        db = self.dest.db
        db.name = connection.get('name', 'pychron_dataset')
        db.host = connection.get('host', 'localhost')
        db.username = connection.get('username', 'root')
        db.password = connection.get('password', 'Argon')
        db.kind = connection.get('kind', 'mysql')

        db.connect(test=False)

    def _transfer_analyses(self, rids):
        bridge=DatabaseBridge(source=self.source.db,dest=self.dest.db)

        db=self.source.db
        with db.session_ctx() as sess:
            ans=[db.get_unique_analysis(*r) for r in rids]
            bridge.add_analyses(ans)

    def _transfer_runids(self, rids):
        for identifier, aliquot, step in rids:
            print identifier, aliquot, step

    def _assemble_runids(self, d):
        rids=d['runids']
        return [strip_runid(r) for r in rids]

    def _make_blank_database(self, connection):
        with open('dataset.sql', 'r') as fp:
            sql=fp.read()

            db = self.dest.db
            with db.session_ctx() as sess:
                sess.execute(sql)


if __name__=='__main__':
    g=DataSetGenerator()
    g.generate_from_file()
    g.configure_traits()
#============= EOF =============================================

