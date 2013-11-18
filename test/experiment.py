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
import os

from pychron.experiment.experimentor import Experimentor
from test.database import isotope_manager_factory
from pychron.experiment.tasks.experiment_editor import ExperimentEditor
from pychron.experiment.tasks.experiment_task import ExperimentEditorTask
from pychron.database.records.isotope_record import IsotopeRecord

#============= standard library imports ========================
#============= local library imports  ==========================


class BaseExperimentTest(unittest.TestCase):
    def _load_queues(self):
        man = self.experimentor
        path = self._experiment_file
        with open(path, 'r') as fp:
            txt = fp.read()

            qtexts = self.exp_task._split_text(txt)
            qs = []
            for qi in qtexts:
                editor = ExperimentEditor(path=path)
                editor.new_queue(qi)
                qs.append(editor.queue)

                #         man.test_queues(qs)
        man.experiment_queues = qs
        man.update_info()
        man.path = path
        man.executor.reset()
        return qs

    def setUp(self):
        self.experimentor = Experimentor(connect=False,
                                         unique_executor_db=False
        )
        self.experimentor.db = db = isotope_manager_factory().db

        self._experiment_file = './data/experiment2.txt'

        self.exp_task = ExperimentEditorTask()
        self._load_queues()


class ExperimentTest2(BaseExperimentTest):
    def testAliquots(self):
        queue = self._load_queues()[0]
        #         aqs = (46, 46, 47, 47)
        aqs = (46, 46, 47, 46, 46)
        aqs = (1, 46, 46, 47, 46, 46, 2)
        aqs = (1, 46, 46, 45, 46, 46, 2)
        for i, (aq, an) in enumerate(zip(aqs, queue.automated_runs)):
            print i, an.labnumber, an.aliquot, aq, 'aaa'
            self.assertEqual(an.aliquot, aq)

    def testSteps(self):
        queue = self._load_queues()[0]
        #         sts = ('A', 'B', '', 'A', 'B', '', '', '', '')
        sts = ('A', 'B', 'A', 'C', 'D')
        sts = ('', 'A', 'B', 'A', 'C', 'D', '')
        sts = ('', 'A', 'B', 'E', 'C', 'D')
        for i, (st, an) in enumerate(zip(sts, queue.automated_runs)):
        #             if st in ('E', 'F'):
            print i, an.labnumber, an.step, st, an.aliquot
            self.assertEqual(an.step, st)


class ExperimentTest(BaseExperimentTest):
    def testFile(self):
        p = self._experiment_file
        self.assertTrue(os.path.isfile(p))

    def testOpen(self):
        qs = self._load_queues()
        self.assertEqual(len(qs), 1)

    def testNRuns(self):
        n = 11
        queue = self._load_queues()[0]
        self.assertEqual(len(queue.automated_runs), n)

    def testAliquots(self):
        queue = self._load_queues()[0]
        #         aqs = (31, 31, 2, 32, 32, 200, 201, 3, 40, 41)
        #         aqs = (46, 46, 2, 47, 47, 45, 45, 3, 40, 41)
        aqs = (46, 46, 2, 47, 47, 46, 46, 40, 41, 45, 45, 3, 40, 41)
        for aq, an in zip(aqs, queue.automated_runs):
            self.assertEqual(an.aliquot, aq)

    def testSteps(self):
        queue = self._load_queues()[0]
        #         sts = ('A', 'B', '', 'A', 'B', '', '', '', '')
        sts = ('A', 'B', '', 'A', 'B', 'C', 'D', '', '', 'E', 'F',
               '', '', '', 'C', 'D')
        for i, (st, an) in enumerate(zip(sts, queue.automated_runs)):
        #             if st in ('E', 'F'):
            print i, an.labnumber, an.step, st, an.aliquot
            self.assertEqual(an.step, st)

    @unittest.skip('foo')
    def testSample(self):
        queue = self._load_queues()[0]
        samples = ('NM-779', 'NM-779', '', 'NM-779', 'NM-779', 'NM-779',
                   'NM-779', '', 'NM-791', 'NM-791'
        )
        for sample, an in zip(samples, queue.automated_runs):
            self.assertEqual(an.sample, sample)

    @unittest.skip('foo')
    def testIrradation(self):
        queue = self._load_queues()[0]
        irrads = ('NM-251H', 'NM-251H', '', 'NM-251H', 'NM-251H', 'NM-251H',
                  'NM-251H', '', 'NM-251H', 'NM-251H')
        for irrad, an in zip(irrads, queue.automated_runs):
            self.assertEqual(an.irradiation, irrad)


class ExecutorTest(BaseExperimentTest):
    def testPreviousBlank(self):
        exp = self.experimentor
        ext = exp.executor
        ext.experiment_queue = exp.experiment_queues[0]
        result = ext._get_preceeding_blank_or_background(inform=False)
        self.assertIsInstance(result, IsotopeRecord)

    def testExecutorHumanError(self):
        exp = self.experimentor
        ext = exp.executor
        ext.experiment_queue = exp.experiment_queues[0]
        self.assertTrue(ext._check_for_human_errors())

    def testPreExecuteCheck(self):
        exp = self.experimentor
        ext = exp.executor
        ext.experiment_queue = exp.experiment_queues[0]

        ext._pre_execute_check(inform=False)


class HumanErrorCheckerTest(BaseExperimentTest):
    def setUp(self):
        super(HumanErrorCheckerTest, self).setUp()

        from pychron.experiment.utilities.human_error_checker import HumanErrorChecker

        hec = HumanErrorChecker()
        self.hec = hec

    def testNoLabnumber(self):
        err = self._get_errors()
        self.assertTrue('-01' in err.keys())
        self.assertEqual(err['-01'], 'no labnumber')

    def testNoDuration(self):
        err = self._get_errors()
        self.assertEqual(err['61311-101'], 'no duration')

    #
    def testNoCleanup(self):
        err = self._get_errors()
        self.assertEqual(err['61311-100'], 'no cleanup')

    def testPositionNoExtract(self):
        err = self._get_errors()
        self.assertEqual(err['61311-102'], 'position but no extract value')

    def _get_errors(self):
        hec = self.hec
        exp = self.experimentor

        q = exp.experiment_queues[0]
        err = hec.check(q, test_all=True, inform=False)
        return err

        #============= EOF =============================================
