from numpy import linspace

from pychron.experiment.conditional.conditional import conditional_from_dict
from pychron.processing.arar_age import ArArAge
from pychron.processing.isotope import Isotope


__author__ = 'ross'

import unittest

class Arun(object):
    def __init__(self):
        self.arar_age=ArArAge()

    def get_deflection(self, *args, **kw):
        return 2000

class ConditionalsTestCase(unittest.TestCase):
    def setUp(self):
        self.arun = Arun()
        xs = linspace(0,100)
        ys = 2*xs+1

        ar40=Isotope(name='Ar40',xs=xs,ys=ys)
        ar40.baseline.value=1.23
        self.arun.arar_age.isotopes={'Ar40':ar40}

    def test_Slope(self):
        d={'check':'slope(Ar40)>0.1', 'attr':'Ar40'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_Min(self):
        d={'check':'min(Ar40)>0','attr':'Ar40'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_MinWindow(self):
        d={'check':'min(Ar40)==164.26530612244898','attr':'Ar40', 'window':10}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_Max(self):
        d={'check':'max(Ar40)>0','attr':'Ar40'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_Average(self):
        d={'check':'average(Ar40)>1','attr':'Ar40'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_AverageWindow(self):
        d={'check':'average(Ar40)>182','attr':'Ar40', 'window':10}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_Current(self):
        d={'check':'Ar40.cur>1','attr':'Ar40'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_Baseline(self):
        d={'check':'Ar40.bs==1.23','attr':'Ar40'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_BaselineCorrected(self):
        d={'check':'Ar40.bs_corrected<1','attr':'Ar40'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_Mapper(self):
        d={'check':'Ar40<-1','attr':'Ar40', 'mapper':'x-1000'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

    def test_Inactive1(self):
        d={'check':'CDD.inactive', 'attr':'CDD'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, (['H1','AX','CDD'],[]), 1000)
        self.assertIsNone(ret)

    def test_Inactive2(self):
        d={'check':'CDD.inactive', 'attr':'CDD'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, (['H1','AX'],[]), 1000)
        self.assertTrue(ret)

    def test_Deflection(self):
        d={'check':'CDD.deflection == 2000', 'attr':'CDD'}
        c=conditional_from_dict(d, 'TerminationConditional')
        ret = c.check(self.arun, ([],[]), 1000)
        self.assertTrue(ret)

if __name__ == '__main__':
    unittest.main()
