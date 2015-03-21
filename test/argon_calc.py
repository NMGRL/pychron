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
# ============= standard library imports ========================
import math
from unittest import TestCase
from ConfigParser import ConfigParser
# ============= local library imports  ==========================
from pychron.processing.argon_calculations import calculate_arar_age
from pychron.processing import constants

class AgeCalcTest(TestCase):
    def setUp(self):
        rid = '60754-10'
        config = ConfigParser()
        p = '/Users/ross/Sandbox/pychron_validation_data.cfg'
        config.read(p)

        signals = map(lambda x: map(float, x.split(',')),
                      [config.get('Signals-{}'.format(rid), k)
                        for k in ['ar40', 'ar39', 'ar38', 'ar37', 'ar36']])

        blanks = map(lambda x: map(float, x.split(',')),
                      [config.get('Blanks-{}'.format(rid), k)
                        for k in ['ar40', 'ar39', 'ar38', 'ar37', 'ar36']])

        irradinfo = map(lambda x: map(float, x.split(',')),
                       [config.get('irrad-{}'.format(rid), k) for k in ['k4039', 'k3839', 'ca3937', 'ca3837', 'ca3637', 'cl3638']])

        j = config.get('irrad-{}'.format(rid), 'j')
        j = map(lambda x: float(x), j.split(','))
        baselines = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
        backgrounds = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]

        ar37df = config.getfloat('irrad-{}'.format(rid), 'ar37df')
        t = math.log(ar37df) / (constants.lambda_37.nominal_value * 365.25)
        irradinfo.append(t)

        # load results
        r = 'results-{}'.format(rid)
        self.age = config.getfloat(r, 'age')
        self.rad4039 = config.getfloat(r, 'rad4039')
        self.ca37k39 = config.getfloat(r, 'ca37k39')


        self.age_dict = calculate_arar_age(signals, baselines, blanks, backgrounds, j, irradinfo,
                               )

    def test_age_dict(self):
        self.assertIsInstance(self.age_dict, dict)

    def test_age(self):
        ageerr = self.age_dict['age']
        age = ageerr.nominal_value / 1e6
        err = ageerr.std_dev
        self.assertAlmostEqual(age,
                         self.age,  # 28.0625,
                         places=4)

    def test_4039(self):
        ar40 = self.age_dict['rad40']
        k39 = self.age_dict['k39']

        n = ar40 / k39
        n = n.nominal_value
        self.assertAlmostEqual(n,
                         self.rad4039,
                         # 7.0039026,
                         places=5
                         )
    def test_3739(self):
        ca37 = self.age_dict['ca37']
        k39 = self.age_dict['k39']
        n = ca37 / k39
        n = n.nominal_value
        self.assertAlmostEqual(n,
                               self.ca37k39,
#                               0.0062869,
                          )
    def test_mswd(self):
        pass
    def test_intercept(self):
        pass
    def test_intercept_error(self):
        pass
    def test_plateau_age(self):
        pass
    def test_plateau_error(self):
        pass

# ============= EOF =============================================
#        self.ca37k39 = 0.0062869
#        self.age = 28.0625
#        self.rad4039 = 7.0039026
#
#        a37df = 3.80315e1
#        t = math.log(a37df) / (constants.lambda_37.nominal_value * 365.25)
#
#        signals = ((2655.294, 0.12),
#                   (377.5964, 0.046),
#                   (4.999, 0.012),
#                   (0.0853, 0.014),
#                   (0.013245, 0.00055)
#                   )
#        baselines = ((0, 0), (0, 0), (0, 0), (0, 0), (0, 0))
#        blanks = ((1.5578, 0.023),
#                  (0.0043, 0.024),
#                  (-0.0198, 0.011),
#                  (0.0228, 0.012),
#                  (0.00611, 0.00033))
#        backgrounds = ((0, 0), (0, 0), (0, 0), (0, 0), (0, 0))
#        j = (2.2408e-3, 1.7795e-6)
#        irradinfo = ((1e-2, 2e-3),
#                         (1.3e-2, 0),
#
#                         (7e-4, 2e-6),
#                         (0, 0),
#                         (2.8e-4, 2e-5),
#                         (2.5e2, 0), t)
