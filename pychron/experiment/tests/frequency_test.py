import unittest

from pychron.experiment.utilities.frequency_generator import frequency_index_gen


class Run(object):
    analysis_type = 'unknown'


class FrequencyTestCase(unittest.TestCase):
    def setUp(self):
        self.runs = [Run() for i in range(10)]

    def test_before(self):
        runs = self.runs
        for i in reversed(list(frequency_index_gen(runs, 2, ('unknown', ), True, False))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)

        atypes = [ri.analysis_type for ri in runs]
        self.assertListEqual(atypes, ['blank', 'unknown', 'unknown',
                                      'blank', 'unknown', 'unknown',
                                      'blank', 'unknown', 'unknown',
                                      'blank', 'unknown', 'unknown',
                                      'blank', 'unknown', 'unknown', ])

    def test_after(self):
        runs = self.runs
        for i in reversed(list(frequency_index_gen(runs, 2, ('unknown', ), False, True))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)

        atypes = [ri.analysis_type for ri in runs]
        self.assertListEqual(atypes, ['unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank', ])

    def test_before_and_after(self):
        runs = self.runs
        for i in reversed(list(frequency_index_gen(runs, 2, ('unknown', ), True, True))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)

        atypes = [ri.analysis_type for ri in runs]
        self.assertListEqual(atypes, ['blank', 'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank', ])

    def test_not_before_or_after(self):
        runs = self.runs
        for i in reversed(list(frequency_index_gen(runs, 2, ('unknown', ), False, False))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)

        atypes = [ri.analysis_type for ri in runs]
        self.assertListEqual(atypes, ['unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown'])

    def test_not_before_or_after3(self):
        runs = self.runs
        for i in reversed(list(frequency_index_gen(runs, 3, ('unknown', ), False, False))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)

        atypes = [ri.analysis_type for ri in runs]
        self.assertListEqual(atypes, ['unknown', 'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'unknown', 'blank',
                                      'unknown'])

    def test_after_subset1(self):
        runs = self.runs

        for i in reversed(list(frequency_index_gen(runs[:7], 3, ('unknown', ), False, False))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)

        atypes = [ri.analysis_type for ri in runs]
        print atypes
        self.assertListEqual(atypes, ['unknown', 'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'unknown',
                                      'unknown'])

    def test_after_subset2(self):
        runs = self.runs
        sidx = 3
        for i in reversed(list(frequency_index_gen(runs[sidx:], 3, ('unknown', ), False, True, sidx=sidx))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)
        print list(frequency_index_gen(runs[sidx:], 3, ('unknown', ), False, True, sidx=sidx))
        atypes = [ri.analysis_type for ri in runs]
        print atypes
        self.assertListEqual(atypes, ['unknown', 'unknown', 'unknown',
                                      'unknown', 'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'unknown', 'blank',
                                      'unknown'])

    def test_after_subset3(self):
        runs = self.runs
        sidx = 3
        for i in reversed(list(frequency_index_gen(runs[sidx:], 3, ('unknown', ), False, False, sidx=sidx))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)

        atypes = [ri.analysis_type for ri in runs]
        self.assertListEqual(atypes, ['unknown', 'unknown', 'unknown',
                                      'unknown', 'unknown', 'unknown', 'blank',
                                      'unknown', 'unknown', 'unknown',
                                      'unknown'])


if __name__ == '__main__':
    unittest.main()