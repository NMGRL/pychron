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
from pychron.processing.export.export_manager import ExportManager

# from pychron.processing.export.exporter import MassSpecExporter
from pychron.paths import paths

paths.build('_dev')
from pychron.core.helpers.logger_setup import logging_setup
logging_setup('foo')

class DataSet(HasTraits):
    pass


class PychronDataSet(DataSet):
    manager = Instance(IsotopeDatabaseManager)

    def _manager_default(self):
        return IsotopeDatabaseManager(connect=False, bind=False)

    def connect(self, d):
        connection = d.get('connection')
        db=self.manager.db
        db.name = connection.get('name', 'pychron_dataset')
        db.host = connection.get('host', 'localhost')
        db.username = connection.get('username', 'root')
        db.password = connection.get('password', 'Argon')
        db.kind = connection.get('kind', 'mysql')

        db.connect(test=False, force=True)

class MassSpecDataSet(DataSet):
    manager = Instance(ExportManager)

    def _manager_default(self):
        m = ExportManager()
        return m

    def connect(self, d):
        connection = d.get('connection')

        db=self.manager.exporter.importer.db
        db.name=connection.get('name', 'massspec_dataset')
        db.host = connection.get('host', 'localhost')
        db.username = connection.get('username', 'root')
        db.password = connection.get('password', 'Argon')
        db.connect(test=False, force=True)

    def get_session(self):
        return self.manager.exporter.importer.db.get_session()


class DataSetGenerator(HasTraits):
    # dest=Instance(IsotopeDatabaseManager)

    """
        refactor export task. add a exportmanager and then use it here
    """
    source = Instance(IsotopeDatabaseManager)

    def _source_default(self):
        r = IsotopeDatabaseManager(connect=False, bind=False)
        r.db.trait_set(kind='mysql',
                       host='localhost',
                       username='root',
                       password='Argon',
                       name='pychrondata_dev')
        r.db.connect()
        return r

    def generate_from_file(self):
        p = os.path.join(paths.data_dir, 'dataset.yaml')

        with open(p, 'r') as fp:
            yd = yaml.load(fp)
            print yd

        pdataset = yd.get('pychron')
        if pdataset:
            self._generate_pychron_dataset(yd, pdataset)

        mdataset = yd.get('massspec')
        if mdataset:
            self._generate_massspec_dataset(yd,mdataset)

    def _generate_massspec_dataset(self, yd, d):
        dest=MassSpecDataSet()
        dest.manager.manager=self.source
        dest.connect(d)
        if d.get('build_db'):
            sess=dest.get_session()
            self._make_blank_massspec_database(sess)
            return

        db=self.source.db
        with db.session_ctx():
            rids = self._assemble_runids(yd)
            ans = [db.get_unique_analysis(*r) for r in rids]
            ans=self.source.make_analyses(ans, unpack=True)
            dest.manager.export(ans)

    def _generate_pychron_dataset(self, yd, d):
        dest = PychronDataSet()

        dest.connect(d)
        db = dest.manager.db
        with db.session_ctx() as sess:
            if d.get('build_db'):
                self._make_blank_pychron_database(sess)
                return
            rids = self._assemble_runids(yd)
            self._transfer_pychron_analyses(rids, dest)


    def _transfer_pychron_analyses(self, rids, dest):
        bridge = DatabaseBridge(source=self.source.db,
                                dest=dest.manager.db)

        db = self.source.db
        with db.session_ctx() as sess:
            ans = [db.get_unique_analysis(*r) for r in rids]
            bridge.add_analyses(ans)

    def _assemble_runids(self, d):
        rids = d['runids']
        return [strip_runid(r) for r in rids]

    def _make_blank_pychron_database(self, sess):
        p = os.path.join(os.path.dirname(__file__), 'pychron_dataset.sql')
        with open(p, 'r') as fp:
            sql = fp.read()
            sess.execute(sql)

    def _make_blank_massspec_database(self, sess):
        p = os.path.join(os.path.dirname(__file__), 'massspec_dataset.sql')
        with open(p, 'r') as fp:
            sql = fp.read()
            sess.execute(sql)


if __name__ == '__main__':
    g = DataSetGenerator()
    g.generate_from_file()
    g.configure_traits()
#============= EOF =============================================

