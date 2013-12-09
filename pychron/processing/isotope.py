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
from traits.api import HasTraits, Str, Float, Property, Instance, \
    Array, String, Either, Dict, cached_property, Event

#============= standard library imports ========================
from uncertainties import ufloat, Variable, AffineScalarFunc, nominal_value
from numpy import array
from pychron.regression.mean_regressor import MeanRegressor
from pychron.regression.ols_regressor import PolynomialRegressor
import struct
#============= local library imports  ==========================
#logger = new_logger('isotopes')

def fit_abbreviation(fit):
    f = ''
    if fit:
        f = fit[0].upper()
    return f


class BaseMeasurement(HasTraits):
    xs = Array
    ys = Array

    n = Property(depends_on='xs')
    name = Str
    mass = Float
    detector = Str

    unpack_error = None
    endianness = '>'
    reverse_unpack = False

    def __init__(self, dbrecord=None, unpack=True, unpacker=None, *args, **kw):
        super(BaseMeasurement, self).__init__(*args, **kw)

        if dbrecord and unpack:
            try:
                if unpacker is None:
                    unpacker = lambda x: x.signal.data
                xs, ys = self._unpack_blob(unpacker(dbrecord))
            except (ValueError, TypeError, IndexError, AttributeError), e:
                self.unpack_error = e
                return

            self.xs = array(xs)
            self.ys = array(ys)
        
    def _unpack_blob(self, blob, endianness=None):
        if endianness is None:
            endianness = self.endianness

        try:
            x, y = zip(*[struct.unpack('{}ff'.format(endianness), blob[i:i + 8]) for i in xrange(0, len(blob), 8)])
            if self.reverse_unpack:
                return y, x
            else:
                return x, y

        except struct.error, e:
            print 'unpack_blob', e

    def _get_n(self):
        return len(self.xs)


class IsotopicMeasurement(BaseMeasurement):
    uvalue = Property(depends='value, error, _value, _error, dirty')

    value = Property(depends_on='_value,fit, dirty')
    error = Property(depends_on='_error,fit, dirty')
    _value = Float
    _error = Float

    fit = String
    fit_abbreviation = Property(depends_on='fit')

    filter_outliers_dict=Dict

    regressor = Property(depends_on='xs,ys,fit, dirty')
    dirty=Event

    def __init__(self, dbresult=None, *args, **kw):
        
        if dbresult:
            self._value = dbresult.signal_
            self._error = dbresult.signal_err
        else:
            kw['unpack'] = True

        super(IsotopicMeasurement, self).__init__(*args, **kw)

    def set_fit(self, fit):
        if fit is not None:
            self.filter_outliers_dict=dict(filter_outliers=bool(fit.filter_outliers),
                                           iterations=int(fit.filter_outlier_iterations),
                                           std_devs=int(fit.filter_outlier_std_devs))
            self.fit = fit.fit

    def set_uvalue(self, v):
        if isinstance(v, tuple):
            self._value, self._error = v
        else:
            self._value = v.nominal_value
            self._error = v.std_dev

        self.dirty=True

    def _mean_regressor_factory(self):
        reg = MeanRegressor(xs=self.xs, ys=self.ys,
                            filter_outliers_dict=self.filter_outliers_dict)
        return reg

    def _set_error(self, v):
        self._error = v

    def _set_value(self, v):
        self._value = v

    #@cached_property
    def _get_value(self):
        if self.xs is not None and len(self.xs) > 1:  # and self.ys is not None:
        #            if len(self.xs) > 2 and len(self.ys) > 2:
        #            print self.xs
        #            print self._get_regression_param('coefficients')
        #            return self._get_regression_param('coefficients')
            return self.regressor.predict(0)
        else:
            return self._value

    #@cached_property
    def _get_error(self):
        if self.xs is not None and len(self.xs) > 1:
        #            if len(self.xs) > 2 and len(self.ys) > 2:
            return self.regressor.predict_error(0)
        #            return self._get_regression_param('coefficient_errors')
        else:
            return self._error

    #@cached_property
    def _get_regressor(self):
        try:
            if 'average' in self.fit.lower():
                reg = self._mean_regressor_factory()
            else:
                reg = PolynomialRegressor(xs=self.xs,
                                          ys=self.ys,
                                          degree=self.fit,
                                          filter_outliers_dict=self.filter_outliers_dict)

        except Exception, e:
            reg = PolynomialRegressor(xs=self.xs, ys=self.ys,
                                      degree=self.fit,
                                      filter_outliers_dict=self.filter_outliers_dict)

        reg.calculate()

        return reg

    #@cached_property
    def _get_uvalue(self):
        return ufloat(self.value, self.error)

    def _get_fit_abbreviation(self):
        return fit_abbreviation(self.fit)

    #===============================================================================
    # arthmetic
    #===============================================================================
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
    #        return self.uvalue - a
        return a - self.uvalue

    def __div__(self, a):
        return self.uvalue / a

    def __rdiv__(self, a):
    #        return self.uvalue / a
        return a / self.uvalue


class CorrectionIsotopicMeasurement(IsotopicMeasurement):
    pass

    def __init__(self, dbrecord=None, *args, **kw):
        if dbrecord:
            self._value = dbrecord.user_value if dbrecord.user_value is not None else 0
            self._error = dbrecord.user_error if dbrecord.user_value is not None else 0

        super(IsotopicMeasurement, self).__init__(*args, **kw)

        #        if self.dbrecord:

#            self._value = self.dbrecord.user_value
#            self._error = self.dbrecord.user_error

class Background(CorrectionIsotopicMeasurement):
    pass


class Blank(CorrectionIsotopicMeasurement):
    pass


class Baseline(IsotopicMeasurement):
    _kind = 'baseline'


class Sniff(BaseMeasurement):
    pass


class Isotope(IsotopicMeasurement):
    _kind = 'signal'

    baseline = Instance(Baseline)
    blank = Instance(Blank)
    background = Instance(Background)
    sniff = Instance(Sniff)

    correct_for_blank = True
    ic_factor = Either(Variable, AffineScalarFunc)

    age_error_component = Float(0.0)
    temporary_ic_factor = None

    baseline_fit_abbreviation = Property(depends_on='baseline:fit')

    discrimination = Either(Variable, AffineScalarFunc)

    interference_corrected_value = Either(Variable, AffineScalarFunc)

    def get_interference_corrected_value(self):
        return self.interference_corrected_value

    def get_intensity(self):
        """
            return the discrimination and ic_factor corrected value
        """
        return self.disc_corrected_value() * self.ic_factor

    def disc_corrected_value(self):
        disc = self.discrimination
        if disc is None:
            disc = 1

        return self.get_corrected_value() * nominal_value(disc)

    def ic_corrected_value(self):
        return self.get_corrected_value() * self.ic_factor

    def baseline_corrected_value(self):
        nv=self.uvalue - self.baseline.uvalue.nominal_value
        return ufloat(nv.nominal_value, nv.std_dev, tag=self.name)

    def get_corrected_value(self):
        v = self.baseline_corrected_value()

        if self.correct_for_blank:
            v = v - self.blank.uvalue

        return v - self.background.uvalue

    def _baseline_default(self):
        return Baseline()

    def _blank_default(self):
        return Blank()

    def _background_default(self):
        return Background()

    def _get_baseline_fit_abbreviation(self):
        return fit_abbreviation(self.baseline.fit)

        #============= EOF =============================================
