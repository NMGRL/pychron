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

from traits.api import Array, List, Event, Property, Any, \
    Dict, Str, Bool, cached_property, HasTraits
#============= standard library imports ========================
import re
import math
from numpy import where, delete
#============= local library imports  ==========================
from pychron.core.codetools.inspection import caller_stack
from tinv import tinv
from pychron.core.stats.core import calculate_mswd, validate_mswd
from pychron.pychron_constants import ALPHAS

import logging

logger = logging.getLogger('BaseRegressor')


class BaseRegressor(HasTraits):
    xs = Array
    ys = Array
    xserr = Array
    yserr = Array

    dirty = Event
    coefficients = Property(depends_on='dirty, xs, ys')
    coefficient_errors = Property(depends_on='coefficients, xs, ys')
    _coefficients = List
    _coefficient_errors = List
    _result = Any

    fit = Property
    _fit = Any

    n = Property(depends_on='dirty, xs, ys')

    user_excluded = List
    outlier_excluded = List
    truncate_excluded = List

    filter_outliers_dict = Dict
    truncate = Str

    filter_xs = Array
    filter_ys = Array
    # _filtering = Bool(False)

    error_calc_type = 'SD'

    mswd = Property(depends_on='dirty, xs, ys')
    valid_mswd = Bool

    pre_clean_xs = Property(depends_on='dirty, xs, ys')
    pre_clean_ys = Property(depends_on='dirty, xs, ys')

    clean_xs = Property(depends_on='dirty, xs, ys')
    clean_ys = Property(depends_on='dirty, xs, ys')
    clean_xserr = Property(depends_on='dirty, xs, ys')
    clean_yserr = Property(depends_on='dirty, xs, ys')
    clean_yserr = Property(depends_on='dirty, xs, ys')

    degrees_of_freedom = Property


    def calculate_filtered_data(self):
        fod = self.filter_outliers_dict

        if fod.get('filter_outliers', False):
            self.outlier_excluded = []
            for _ in range(fod.get('iterations', 1)):
                self.calculate(filtering=True)

                outliers = self.calculate_outliers(nsigma=fod.get('std_devs', 2))
                self.outlier_excluded = list(set(self.outlier_excluded + list(outliers)))

        self.dirty = True
        return self.clean_xs, self.clean_ys

    def get_excluded(self):
        return list(set(self.user_excluded + self.outlier_excluded + self.truncate_excluded))

    def set_truncate(self, trunc):
        self.truncate = trunc
        if self.truncate:
            m = re.match(r'[A-Za-z]+', self.truncate)
            if m:
                k = m.group(0)
                exclude = eval(self.truncate, {k: self.xs})
                excludes = list(exclude.nonzero()[0])
                self.truncate_excluded = excludes

    def calculate(self, *args, **kw):
        pass

    def format_percent_error(self, s, e):
        try:
            return '{:0.2}%'.format(abs(e / s * 100))
        except ZeroDivisionError:
            return 'Inf'

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
        """
            mass spec calculates error in fit as
            see LeastSquares.CalcResidualsAndFitError

            SigmaFit=Sqrt(SumSqResid/((NP-1)-(q-1)))

            NP = number of points
            q= number of fit params... parabolic =3
        """
        res = self.calculate_residuals()
        ss_res = (res ** 2).sum()

        n = res.shape[0]
        q = len(self.coefficients)
        s = (ss_res / (n - q)) ** 0.5
        return s

    def calculate_residuals(self):
        return self.predict(self.clean_xs) - self.clean_ys

    def calculate_error_envelope(self, rx, rmodel=None):
        if rmodel is None:
            rmodel = self.predict(rx)
        if self.error_calc_type == 'CI':
            func = self.calculate_ci
        elif self.error_calc_type == 'SD':
            func = self.calculate_sd_error_envelope
        else:
            func = self.calculate_sem_error_envelope
        return func(rx, rmodel)

    def calculate_sd_error_envelope(self, rx, rmodel):
        es = self.predict_error(rx, error_calc='SD')
        return rmodel - es, rmodel + es

    def calculate_sem_error_envelope(self, rx, rmodel):
        es = self.predict_error(rx, error_calc='SEM')
        return rmodel - es, rmodel + es

    def calculate_ci(self, rx, rmodel):
        cors = self.calculate_ci_error(rx, rmodel)
        if rmodel is not None and cors is not None:
            if rmodel.shape[0] and cors.shape[0]:
                return rmodel - cors, rmodel + cors

    def calculate_ci_error(self, rx, rmodel=None):
        if rmodel is None:
            rmodel = self.predict(rx)

        cors = self._calculate_ci(rx, rmodel)
        return cors

    def get_syx(self):
        n = self.clean_xs.shape[0]
        obs = self.clean_ys

        model = self.predict(self.clean_xs)
        if model is not None:
            return (1. / (n - 2) * ((obs - model) ** 2).sum()) ** 0.5
        else:
            return 0

    def get_ssx(self, xm=None):
        x = self.clean_xs
        if xm is None:
            xm = x.mean()

        return ((x - xm) ** 2).sum()

    def tostring(self, sig_figs=5, error_sig_figs=5):

        cs = self.coefficients[::-1]
        ce = self.coefficient_errors[::-1]

        coeffs = []
        for a, ci, ei in zip(ALPHAS, cs, ce):
            pp = '({})'.format(self.format_percent_error(ci, ei))
            fmt = '{{:0.{}e}}' if abs(ci) < math.pow(10, -sig_figs) else '{{:0.{}f}}'
            ci = fmt.format(sig_figs).format(ci)

            fmt = '{{:0.{}e}}' if abs(ei) < math.pow(10, -error_sig_figs) else '{{:0.{}f}}'
            ei = fmt.format(error_sig_figs).format(ei)

            vfmt = u'{}= {} +/- {} {}'
            coeffs.append(vfmt.format(a, ci, ei, pp))

        s = u', '.join(coeffs)
        return s

    def make_equation(self):
        """
            y=Ax+B
            y=Ax2+Bx+C
        """
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

    def _calculate_ci(self, rx, rmodel):
        if isinstance(rx, (float, int)):
            rx = [rx]

        X = self.clean_xs
        Y = self.clean_ys
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

            ti = tinv(alpha, n - 2)

            syx = self.get_syx()
            ssx = self.get_ssx(xm)

            d = n ** -1 + (rx - xm) ** 2 / ssx
            cors = ti * syx * d ** 0.5

            return cors

    def _delete_filtered_hook(self, outliers):
        pass

    @cached_property
    def _get_pre_clean_xs(self):
        return self._pre_clean_array(self.xs)

    @cached_property
    def _get_pre_clean_ys(self):
        return self._pre_clean_array(self.ys)

    @cached_property
    def _get_clean_xs(self):
        return self._clean_array(self.xs)

    @cached_property
    def _get_clean_ys(self):
        return self._clean_array(self.ys)

    @cached_property
    def _get_clean_xserr(self):
        return self._clean_array(self.xserr)

    @cached_property
    def _get_clean_yserr(self):
        return self._clean_array(self.yserr)

    def _pre_clean_array(self, v):
        exc = set(self.user_excluded) ^ set(self.truncate_excluded)
        return delete(v, list(exc), 0)

    def _clean_array(self, v):
        exc = set(self.user_excluded) ^ set(self.truncate_excluded) ^ set(self.outlier_excluded)
        return delete(v, list(exc), 0)

    def _check_integrity(self, x, y):
        nx, ny = len(x), len(y)
        if not nx or not ny:
            logger.warning('not x={} y={}'.format(nx, ny))
            return
        if nx != ny:
            logger.warning('x!=y x={} y={}'.format(nx, ny))
            return

        if nx == 1 or ny == 1:
            logger.warning('==1 x={} y={}'.format(nx, ny))
            return

        return True

    def _get_degrees_of_freedom(self):
        return 1

    @cached_property
    def _get_mswd(self):
        self.valid_mswd = False
        # ys=self._clean_array(self.ys)
        # yserr=self._clean_array(self.yserr)
        ys = self.clean_ys
        yserr = self.clean_yserr

        if self._check_integrity(ys, yserr):
            mswd = calculate_mswd(ys, yserr, k=self.degrees_of_freedom)
            self.valid_mswd = validate_mswd(mswd, len(ys), k=self.degrees_of_freedom) or False
            return mswd

    def _get_n(self):
        return len(self.clean_xs)

    def _get_coefficients(self):
        return self._calculate_coefficients()

    def _get_coefficient_errors(self):
        return self._calculate_coefficient_errors()

    def _calculate_coefficients(self):
        raise NotImplementedError

    def _calculate_coefficient_errors(self):
        raise NotImplementedError

    def _get_fit(self):
        return self._fit

    def _set_fit(self, v):
        self._fit = v
        self.dirty = True

#============= EOF =============================================
