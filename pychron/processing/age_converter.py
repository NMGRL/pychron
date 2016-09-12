# ===============================================================================
# Copyright 2016 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= standard library imports ========================
# ============= local library imports  ==========================
from numpy import exp, ones, log, std, mean
from numpy.random.mtrand import randn
from uncertainties import ufloat, nominal_value, std_dev


class AgeConverter(object):
    """
    ported from Renne_2011_noLSC.m (Leah Morgan USGS 2016)
    original source available in  docs/dev_guide

    """

    _original_monitor_age = None
    _original_total_decay_constant = None

    def __init__(self, n=10e4, arar_constants=None):
        self._n = n
        if arar_constants is None:
            self._lambda_ec = ec = ufloat(5.757e-11, 1.6e-13)
            self._lambda_b = b = ufloat(4.955e-10, 1.34e-12)

            self._lambda_t = ec + b

        self._f = ufloat(0.001642, 4.50e-6)  # 40Ar*/40K for mineral standard

    def setup(self, monitor_age=28.02, total_decay=5.543e-10):
        self._original_monitor_age = monitor_age
        self._original_total_decay_constant = total_decay

    def convert(self, age, error):
        if hasattr(age, '__iter__'):
            m = len(age)
        else:
            m = 1

        oma = self._original_monitor_age
        torig = self._original_total_decay_constant
        t = self._lambda_t

        ex_orig = exp(t * oma * 1e6) - 1
        ex = exp(t * age * 1e6) - 1

        r = ex / ex_orig
        sr = torig * exp(torig * age * 1e6) * error * 1e6 / ex_orig

        r_mc = ones(self._n) * r
        sr_mc = ones(self._n) * sr

        vr = r_mc + sr_mc * randn(self._n, m)

        t = log(((t / self._lambda_ec) * self._f * r) + 1) / (t * 1e6)

        # linear error propagation

        e = self._linear_error_propagation(t * 1e6, r, vr, m)
        e *= 1e-6

        tm, tme = self._monte_carlo_error_propagation()
        tm *= 1e-6
        tme *= 1e-6

        return t, e, tm, tme

    def _monte_carlo_error_propagation(self, vr, m):
        lambda_total = self._lambda_t
        el = self._lambda_ec
        f = self._f

        vel = nominal_value(el) + std_dev(el) * randn(self._n)
        vt = nominal_value(lambda_total) + std_dev(lambda_total) * randn(self._n)
        vf = nominal_value(f) + std_dev(f) * randn(self._n)

        vt_mc = ones(1, m) * vt
        vf_mc = ones(1, m) * vf
        vel_mc = ones(1, m) * vel

        t_mc = log(vt_mc / vel_mc * vf_mc * vr + 1) / vt_mc
        return mean(t_mc), std(t_mc)

    def _linear_error_propagation(self, age, r, vr, m):
        """
        age in years
        :param age:
        :param r:
        :return: linear error propagation age error in years
        """

        lambda_total = self._lambda_t
        b = self._lambda_b
        el = self._lambda_ec
        f = self._f

        # partial derivatives
        pd_el = -(1. / lambda_total) * (age + (b * f * r / ((el ** 2) * exp(lambda_total * age))))
        pd_b = (1 / lambda_total) * ((f * r / (el * exp(lambda_total * age))) - age)
        pd_f = r / (el * exp(lambda_total * age))
        pd_r = f / (el * exp(lambda_total * age))

        sel = std_dev(el)
        sb = std_dev(b)
        sf = std_dev(self._f)
        sr = std_dev(r)

        # (partial derivatives x sigma) ** 2
        pd_el2 = (pd_el * sel) ** 2
        pd_b2 = (pd_b * sb) ** 2
        pd_f2 = (pd_f * sf) ** 2
        pd_r2 = (pd_r * sr) ** 2

        sum_pd = pd_el2 + pd_b2 + pd_f2 + pd_r2

        # covariances
        cov_f_el = 7.1903e-19
        cov_f_b = -6.5839e-19
        cov_el_b = -3.4711e-26

        cov_f_el2 = 2. * cov_f_el * pd_f * pd_el
        cov_f_b2 = 2. * cov_f_b * pd_f * pd_b
        cov_el_b = 2. * cov_el_b * pd_el * pd_b

        sum_cov = cov_f_el2 + cov_f_b2 + cov_el_b

        ss = sum_pd + sum_cov

        # uncertainty in age
        st = ss ** 0.5
        return st

# ============= EOF =============================================
