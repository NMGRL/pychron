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

#============= enthought library imports =======================
#============= standard library imports ========================
import unittest

from uncertainties import ufloat

from pychron.experiment.queue.experiment_queue import ExperimentQueue

#============= local library imports  ==========================

class MockRun(object):
    analysis_type = 'blank_unknown'
    Ar40 = ufloat(0, 0)

class QueueTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        p = './data/experiment.txt'
        cls.txt = open(p).read()

    def setUp(self):
        self._queue = ExperimentQueue()
        self._queue.load(self.txt)

    def testLoadActions(self):
        q = self._queue
        self.assertEqual(len(q.queue_actions), 2)

    def testActions(self):
        q = self._queue
        act = q.queue_actions[0]
        self.assertEqual(act.analysis_type, 'blank_unknown')
        self.assertEqual(act.nrepeat, 3)

        act = q.queue_actions[1]
        self.assertEqual(act.nrepeat, 1)

    def testCheckRun(self):
        q = self._queue
        act = q.queue_actions[0]
        run = MockRun()

        run.Ar40 = ufloat(100, 0)
        self.assertTrue(act.check_run(run))


        run.Ar40 = ufloat(10, 0)
        self.assertFalse(act.check_run(run))
#         self.assertEqual(len(q.queue_actions), 2)
# ============= EOF =============================================
