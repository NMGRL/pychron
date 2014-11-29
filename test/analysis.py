# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
import unittest
# ============= local library imports  ==========================
from test.database import isotope_manager_factory
from pychron.core.codetools.simple_timeit import timethis


class AnalysisTest(unittest.TestCase):
    def setUp(self):
        self.manager = isotope_manager_factory()
        self.manager.db.connect()

    def testMakeAnalysis(self):
    #         ai = self.manager.db.get_analyses(18)
        ln = self.manager.db.get_labnumber('61311')

        aa = timethis(self.manager.make_analyses, args=(ln.analyses,))
        timethis(self.manager.load_analyses, args=(aa,),
                 kwargs={'open_progress': False})
        na = aa[0]
        #         timethis(na.load_isotopes)
        self.assertEqual(na.labnumber, '61311')


# ============= EOF =============================================
