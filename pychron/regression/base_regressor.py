#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Array, List, Event, Property, cached_property
#============= standard library imports ========================
import math
from numpy import array, where
#============= local library imports  ==========================
from tinv import tinv
from pychron.pychron_constants import ALPHAS


class BaseRegressor(HasTraits):
    xs = Array
    ys = Array
    #    xs = Any
    #    ys = Any
    xserr = Array
    yserr = Array

    dirty = Event
    coefficients = Property(depends_on='dirty, xs, ys')
    coefficient_errors = Property(depends_on='coefficients, xs, ys')
    _coefficients = List
    _coefficient_errors = List
    _result = None
    fit = Property
    _fit = None

    n = Property(depends_on='dirty, xs, ys')

    def _get_n(self):
        return len(self.xs)

    def _xs_changed(self):
    #        if len(self.xs) and len(self.ys):
        self.calculate()

    def _ys_changed(self):
        self.calculate()

    def calculate(self):
        pass

    def percent_error(self, s, e):
        try:
            return abs(e / s * 100)
        except ZeroDivisionError:
            return 'Inf'

    def tostring(self, sig_figs=5, error_sig_figs=5):

        cs = self.coefficients[::-1]
        ce = self.coefficient_errors[::-1]

        coeffs = []
        s = u''
        for a, ci, ei in zip(ALPHAS, cs, ce):
            pp = '({:0.2f}%)'.format(self.percent_error(ci, ei))
            #            print pp, ci, ei, self.percent_error(ci, ei)
            fmt = '{{:0.{}e}}' if abs(ci) < math.pow(10, -sig_figs) else '{{:0.{}f}}'
            ci = fmt.format(sig_figs).format(ci)

            fmt = '{{:0.{}e}}' if abs(ei) < math.pow(10, -error_sig_figs) else '{{:0.{}f}}'
            ei = fmt.format(error_sig_figs).format(ei)

            vfmt = u'{}= {} +/- {} {}'
            coeffs.append(vfmt.format(a, ci, ei, pp))

        #        s = ', '.join([fmt.format(a, ci, pm, cei, self.percent_error(ci, cei))
        #                       for a, ci, cei in zip(ALPHAS, cs, ce)
        #                       ])
        s = u', '.join(coeffs)
        return s

    def make_equation(self):
        '''
            y=Ax+B
            y=Ax2+Bx+C
        '''
        n = len(self.coefficients) - 1
        constant = ALPHAS[n]
        ps = []
        for i in range(n):
            a = ALPHAS[i]

            e = n - i
            if e > 1:
                a = '{}x{}'.format(a, e)
            else:
                a = '{}x'.format(a)
            ps.append(a)

        fit = self.fit
        eq = '+'.join(ps)
        s = '{}    y={}+{}'.format(fit, eq, constant)
        return s

    def predict(self, x):
        raise NotImplementedError

    def predict_error(self, x, error_calc=None):
        raise NotImplementedError

    def calculate_pearsons_r(self, X, Y):

        Xbar = X.mean()
        Ybar = Y.mean()

        n = len(X)
        i_n = (n - 1) ** -1

        sx = (i_n * sum((X - Xbar) ** 2)) ** 0.5
        sy = (i_n * sum((Y - Ybar) ** 2)) ** 0.5
        A = (X - Xbar) / sx
        B = (Y - Ybar) / sy
        r = i_n * sum(A * B)
        return r

    def calculate_outliers(self, nsigma=2):
        res = self.calculate_residuals()
        cd = abs(res)
        s = self.calculate_standard_error_fit()
        return where(cd > (s * nsigma))[0]

    def calculate_standard_error_fit(self):
        res = self.calculate_residuals()

        ss_res = (res ** 2).sum()
        #        s = std(devs)
        #        s = (dd.sum() / (devs.shape[0])) ** 0.5

        '''
            mass spec calculates error in fit as 
            see LeastSquares.CalcResidualsAndFitError
            
            SigmaFit=Sqrt(SumSqResid/((NP-1)-(q-1)))
  
            NP = number of points
            q= number of fit params... parabolic =3
        '''
        n = res.shape[0]
        q = self._degree
        s = (ss_res / (n - q)) ** 0.5
        return s

    @cached_property
    def _get_coefficients(self):
        return self._calculate_coefficients()

    @cached_property
    def _get_coefficient_errors(self):
        return self._calculate_coefficient_errors()

    def _calculate_coefficients(self):
        raise NotImplementedError

    def _calculate_coefficient_errors(self):
        raise NotImplementedError

    def calculate_residuals(self):
        return self.predict(self.xs) - self.ys

    def calculate_ci(self, rx, rmodel):
        cors = self._calculate_ci(rx, rmodel)
        #         print cors
        if rmodel is not None and cors is not None:
            if rmodel.shape[0] and cors.shape[0]:
                return rmodel - cors, rmodel + cors

                #                 lci, uci = zip(*[(yi - ci, yi + ci) for yi, ci in zip(rmodel, cors)])
                #                 return asarray(lci), asarray(uci)

    def _calculate_ci(self, rx, rmodel):
        if isinstance(rx, (float, int)):
            rx = [rx]

        X = self.xs
        Y = self.ys
        #         model = self.predict(X)
        #         rmodel = self.predict(rx)
        cors = self._calculate_confidence_interval(X, Y, rx, rmodel)
        return cors

    def _calculate_confidence_interval(self,
                                       x,
                                       observations,
                                       rx,
                                       model,
                                       confidence=95):

        alpha = 1.0 - confidence / 100.0

        n = len(observations)
        if n > 2:
            xm = x.mean()
            observations = array(observations)
            model = array(model)

            ti = tinv(alpha, n - 2)

            syx = self.syx()
            ssx = self.ssx(xm)

            d = n ** -1 + (rx - xm) ** 2 / ssx
            cors = ti * syx * d ** 0.5

            return cors


    def syx(self):
        n = self.xs.shape[0]
        obs = self.ys

        #         for di in dir(self._result):
        #             print di

        #         model = self._result.fittedvalues
        model = self.predict(self.xs)
        #         print 'sssss', model.shape, obs.shape
        if model is not None:
            return (1. / (n - 2) * ((obs - model) ** 2).sum()) ** 0.5
        else:
            return 0

    def ssx(self, xm=None):
        x = self.xs
        if xm is None:
            xm = x.mean()

        return ((x - xm) ** 2).sum()

    def _get_fit(self):
        return self._fit

    def _set_fit(self, v):
        self._fit = v
        self.dirty = True

#    fit = property(fset=_set_fit, fget=_get_fit)
#            lower=[]
#                lower.append(rmodel[i] - cor)
#                upper.append(rmodel[i] + cor)
#============= EOF =============================================
