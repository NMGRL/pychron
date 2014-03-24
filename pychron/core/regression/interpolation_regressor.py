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
from traits.api import Str

from pychron.core.regression.base_regressor import BaseRegressor

#============= standard library imports ========================
from numpy import where, polyval, polyfit, asarray
#============= local library imports  ==========================

class InterpolationRegressor(BaseRegressor):
    kind = Str
    def _calculate_coefficients(self):
        pass

    def predict(self, xs):
        return self._predict(xs, 'value')

    def predict_error(self, xs):
        return self._predict(xs, 'error')

    def _predict(self, xs, attr):
        kind = self.kind.replace(' ', '_')
        func = getattr(self, '{}_predictors'.format(kind))
        if not hasattr(xs, '__iter__'):
            xs = (xs,)
        xs = (func(xi, attr) for xi in xs)

        #filter out None values. None values occur say if looking for a preceding blank and none exists
        return [xi for xi in xs if xi is not None]

    def preceding_predictors(self, timestamp, attr='value'):
        xs = self.xs
        ys = self.ys

        es = self.yserr
        try:
            ti = where(xs <= timestamp)[0][-1]
            if attr == 'value':
                return ys[ti]
            else:
                return es[ti]
        except IndexError:
            pass

    def bracketing_average_predictors(self, tm, attr='value'):
        try:
            pb, ab, _ = self._bracketing_predictors(tm, attr)

            return (pb + ab) / 2.0
        except TypeError:
            return 0

    def bracketing_interpolate_predictors(self, tm, attr='value'):
        xs = self.xs
        try:
            pb, ab, ti = self._bracketing_predictors(tm, attr)

            x = [xs[ti], xs[ti + 1]]
            y = [pb, ab]

            if attr == 'error':
                '''
                    geometrically sum the errors and weight by the fractional difference
                    
                    0----10----------------100
                    f=0.1
                '''
                f = (tm - x[0]) / (x[1] - x[0])
                v = (((1 - f) * pb) ** 2 + (f * ab) ** 2) ** 0.5
            else:
                v = polyval(polyfit(x, y, 1), tm)
            return v
        except TypeError:
            return 0

    def _bracketing_predictors(self, tm, attr):
        xs = self.xs
        ys = self.ys
        es = self.yserr

        try:
            ti = where(xs < tm)[0][-1]
            if attr == 'value':
                pb = ys[ti]
                ab = ys[ti + 1]
            else:
                pb = es[ti]
                ab = es[ti + 1]

            return pb, ab, ti
        except IndexError:
            return 0

class GaussianRegressor(BaseRegressor):
    def _calculate_coefficients(self):
        pass
    def predict(self, xs):
        if isinstance(xs, (float, int)):
            xs = [xs]
        xs = asarray(xs)

        gp = self._calculate()
        ypred, mse = gp.predict(xs, eval_MSE=True)
        sigma = mse ** 0.5
        return ypred, sigma

    def _calculate(self):
        from sklearn.gaussian_process.gaussian_process import GaussianProcess

        X = self.xs.reshape((self.xs.shape[0], 1))
        y = self.ys
        yserr = self.yserr
        nugget = (yserr / y) ** 2
        gp = GaussianProcess(
#                             nugget=nugget
                             )

        gp.fit(X, y)
        return gp

if __name__ == '__main__':
    import numpy as np
    from matplotlib import pyplot as pl
    n = 20
    xs = np.linspace(0, 10, n)
#    ys = a * xs + b
    def f(xx):
        a = 0
        b = 2
        return a * xx + b

    yserr = [np.random.normal() for _ in range(n)]
    gp = GaussianRegressor(xs=xs, ys=f(xs) + yserr, yserr=yserr)

    x = np.atleast_2d(np.linspace(0, 10, 1000)).T
    y_pred, sigma = gp.predict(x)
    fig = pl.figure()

    pl.plot(x, f(x), 'r:', label=u'$f(x) = x\,\sin(x)$')
    pl.plot(xs, f(xs) + yserr, 'r.', markersize=10, label=u'Observations')
    pl.plot(x, y_pred, 'b-', label=u'Prediction')
    pl.fill(np.concatenate([x, x[::-1]]), \
            np.concatenate([y_pred - 1.9600 * sigma,
                           (y_pred + 1.9600 * sigma)[::-1]]), \
            alpha=.5, fc='b', ec='None', label='95% confidence interval')
    pl.xlabel('$x$')
    pl.ylabel('$f(x)$')
    pl.ylim(-10, 20)
    pl.legend(loc='upper left')

    pl.show()

#============= EOF =============================================
