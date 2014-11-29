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

from pychron.processing.bayesian_modeler import BayesianModeler

# ============= standard library imports ========================
# ============= local library imports  ==========================

class BayesianTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.modeler = BayesianModeler()


    def testStratOrder(self):
        ages = [1, 2, 3, 4, 5, 6]
        self.assertTrue(self.modeler._is_valid(ages))

    def testStratOrderFail(self):
        ages = [1, 2, 3, 6, 4, 5]
        self.assertFalse(self.modeler._is_valid(ages))

# ============= EOF =============================================
