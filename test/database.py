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
from traits.etsconfig.etsconfig import ETSConfig

ETSConfig.toolkit = 'qt4'
#============= standard library imports ========================
#============= local library imports  ==========================
import unittest
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


def isotope_manager_factory(name='isotopedb_dev'):
    man = IsotopeDatabaseManager(connect=False)
    man.db.kind = 'mysql'
    man.db.name = name
    man.db.password = 'Argon'
    man.db.username = 'root'
    man.db.host = 'localhost'
    return man


class IsotopeTestCase(unittest.TestCase):
    def setUp(self):
        self.isotope_database_manager = isotope_manager_factory()

    def testUrl(self):
        man = self.isotope_database_manager
        self.assertEqual(man.db.url,
                         'mysql+pymysql://root:Argon@localhost/isotopedb_dev?connect_timeout=3')

    def testConnection(self):
        man = self.isotope_database_manager
        result = man.db.connect()
        self.assertEqual(result, True)


#============= EOF =============================================
