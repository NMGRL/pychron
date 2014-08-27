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
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.spectrometer.thermo.spectrometer import Spectrometer

class MagnetTest(unittest.TestCase):
    def setUp(self):
        spec = Spectrometer()
        spec.load()
        self.spec = spec

    def testMassToDac(self):
        mass = 39.962
        dac = self.spec.magnet.map_mass_to_dac(mass)
        self.assertEqual(dac, 6.0878436559224873)


    def testDacToMass(self):
#         mass = 39.962
        dac = 6.0878436559224873
        mass = self.spec.magnet.map_dac_to_mass(dac)
        self.assertEqual(mass, 39.962)

#============= EOF =============================================
