# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= enthought library imports =======================
# from traits.api import HasTraits, Str, Float, Property, Instance, \
#     String, Either, Dict, cached_property, Event, List, Bool, Int, Array
# ============= standard library imports ========================
import re
import struct
from binascii import hexlify
from math import isnan, isinf

import six
from numpy import array, Inf, polyfit, gradient, array_split, mean, isfinite
from uncertainties import ufloat, nominal_value, std_dev

from pychron.core.geometry.geometry import curvature_at
from pychron.core.helpers.binpack import unpack
from pychron.core.helpers.fits import natural_name_fit, fit_to_degree
from pychron.core.regression.least_squares_regressor import (
    ExponentialRegressor,
    FitError,
    LeastSquaresRegressor,
)
from pychron.core.regression.mean_regressor import MeanRegressor
from pychron.core.regression.ols_regressor import PolynomialRegressor
from pychron.pychron_constants import AUTO_N


def fit_abbreviation(
    fit,
):
    f = ""
    if fit:
        f = fit[0].upper()
    return f


class BaseMeasurement(object):
    unpack_error = None
    endianness = ">"
    reverse_unpack = False
    use_manual_value = False
    use_manual_error = False
    units = "fA"
    _n = None
    detector = None
    detector_serial_id = None
    group_data = 0
    _regressor = None

    @property
    def n(self):
        if self._n:
            return self._n

        return self.xs.shape[0]

    @n.setter
    def n(self, v):
        self._n = v

    @property
    def offset_xs(self):
        return self.xs - self.time_zero_offset

    def __init__(self, name, detector):
        self.name = name
        self.detector = detector
        self.xs, self.ys = array([]), array([])
        self.mass = 0
        self.time_zero_offset = 0

    def set_grouping(self, n):
        self.group_data = n
        self._regressor = None
        # if self._regressor:
        #     self._regressor.dirty = True

    def get_data(self):
        xs = self.offset_xs
        ys = self.ys
        if self.group_data > 1:
            n = len(xs) // self.group_data
            xs = [mean(g) for g in array_split(xs, n)]
            ys = [mean(g) for g in array_split(ys, n)]

        return xs, ys

    def pack(self, endianness=None, as_hex=True):
        if endianness is None:
            endianness = self.endianness

        fmt = "{}ff".format(endianness)
        txt = b"".join((struct.pack(fmt, x, y) for x, y in zip(self.xs, self.ys)))
        if as_hex:
            txt = hexlify(txt)
        return txt

    def unpack_data(self, blob, n_only=False):
        if not blob:
            return

        try:
            xs, ys = self._unpack_blob(blob)
        except (ValueError, TypeError, IndexError, AttributeError) as e:
            self.unpack_error = e
            return

        if n_only:
            self.n = len(xs)
        else:
            self.xs = array(xs)
            self.ys = array(ys)

            # print self.name, self.xs.shape, self.ys.shape
            # print self.name, self.ys

    def _unpack_blob(self, blob, endianness=None):
        if endianness is None:
            endianness = self.endianness

        try:
            x, y = unpack(blob, fmt="{}ff".format(endianness))
            # x, y = zip(*[struct.unpack('{}ff'.format(endianness), blob[i:i + 8]) for i in range(0, len(blob), 8)])
            if self.reverse_unpack:
                return y, x
            else:
                return x, y

        except struct.error as e:
            print("unpack_blob", e)

    def get_slope(self, n=-1):
        if (
            self.xs.shape[0]
            and self.ys.shape[0]
            and self.xs.shape[0] == self.ys.shape[0]
        ):
            xs = self.offset_xs
            ys = self.ys
            if n != -1:
                xs = xs[-n:]
                ys = ys[-n:]

            xs = xs[isfinite(xs)]
            ys = ys[isfinite(ys)]
            try:
                return polyfit(xs, ys, 1)[0]
            except BaseException as e:
                print("get slope exception", e)
                return 0
        else:
            return 0

    def get_curvature(self, x):
        ys = self._get_curvature_ys()
        if ys is not None and len(ys):
            # if x is between 0-1 treat as a percentage of the total number of points
            if 0 < x < 1:
                x = self.xs.shape[0] * x

            return curvature_at(ys, x)
        else:
            return 0

    def _get_curvature_ys(self):
        return self.ys


