import unittest

from numpy import linspace

from pychron.experiment.conditional.conditional import conditional_from_dict, tokenize
from pychron.processing.arar_age import ArArAge
from pychron.processing.isotope import Isotope

DEBUGGING = False

import sys

if sys.platform == 'darwin':
    pass
    # from pychron.core.helpers.logger_setup import logging_setup
    # logging_setup('conditionals')
else:
    DEBUGGING = False


class MSpec(object):
    analysis_type = 'unknown'


class Arun(object):
    def __init__(self):
        self.isotope_group = ArArAge()
        self.spec = MSpec()

    def get_deflection(self, *args, **kw):
        return 2000

    def get_pressure(self, attr):
        return 1e-9

    def get_device_value(self, dev_name):
        return 60


class ParseConditionalsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_device(self):
        t = 'device.pneumatics<80'
        tokens = tokenize(t)
        self.assertListEqual(tokens, [('device.pneumatics<80', None)])

    def test_pressure(self):
        t = 'bone.ig.pressure<1e-7'
        tokens = tokenize(t)
        self.assertListEqual(tokens, [('bone.ig.pressure<1e-7', None)])

    def test_single(self):
        t = 'Ar40>50'
        tokens = tokenize(t)
        self.assertListEqual(tokens, [('Ar40>50', None)])

    def test_single_and(self):
        t = 'Ar40>50 and age>10'
        tokens = tokenize(t)
        self.assertListEqual(tokens, [('Ar40>50', 'and'), ('age>10', None)])

    def test_single_or(self):
        t = 'Ar40>50 or age>10'
        tokens = tokenize(t)
        self.assertListEqual(tokens, [('Ar40>50', 'or'), ('age>10', None)])

    def test_and_or(self):
        t = 'Ar40>50 and age>10 or age<0'
        tokens = tokenize(t)
        self.assertListEqual(tokens, [('Ar40>50', 'and'), ('age>10', 'or',), ('age<0', None)])

    def test_parse_deflection(self):
        t = 'CDD.deflection==2000'
        tokens = tokenize(t)
        self.assertListEqual(tokens, [('CDD.deflection==2000', None)])

    def test_not(self):
        t = 'not age<10'
        tokens = tokenize(t)
        self.assertEqual(tokens, [('not age<10', None)])


class ConditionalsTestCase(unittest.TestCase):
    def setUp(self):
        self.arun = Arun()
        xs = linspace(0, 100)
        ys = 2 * xs + 4

        ar40 = Isotope(name='Ar40', xs=xs, ys=ys)
        ar40.baseline.value = 0.25
        ar40.blank.value = 0.75

        ys = 2 * xs + 1
        ar39 = Isotope(name='Ar39', xs=xs, ys=ys)
        # ar39.baseline.value = 0.25
        # ar39.blank.value = 0.75
        self.arun.isotope_group.isotopes = {'Ar40': ar40, 'Ar39': ar39}
        self.arun.isotope_group.age = 10
        # print ar40
        # print 'bs', ar40.get_baseline_corrected_value()
        # print 'int', ar40.uvalue, ar40.baseline.uvalue

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_device(self):
        d = {'check': 'device.pneumatics<80'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Pressure(self):
        d = {'check': 'bone.ig.pressure<1e-7'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Ratio(self):
        d = {'check': 'Ar40/Ar39>1', 'attr': 'age'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_And(self):
        d = {'check': 'age>0.1 and age<100', 'attr': 'age'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_AndBetween(self):
        d = {'check': 'age>0.1 and between(Ar40,0,100)'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_OrA(self):
        d = {'check': 'age>0.1 or Ar40<100', 'attr': 'age'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_OrB(self):
        d = {'check': 'age<0.1 or Ar40<100', 'attr': 'age'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Age(self):
        d = {'check': 'age>0.1', 'attr': 'age'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_NotAge(self):
        d = {'check': 'not age<0.1', 'attr': 'age'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_NotAr40(self):
        d = {'check': 'not Ar40>100', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between1(self):
        self._test_between(0, 5)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between2(self):
        self._test_between(0, 5.)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between3(self):
        self._test_between(0, 5.0)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between4(self):
        self._test_between(0., 5)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between5(self):
        self._test_between(0., 5.)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between6(self):
        self._test_between(0., 5.0)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between7(self):
        self._test_between(0.0, 5)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between8(self):
        self._test_between(0.0, 5.)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Between9(self):
        self._test_between(0.0, 5.0)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_BetweenModifier(self):
        d = {'check': 'between(Ar40.bs,0,1)', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_MinBetween(self):
        d = {'check': 'between(min(Ar40),0,5)', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_MaxBetween(self):
        d = {'check': 'between(max(Ar40),200,205)', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_NotBetween(self):
        self.arun.isotope_group.isotopes['Ar40'].value = 10
        d = {'check': 'not between(Ar40,0,5)', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_NotSlope(self):
        d = {'check': 'not slope(Ar40)>0.1', 'attr': 'Ar40'}
        self._test(d, expected=None)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Slope(self):
        d = {'check': 'slope(Ar40)>0.1', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Min(self):
        d = {'check': 'min(Ar40)>0', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_MinWindow(self):
        d = {'check': 'min(Ar40)<170', 'attr': 'Ar40', 'window': 10}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Max(self):
        d = {'check': 'max(Ar40)>0', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Average(self):
        d = {'check': 'average(Ar40)>1', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_AverageWindow(self):
        d = {'check': 'average(Ar40)>182', 'attr': 'Ar40', 'window': 10}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Current(self):
        d = {'check': 'Ar40.cur>1', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Baseline(self):
        d = {'check': 'Ar40.bs==0.25', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_BaselineCorrected(self):
        d = {'check': 'Ar40.bs_corrected<10', 'attr': 'Ar40'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Mapper(self):
        # d = {'check': 'Ar40==-100', 'attr': 'Ar40', 'mapper': 'min(x,-1000)'}
        # self.arun.arar_age.isotopes['Ar40'].set_uvalue((10,0))
        d = {'check': 'Ar40>900', 'attr': 'Ar40', 'mapper': 'x+1000'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Inactive1(self):
        d = {'check': 'CDD.inactive', 'attr': 'CDD'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Inactive2(self):
        d = {'check': 'CDD.inactive', 'attr': 'CDD'}
        self._test(d)

    @unittest.skipIf(DEBUGGING, 'Debugging')
    def test_Deflection(self):
        d = {'check': 'CDD.deflection==2000', 'attr': 'CDD'}
        self._test(d)

    def _test_between(self, l, h):
        self.arun.isotope_group.isotopes['Ar40'].value = 3.4
        d = {'check': 'between(Ar40,{},{})'.format(l, h), 'attr': 'Ar40'}
        self._test(d)

    def _test(self, d, expected=True, kind='TerminationConditional'):
        c = conditional_from_dict(d, kind)
        ret = c.check(self.arun, ([], []), 1000)
        self.assertEqual(ret, expected)


if __name__ == '__main__':
    unittest.main()
