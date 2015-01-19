import unittest

from pychron.experiment.utilities.frequency_generator import frequency_index_gen, parse_frequency_template, \
    validate_frequency_template


class FrequencyTemplateTestCase(unittest.TestCase):
    def test_parse1(self):
        self._test_parse('s', (True, False, False, None))

    def test_parse2(self):
        self._test_parse('s,e', (True, True, False, None))

    def test_parse3(self):
        self._test_parse('s,3,4,e', (True, True, False, [3, 4]))

    def test_parse4(self):
        self._test_parse('s,E', (True, True, True, None))

    def _test_parse(self, v, args):
        pargs = parse_frequency_template(v)
        self.assertTupleEqual(args, pargs)

    def test_pass_validate1(self):
        self._test_pass('s')

    def test_pass_validate2(self):
        self._test_pass('s,e')

    def test_pass_validate3(self):
        self._test_pass('s,3,e')

    def test_pass_validate4(self):
        self._test_pass('s,3,4,e')

    def test_pass_validate5(self):
        self._test_pass('3')

    def test_pass_validate6(self):
        self._test_pass('3,4')

    def test_pass_validate7(self):
        self._test_pass('3,4,e')

    def test_pass_validate8(self):
        self._test_pass('e')

    def test_pass_validate9(self):
        self._test_pass('s,E')

    def test_pass_validate10(self):
        self._test_pass('s,3,E')

    def test_fail_validate1(self):
        self._test_fail('s,')

    def test_fail_validate2(self):
        self._test_fail('s,x')

    def test_fail_validate3(self):
        self._test_fail('s,3e')

    def test_fail_validate4(self):
        self._test_fail('s,3e,4')

    def test_fail_validate5(self):
        self._test_fail('3e')

    def test_fail_validate6(self):
        self._test_fail('3,')

    def test_fail_validate7(self):
        self._test_fail('3,4,')

    def test_fail_validate8(self):
        self._test_fail('e,')

    def test_fail_validate9(self):
        self._test_fail(',e')

    def _test_pass(self, v):
        self.assertTrue(validate_frequency_template(v))

    def _test_fail(self, v):
        self.assertIsNone(validate_frequency_template(v))

    def test_template_start(self):
        self._test_template('s', ['blank', 'unknown', 'unknown', 'unknown'])

    def test_template_end(self):
        self._test_template('e', ['unknown', 'unknown', 'unknown', 'blank'])

    def test_template_start_end(self):
        self._test_template('s,e', ['blank', 'unknown', 'unknown', 'unknown', 'blank'])

    def test_template_start_idx(self):
        self._test_template('s,2', ['blank', 'unknown', 'unknown', 'blank', 'unknown'])

    def test_template_start_end_idx(self):
        self._test_template('s,2,e', ['blank', 'unknown', 'unknown', 'blank', 'unknown', 'blank'])

    def test_template_start_idx2(self):
        self._test_template('s,2', ['blank', 'unknown', 'unknown', 'blank', 'unknown',
                                    'blank', 'unknown', 'unknown', 'blank', 'unknown'],
                            runs=self._get_runs())

    def test_template_start_end_idx2(self):
        self._test_template('s,2,e', ['blank', 'unknown', 'unknown', 'blank', 'unknown', 'blank',
                                      'blank', 'unknown', 'unknown', 'blank', 'unknown', 'blank'],
                            runs=self._get_runs())

    def test_template_start_idx3(self):
        self._test_template('s,2,10', ['blank', 'unknown', 'unknown', 'blank', 'unknown','blank'])

    def test_template_start2(self):
        self._test_template('s', ['blank', 'unknown', 'unknown', 'unknown',
                                  'blank', 'unknown', 'unknown', 'unknown', ],
                            runs=self._get_runs())

    def test_template_start_end2(self):
        self._test_template('s,e', ['blank', 'unknown', 'unknown', 'unknown', 'blank',
                                    'blank', 'unknown', 'unknown', 'unknown', 'blank'],
                            runs=self._get_runs())

    def test_template_end2(self):
        self._test_template('e', ['unknown', 'unknown', 'unknown', 'blank',
                                  'unknown', 'unknown', 'unknown', 'blank'],
                            runs=self._get_runs())

    def test_template_compress(self):
        self._test_template('e', ['unknown', 'unknown', 'unknown', 'blank', 'air',
                                  'unknown', 'unknown', 'unknown', 'blank'],
                            runs=self._get_runs2())

    def test_template_start_end_ex(self):
        self._test_template('s,E', ['blank', 'unknown', 'unknown', 'unknown',
                                    'blank', 'unknown', 'unknown', 'unknown', 'blank'],
                            runs=self._get_runs())

    def test_template_start_end_ex2(self):
        self._test_template('s,E', ['blank', 'unknown', 'unknown', 'unknown', 'blank', 'air',
                                    'blank', 'unknown', 'unknown', 'unknown', 'blank'],
                            runs=self._get_runs2())

    def test_template_start_end_ex3(self):
        self._test_template('s,E', ['blank', 'unknown', 'unknown', 'unknown', 'blank', 'air',
                                    'blank', 'unknown', 'unknown', 'unknown', 'blank', 'air',
                                    'blank', 'unknown', 'unknown', 'unknown', 'blank'],
                            runs=self._get_runs3())

    def test_template_start_end2(self):
        self._test_template('s,e', ['blank', 'unknown', 'unknown', 'unknown', 'blank',
                                    'blank', 'unknown', 'unknown', 'unknown', 'blank',
                                    'blank', 'unknown', 'unknown', 'unknown', 'blank'],
                            runs=self._get_runs4())

    def test_template_start_idx3(self):
        runs = [Run() for i in range(4)]
        runs[1].skip=True
        self._test_template('s,2',
                            ['blank', 'unknown', 'unknown', 'unknown', 'blank', 'unknown'],
                            runs=runs)

    def test_template_start_idx4(self):
        runs = [Run() for i in range(4)]+[Run(aliquot=1) for i in range(4)]
        runs[1].skip=True
        runs[5].skip=True
        self._test_template('s,2',
                            ['blank', 'unknown', 'unknown', 'unknown', 'blank', 'unknown',
                             'blank', 'unknown', 'unknown', 'unknown', 'blank', 'unknown'],
                            runs=runs)

    def _get_runs(self):
        return [Run() for i in range(3)] + [Run(aliquot=1) for i in range(3)]

    def _get_runs2(self):
        return [Run() for i in range(3)] + [Run(analysis_type='air')] + \
               [Run(aliquot=1) for i in range(3)]

    def _get_runs3(self):
        return [Run() for i in range(3)] + [Run(analysis_type='air')] + \
               [Run(aliquot=1) for i in range(3)]+[Run(analysis_type='air')]+\
               [Run(aliquot=2) for i in range(3)]
    def _get_runs4(self):
        return [Run() for i in range(3)] + \
               [Run(aliquot=1) for i in range(3)]+\
               [Run(aliquot=2) for i in range(3)]

    def _test_template(self, temp, exp, runs=None):
        if runs is None:
            runs = [Run() for i in range(3)]

        for i in reversed(list(frequency_index_gen(runs, temp, ('unknown', ), False, False))):
            r = Run()
            r.analysis_type = 'blank'
            runs.insert(i, r)
        atypes = [ri.analysis_type for ri in runs]
        # print exp
        # print atypes
        self.assertListEqual(atypes, exp)


class Run(object):
    analysis_type = 'unknown'
    aliquot = 0
    skip = False
    def __init__(self, aliquot=0, analysis_type='unknown'):
        self.aliquot = aliquot
        self.analysis_type = analysis_type


class FrequencyTestCase(unittest.TestCase):
    def setUp(self):
        self.runs=[Run() for i in range(10)]

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
        atypes = [ri.analysis_type for ri in runs]
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