class IsotopicMeasurement(BaseMeasurement):
    fit_blocks = None
    error_type = None
    filter_outliers_dict = None
    include_baseline_error = False
    use_static = False
    user_defined_value = False
    user_defined_error = False
    use_stored_value = False
    reviewed = False
    ic_factor_reviewed = False
    ic_factor_fit = None

    _value = 0
    _error = 0
    truncate = None
    _fit = None

    _oerror = None
    _ovalue = None

    _fn = None

    def __init__(self, *args, **kw):
        super(IsotopicMeasurement, self).__init__(*args, **kw)
        self.filter_outliers_dict = dict()

    def get_linear_rsquared(self):
        from pychron.core.regression.ols_regressor import OLSRegressor

        reg = OLSRegressor(fit="linear", xs=self.offset_xs, ys=self.ys)
        reg.calculate()
        return reg.rsquared

    def get_rsquared(self):
        return self._regressor.rsquared

    def get_gradient(self):
        return ((gradient(self.ys) ** 2).sum()) ** 0.5

    def get_xsquared_coefficient(self):
        if self._regressor:
            return self._regressor.get_xsquared_coefficient()

    @property
    def efit(self):
        fit = self.fit
        if fit and "_" not in fit:
            fit = "{}_{}".format(fit, self.error_type)
        return fit

    @property
    def rsquared(self):
        if self._regressor:
            return self._regressor.rsquared

    @property
    def rsquared_adj(self):
        if self._regressor:
            return self._regressor.rsquared_adj

    @property
    def fn(self):
        if self._fn is not None:
            n = self._fn
        elif self._regressor:
            n = self._regressor.clean_xs.shape[0]
        else:
            n = self.n

        return n

    @fn.setter
    def fn(self, v):
        self._fn = v

    @property
    def user_excluded(self):
        if self._regressor:
            return [int(i) for i in self._regressor.user_excluded]

    @property
    def outlier_excluded(self):
        if self._regressor:
            return [int(i) for i in self._regressor.outlier_excluded]

    def set_user_excluded(self, ue):
        if ue:
            reg = self._regressor
            if not reg:
                reg = self.regressor

            reg.ouser_excluded = ue

    def set_filtering(self, d):
        self.filter_outliers_dict = d.copy()
        if self._regressor:
            self._regressor.dirty = True

    def set_fit_blocks(self, fit):
        """
        fit: either tuple of (fit, error_type) or str
        if str either linear, parabolic etc or
        a fit block e.g
            1.  (,10,average)
                fit average from start to 10 counts
            2.  (10,,linear)
                fit linear from 10 to end counds
        """
        if isinstance(fit, tuple):
            fit, error = fit
            self.error_type = error

        if re.match(r"\([\w\d\s,]*\)", fit):
            fs = []
            for m in re.finditer(r"\([\w\d\s,]*\)", fit):
                a = m.group(0)
                a = a[1:-1]
                s, e, f = (ai.strip() for ai in a.split(","))
                if s is "":
                    s = -1
                else:
                    s = int(s)

                if e is "":
                    e = Inf
                else:
                    e = int(e)

                fs.append((s, e, f))

            self.fit_blocks = fs
        else:
            self.fit = fit

    def get_fit(self, cnt):
        r = self.get_fit_block(cnt)
        if r is not None:
            self.fit = r

        return self.fit

    def get_fit_block(self, cnt):
        if self.fit_blocks:
            if cnt < 0:
                return self.fit_blocks[-1][2]
            else:
                for s, e, f in self.fit_blocks:
                    if s < cnt < e:
                        return f

    def set_filter_outliers_dict(
        self,
        filter_outliers=True,
        iterations=1,
        std_devs=2,
        use_standard_deviation_filtering=False,
        use_iqr_filtering=False,
    ):
        self.filter_outliers_dict = {
            "filter_outliers": filter_outliers,
            "iterations": iterations,
            "std_devs": std_devs,
            "use_standard_deviation_filtering": use_standard_deviation_filtering,
            "use_iqr_filtering": use_iqr_filtering,
        }

        self._fn = None
        if self._regressor:
            self._regressor.dirty = True

    def attr_set(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    def set_fit_error_type(self, e):
        self.attr_set(error_type=e)

    def set_fit(self, fit, notify=True):
        if fit is not None:
            self.user_defined_value = False
            self.user_defined_error = False

            if isinstance(fit, (int, str, six.text_type)):
                self.attr_set(fit=fit)
            elif isinstance(fit, dict):
                self.attr_set(**fit)
            else:
                fitname = fit.fit
                if fitname == AUTO_N:
                    fitname = fit.auto_fit(self.n)
                elif fitname == "Custom":
                    fitname = "custom:{}".format(fit.fitfunc)

                self.attr_set(
                    fit=fitname,
                    time_zero_offset=fit.time_zero_offset or self.time_zero_offset,
                    error_type=fit.error_type or "SEM",
                    include_baseline_error=fit.include_baseline_error or False,
                )

                self.set_filter_outliers_dict(
                    filter_outliers=bool(fit.filter_outliers),
                    iterations=int(fit.filter_outlier_iterations or 0),
                    std_devs=int(fit.filter_outlier_std_devs or 0),
                    use_standard_deviation_filtering=fit.use_standard_deviation_filtering,
                    use_iqr_filtering=fit.use_iqr_filtering,
                )
                self.truncate = fit.truncate

            self._regressor = None

    def set_uvalue(self, v):
        if isinstance(v, tuple):
            self._value, self._error = v
        else:
            self._value, self._error = nominal_value(v), std_dev(v)

    def _revert_user_defined(self):
        self.user_defined_error = False
        self.user_defined_value = False
        if self._ovalue is not None:
            self._value = self._ovalue
        if self._oerror is not None:
            self._error = self._oerror

    @property
    def value(self):
        # if not (self.name.endswith('bs') or self.name.endswith('bk')):
        #     print self.name, self.use_static,self.user_defined_value
        # print 'get value', self.name, self.use_static, self._value, self.user_defined_value
        # if self.use_static and self._value:
        #     return self._value
        # elif self.user_defined_value:
        #     return self._value

        if (
            not self.use_stored_value
            and not self.user_defined_value
            and self.xs.shape[0] > 1
        ):
            v = self.regressor.predict(0)

            if isnan(v) or isinf(v):
                v = 0
            return v
        else:
            return self._value

    @property
    def error(self):
        # if self.use_static and self._error:
        #     return self._error
        # elif self.user_defined_error:
        #     return self._error

        if (
            not self.use_stored_value
            and not self.user_defined_error
            and self.xs.shape[0] > 1
        ):
            v = self.regressor.predict_error(0)
            if isnan(v) or isinf(v):
                v = 0
            return v
        else:
            return self._error

    @error.setter
    def error(self, v):
        self.user_defined_error = True
        try:
            # self._oerror = self._error
            self._error = float(v)
        except ValueError:
            pass

    @value.setter
    def value(self, v):
        self.user_defined_value = True
        try:
            # self._ovalue = self._value
            self._value = float(v)
        except ValueError:
            pass

    @property
    def regressor(self):
        fit = self.fit
        if fit is None:
            fit = "linear"
            self.fit = fit
        return self._regressor_factory(fit)

    def _regressor_factory(self, fit):
        lfit = fit.lower()
        reg = self._regressor

        if "average" in lfit:
            if not isinstance(reg, MeanRegressor):
                reg = MeanRegressor()
        elif lfit == "exponential":
            if not isinstance(reg, ExponentialRegressor):
                reg = ExponentialRegressor()
        elif lfit.startswith("custom:"):
            if not isinstance(reg, LeastSquaresRegressor):
                reg = LeastSquaresRegressor()
                reg.construct_fitfunc(lfit)
        elif not isinstance(reg, PolynomialRegressor):
            reg = PolynomialRegressor()
            reg.set_degree(fit, refresh=False)

        xs, ys = self.get_data()
        reg.trait_set(
            xs=xs,
            ys=ys,
            error_calc_type=self.error_type or "SEM",
            filter_outliers_dict=self.filter_outliers_dict,
            tag=self.name,
        )

        if self.truncate:
            reg.set_truncate(self.truncate)
        try:
            fit = reg.determine_fit(lfit)
            self.fit = fit
            reg.calculate()
        except FitError as e:
            reg = self._regressor_factory("average")

        self._regressor = reg
        return reg

    # @cached_property
    @property
    def uvalue(self):
        # v = self._uvalue
        # if v is None or self._dirty:
        # if self.name == 'Ar39':
        #     print self.__class__.__name__, self.value, self.error
        v = ufloat(self.value, self.error, tag=self.name)

        return v

    @property
    def fit_abbreviation(self):
        return "{}{}".format(
            fit_abbreviation(self.fit),
            "*" if self.filter_outliers_dict.get("filter_outliers") else "",
        )

    # def _get_fit_abbreviation(self):
    #     return '{}{}'.format(fit_abbreviation(self.fit),
    #                          '*' if self.filter_outliers_dict.get('filter_outliers') else '')

    @property
    def fit(self):
        return self._fit

    @fit.setter
    def fit(self, f):
        f = natural_name_fit(f)
        self._fit = f

    def standard_fit_error(self):
        return self.regressor.calculate_standard_error_fit()

    def noutliers(self):
        return self.regressor.xs.shape[0] - self.regressor.clean_xs.shape[0]

    def _get_curvature_ys(self):
        return self.regressor.predict(self.offset_xs)

    # def _error_type_changed(self):
    #     self.regressor.error_calc_type = self.error_type

    # ===============================================================================
    # arithmetic
    # ===============================================================================
    def __add__(self, a):
        return self.uvalue + a

    def __radd__(self, a):
        return self.__add__(a)

    def __mul__(self, a):
        return self.uvalue * a

    def __rmul__(self, a):
        return self.__mul__(a)

    def __sub__(self, a):
        return self.uvalue - a

    def __rsub__(self, a):
        return a - self.uvalue

    def __div__(self, a):
        return self.uvalue / a

    def __rdiv__(self, a):
        return a / self.uvalue


class CorrectionIsotopicMeasurement(IsotopicMeasurement):
    pass
    # def __init__(self, dbrecord=None, *args, **kw):
    #     if dbrecord:
    #         self._value = dbrecord.user_value if dbrecord.user_value is not None else 0
    #         self._error = dbrecord.user_error if dbrecord.user_value is not None else 0
    #
    #     super(IsotopicMeasurement, self).__init__(*args, **kw)


class Background(CorrectionIsotopicMeasurement):
    pass


class Baseline(IsotopicMeasurement):
    _kind = "baseline"


class Sniff(BaseMeasurement):
    pass


class Whiff(BaseMeasurement):
    pass


class BaseIsotope(IsotopicMeasurement):
    baseline = None

    # baseline_fit_abbreviation = Property(depends_on='baseline:fit')

    def set_grouping(self, n):
        super(BaseIsotope, self).set_grouping(n)
        self.baseline.set_grouping(n)

    @property
    def intercept_percent_error(self):
        try:
            return self.error / self.value
        except ZeroDivisionError:
            return -1

    @property
    def baseline_fit_abbreviation(self):
        if self.baseline:
            return self.baseline.fit_abbreviation
        else:
            return ""

    def __init__(self, name, detector):
        IsotopicMeasurement.__init__(self, name, detector)
        self.baseline = Baseline("{} bs".format(name), detector)

    def get_baseline_corrected_value(
        self, include_baseline_error=None, window=None, count=None
    ):
        if include_baseline_error is None:
            include_baseline_error = self.include_baseline_error

        b = self.baseline.uvalue
        if window:
            ys = self.sniff.ys[-window:]
            v = ys.mean()
            e = ys.std()
            uv = ufloat(v, e, tag=self.name)
        elif count:
            v = self.sniff.ys[count]
            e = 0
            uv = ufloat(v, e, tag=self.name)
        else:
            uv = self.uvalue

        if not include_baseline_error:
            b = nominal_value(b)
            nv = uv - b
            return ufloat(nominal_value(nv), std_dev(nv), tag=self.name)
        else:
            return uv - b

    def _get_baseline_fit_abbreviation(self):
        return self.baseline.fit_abbreviation


class Blank(BaseIsotope):
    pass


class Isotope(BaseIsotope):
    _kind = "signal"

    # blank = Instance(Blank)
    # background = Instance(Background)
    # sniff = Instance(Sniff)
    temporary_blank = None
    ic_factor = 1.0
    correct_for_blank = True
    # ic_factor = Either(Variable, AffineScalarFunc)

    age_error_component = 0.0
    # temporary_ic_factor = None
    # temporary_blank = Instance(Blank)
    decay_corrected = None

    discrimination = None
    interference_corrected_value = None
    blank_source = ""

    klass = 1

    def __init__(self, name, detector):
        BaseIsotope.__init__(self, name, detector)
        self.blank = Blank("{} bk".format(name), detector)
        self.sniff = Sniff(name, detector)
        self.background = Background("{} bg".format(name), detector)
        self.whiff = Whiff(name, detector)

    def set_detector_serial_id(self, sid):
        self.detector_serial_id = sid
        self.blank.detector_serial_id = sid
        self.sniff.detector_serial_id = sid
        self.baseline.detector_serial_id = sid

    def set_time_zero(self, time_zero_offset):
        self.time_zero_offset = time_zero_offset
        self.blank.time_zero_offset = time_zero_offset
        self.sniff.time_zero_offset = time_zero_offset
        self.baseline.time_zero_offset = time_zero_offset

    def set_units(self, units):
        self.units = units
        self.blank.units = units
        self.sniff.units = units
        self.baseline.units = units

    def get_filtered_data(self):
        return self.regressor.calculate_filtered_data()

    def revert_user_defined(self):
        self.blank._revert_user_defined()
        self.baseline._revert_user_defined()
        self._revert_user_defined()

    def get_ic_decay_corrected_value(self):
        if self.decay_corrected is not None:
            return self.decay_corrected
        else:
            return self.get_ic_corrected_value()

    def get_decay_corrected_value(self):
        if self.decay_corrected is not None:
            return self.decay_corrected
        else:
            return self.get_non_detector_corrected_value()
            # return self.get_interference_corrected_value()

    def get_interference_corrected_value(self):
        if self.interference_corrected_value is not None:
            return self.interference_corrected_value
        else:
            return ufloat(0, 0, tag=self.name)

    def get_intensity(self, **kw):
        """
        return the discrimination and ic_factor corrected value
        """
        v = self.get_disc_corrected_value(**kw) * (self.ic_factor or 1.0)

        # this is a temporary hack for handling Minna bluff data
        if self.detector.lower() == "faraday":
            v = v - self.blank.uvalue
        # if self._regressor:
        #     print 'get intensity {}{} regressor={}'.format(self.name, self.detector, id(self._regressor))
        return v

    def get_disc_corrected_value(self, **kw):
        disc = self.discrimination
        if disc is None:
            disc = 1

        return self.get_non_detector_corrected_value(**kw) * disc

    def get_ic_corrected_value(self):
        return self.get_non_detector_corrected_value() * (self.ic_factor or 1.0)

    def no_baseline_error(self):
        v = self.get_baseline_corrected_value(include_baseline_error=False)

        if self.correct_for_blank:
            v = v - self.blank.value
        return v

    def get_non_detector_corrected_value(self, **kw):
        v = self.get_baseline_corrected_value(**kw)

        # this is a temporary hack for handling Minna bluff data
        if self.correct_for_blank and self.detector.lower() != "faraday":
            v = v - self.blank.uvalue

        if self.background:
            v = v - self.background.uvalue

        return v

    def set_ublank(self, v):
        self.blank = Blank("{} bk".format(self.name), self.detector)
        self.blank.set_uvalue(v)

    def set_blank(self, v, e):
        self.set_ublank((v, e))

    def set_baseline(self, v, e):
        self.baseline = Baseline("{} bs".format(self.name), self.detector)
        self.baseline.set_uvalue((v, e))

    def _whiff_default(self):
        return Whiff()

    def _sniff_default(self):
        return Sniff()

    def _background_default(self):
        return Background()

    def _blank_default(self):
        return Blank()

    def __eq__(self, other):
        return self.get_baseline_corrected_value().__eq__(other)

    def __le__(self, other):
        return self.get_baseline_corrected_value().__le__(other)

    def __ge__(self, other):
        return self.get_baseline_corrected_value().__ge__(other)

    def __gt__(self, other):
        return self.get_baseline_corrected_value().__gt__(other)

    def __lt__(self, other):
        return self.get_baseline_corrected_value().__lt__(other)

    def __str__(self):
        try:
            return "{} {}".format(self.name, self.get_baseline_corrected_value())
        except (OverflowError, ValueError, AttributeError, TypeError) as e:
            return "{} {}".format(self.name, e)


# ============= EOF =============================================
