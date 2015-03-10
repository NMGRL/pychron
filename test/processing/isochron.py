from pychron.core.ui import set_toolkit
from pychron.processing.argon_calculations import isochron_regressor

set_toolkit('qt4')
from pychron.core.regression.new_york_regressor import ReedYorkRegressor

__author__ = 'ross'

import unittest

from test.processing.standard_data import pearson


class IsochronTestCase(unittest.TestCase):
    def setUp(self):
        xs, ys, wxs, wys = pearson()

        exs = wxs ** -0.5
        eys = wys ** -0.5

        self.reg = ReedYorkRegressor(xs=xs, ys=ys,
                                     xserr=exs,
                                     yserr=eys)
        self.reg.calculate()

    def test_slope(self):
        exp = pearson('reed')
        self.assertAlmostEqual(self.reg.slope, exp['slope'], 4)

    def test_y_intercept(self):
        expected = pearson('reed')
        self.assertAlmostEqual(self.reg.intercept, expected['intercept'], 4)

    def test_x_intercept(self):
        pass
        #self.assertEqual(True, False)

    def test_age(self):
        pass

    def test_mswd(self):
        expected = pearson('reed')
        self.assertAlmostEqual(self.reg.mswd, expected['mswd'], 4)


class MassSpecPychronInverseIsochron(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.age = 10.3
        p='../data/isochron_data'
        p = '../data/isochron_data'
        cls.j=7.764e-4
        cls.jerr=4.9e-7

        cls.R=1/0.155
        cls.Rerr=12
        with open(p, 'r') as rfile:
            lines = rfile.read().split('\r')
            header = lines[0].split('\t')
            xidx = header.index('X')
            xeidx = header.index('X Er')
            yidx = header.index('Y')
            yeidx = header.index('Y Er')
            xs, ys, xes, yes = [], [], [], []
            for l in lines[7:]:
                l = l.split('\t')
                # print l
                try:
                    xs.append(float(l[xidx]))
                    xes.append(float(l[xeidx]))
                    ys.append(float(l[yidx]))
                    yes.append(float(l[yeidx]))
                except (IndexError, ValueError, TypeError):
                    break
            cls.xs,cls.ys,cls.xes,cls.yes=xs,ys,xes,yes

    # def test_R(self):

        # R=calculate_isochron2(self.xs,self.xes, self.ys, self.yes)
        # self.assertAlmostEqual(self.R, R.nominal_value, 3)
        # print R.std_dev
        # self.assertAlmostEqual(self.Rerr, R.std_dev, 3)

    # def test_age(self):
    #     R = calculate_isochron2(self.xs, self.xes, self.ys, self.yes)
    #     a=age_equation(self.j, R)
    #     self.assertAlmostEqual(a.std_dev, 0.12)

    def test_regs(self):
        reg=isochron_regressor(self.xs, self.xes, self.ys, self.yes,)
        nyreg=isochron_regressor(self.xs, self.xes, self.ys, self.yes, reg='newyork')
        self.assertEqual(reg.predict(0), nyreg.predict(0))


    def test_yint(self):
        nyreg=isochron_regressor(self.xs, self.xes, self.ys, self.yes, reg='newyork')
        v=nyreg.predict(0)
        self.assertAlmostEqual(v,3.39467e-3)

    def test_yint_err(self):
        reg = isochron_regressor(self.xs, self.xes, self.ys, self.yes)
        nyreg = isochron_regressor(self.xs, self.xes, self.ys, self.yes, reg='newyork')

        v = reg.get_intercept_error()
        nv = nyreg.get_intercept_error()

        self.assertAlmostEqual(v, nv)
        self.assertAlmostEqual(v, 2.75395e-5)





if __name__ == '__main__':
    unittest.main()
    # p = '../data/isochron_data'
    # with open(p, 'r') as rfile:
    #     lines = fp.read().split('\r')
    #     header = lines[0].split('\t')
    #     xidx = header.index('X')
    #     xeidx = header.index('X Er')
    #     yidx = header.index('Y')
    #     yeidx = header.index('Y Er')
    #     xs, ys, xes, yes = [], [], [], []
    #     for l in lines[7:]:
    #         l = l.split('\t')
    #         print l
    #         try:
    #             xs.append(float(l[xidx]))
    #             xes.append(float(l[xeidx]))
    #             ys.append(float(l[yidx]))
    #             yes.append(float(l[yeidx]))
    #         except (IndexError, ValueError, TypeError):
    #             break
    #     print header, xidx
    #     print xs