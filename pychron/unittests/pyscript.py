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
import unittest
import time
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript
from pychron.pyscripts.measurement_pyscript import MeasurementPyScript
#============= standard library imports ========================
#============= local library imports  ==========================
class PyscriptDurationTest(unittest.TestCase):
    def setUp(self):
        self._script = MeasurementPyScript()

    def testDuration(self):
        self._script.root = './data'
        self._script.name = 'measurement_script.py'
        self._script.bootstrap()

        self._script.test()
        etd = self._script.get_estimated_duration()
        mc = 4
        bs = 2
        eq = 2
        st = 4
        td = mc + bs + eq + st
        self.assertEqual(etd, td)

class PyscriptMeasurementTest(unittest.TestCase):
    def setUp(self):
        from pychron.pyscripts.parameter_editor import MeasurementParameterEditor
        self.editor = MeasurementParameterEditor()

    @classmethod
    def setUpClass(cls):
        p = './data/measurement_script.py'
        cls.txt = open(p).read()

    def testExtractFits(self):
        editor = self.editor
        editor.parse(self.txt)

        afit = editor.fit_blocks[0]

        self.assertEqual(afit, (None, ('linear', 'linear')))

#         self.assertEqual(afit, ((0, 5), ('linear', 'linear')))
#         afit = editor.fit_blocks[1]
#         self.assertEqual(afit, ((5, None), ('linear', 'parabolic')))


class RampTest(unittest.TestCase):
    def testRamp(self):
        ps = ExtractionPyScript()
        ps.setup_context(extract_device='a')
#         rm = Ramp()
        r = ps.ramp(start=0, end=10, duration=10, period=0.5)
#         r = rm.ramp(start=0, end=10, rate=2)
        self.assertGreater(r, 10)


#============= EOF =============================================
