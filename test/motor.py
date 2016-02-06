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
import unittest

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.linear_mapper import LinearMapper


class LinearMapperTest(unittest.TestCase):
    def setUp(self):
        self.mapper = LinearMapper()

        self.mapper.low_data = 2
        self.mapper.high_data = 6
        self.mapper.low_step = 0
        self.mapper.high_step = 9500

    def testMapData(self):
        m = self.mapper

        # map from steps to data
        ds = 0
        steps = m.map_data(ds)
        self.assertEqual(steps, 2)

        ds = 9500
        steps = m.map_data(ds)
        self.assertEqual(steps, 6)

    #
    def testMapSteps(self):
        # map from data to steps
        m = self.mapper

        ds = 2
        steps = m.map_steps(ds)
        self.assertEqual(steps, 0)

        ds = 6
        steps = m.map_steps(ds)
        self.assertEqual(steps, 9500)

        ds = 4
        steps = m.map_steps(ds)
        self.assertEqual(steps, 9500 / 2.)

# ============= EOF =============================================
