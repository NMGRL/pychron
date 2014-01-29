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
from binascii import hexlify
from itertools import izip
import re
from traits.api import HasTraits, Str, Float, Property, Instance, \
    Array, String, Either, Dict, cached_property, Event, List

#============= standard library imports ========================
from uncertainties import ufloat, Variable, AffineScalarFunc
from numpy import array, Inf
from pychron.core.regression.mean_regressor import MeanRegressor
from pychron.core.regression.ols_regressor import PolynomialRegressor
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

    def __init__(self, dbrecord=None, unpack=False, unpacker=None, *args, **kw):
        super(BaseMeasurement, self).__init__(*args, **kw)
        # print 'uasdf', unpack, self.name, type(self)
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

    def pack(self, endianness=None, as_hex=True):
        if endianness is None:
            endianness = self.endianness

        fmt = '{}ff'.format(endianness)
        txt=''.join((struct.pack(fmt, x, y) for x, y in izip(self.xs, self.ys)))
        if as_hex:
            txt=hexlify(txt)
        return txt

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
    uvalue = Property(depends_on='value, error, _value, _error, dirty')

    value = Property(depends_on='_value,fit, dirty')
    error = Property(depends_on='_error,fit, dirty')
    _value = Float
    _error = Float

    fit = String
    fit_abbreviation = Property(depends_on='fit')
    fit_blocks=List
    error_type=String

    filter_outliers_dict = Dict

    regressor = Property(depends_on='xs, ys, fit, dirty, error_type')
    dirty = Event

    def __init__(self, dbresult=None, *args, **kw):

        if dbresult:
            self._value = dbresult.signal_
            self._error = dbresult.signal_err
        else:
            kw['unpack'] = True

        super(IsotopicMeasurement, self).__init__(*args, **kw)

    def set_fit_blocks(self, fit):
        if re.match(r'\([\w\d\s,]*\)', fit):
            fs=[]
            for m in re.finditer(r'\([\w\d\s,]*\)', fit):
                a=m.group(0)
                a=a[1:-1]
                s,e,f=map(str.strip, a.split(','))

                if s is '':
                    s=-1
                else:
                    s=int(s)

                if e is '':
                    e=Inf
                else:
                    e=int(e)

                fs.append((s,e,f))

            self.fit_blocks=fs
        else:
            self.fit=fit

    def get_fit(self, cnt):
        if self.fit_blocks:
            if cnt<0:
                return self.fit_blocks[-1][2]
            else:
                for s,e,f in self.fit_blocks:
                    if s<cnt<e:
                        return f
        else:
            return self.fit

    def set_fit(self, fit, notify=True):
        if fit is not None:
            self.filter_outliers_dict = dict(filter_outliers=bool(fit.filter_outliers),
                                             iterations=int(fit.filter_outlier_iterations),
                                             std_devs=int(fit.filter_outlier_std_devs))
            self.error_type=fit.error_type or 'SEM'
            self.trait_set(fit=fit.fit, trait_change_notify=notify)

    def set_uvalue(self, v):
        if isinstance(v, tuple):
            self._value, self._error = v
        else:
            self._value = v.nominal_value
            self._error = v.std_dev

        self.dirty = True

    def _mean_regressor_factory(self):
        reg = MeanRegressor(xs=self.xs, ys=self.ys,
                            filter_outliers_dict=self.filter_outliers_dict,
                            error_calc_type=self.error_type or 'SEM')
        return reg

    def _set_error(self, v):
        self._error = v

    def _set_value(self, v):
        self._value = v

    def _get_value(self):
        if len(self.xs) > 1:  # and self.ys is not None:
            v = self.regressor.predict(0)
            return v
        else:
            return self._value

    def _get_error(self):
        if len(self.xs) > 1:
            v = self.regressor.predict_error(0)
            return v
        else:
            return self._error

    @cached_property
    def _get_regressor(self):
        # print '{} getting regerssior'.format(self.name)
        # try:
        if self.fit.lower() =='average':
            reg = self._mean_regressor_factory()
        else:
            reg = PolynomialRegressor(xs=self.xs,
                                      ys=self.ys,
                                      degree=self.fit,
                                      error_calc_type=self.error_type,
                                      filter_outliers_dict=self.filter_outliers_dict)

        # except Exception, e:
        #     reg = PolynomialRegressor(xs=self.xs, ys=self.ys,
        #                               degree=self.fit,
        #                               filter_outliers_dict=self.filter_outliers_dict)

        reg.calculate()

        return reg

    @cached_property
    def _get_uvalue(self):
        return ufloat(self.value, self.error, tag=self.name)

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


class Baseline(IsotopicMeasurement):
    _kind = 'baseline'


class Sniff(BaseMeasurement):
    pass


class BaseIsotope(IsotopicMeasurement):
    baseline = Instance(Baseline, ())
    baseline_fit_abbreviation = Property(depends_on='baseline:fit')

    def get_baseline_corrected_value(self):
        nv = self.uvalue - self.baseline.uvalue.nominal_value
        return ufloat(nv.nominal_value, nv.std_dev, tag=self.name)

    def _get_baseline_fit_abbreviation(self):
        return fit_abbreviation(self.baseline.fit)


class Blank(BaseIsotope):
    pass


class Isotope(BaseIsotope):
    _kind = 'signal'

    blank = Instance(Blank, ())
    background = Instance(Background, ())
    sniff = Instance(Sniff, ())

    correct_for_blank = True
    ic_factor = Either(Variable, AffineScalarFunc)

    age_error_component = Float(0.0)
    temporary_ic_factor = None

    discrimination = Either(Variable, AffineScalarFunc)

    interference_corrected_value = Either(Variable, AffineScalarFunc)

    def get_interference_corrected_value(self):
        if self.interference_corrected_value is not None:
            return self.interference_corrected_value
        else:
            return ufloat(0, 0, tag=self.name)

    def get_intensity(self):
        """
            return the discrimination and ic_factor corrected value
        """
        return self.get_disc_corrected_value() * (self.ic_factor or 1.0)

    def get_disc_corrected_value(self):
        disc = self.discrimination
        if disc is None:
            disc = 1

        return self.get_corrected_value() * disc

    def ic_corrected_value(self):
        return self.get_corrected_value() * (self.ic_factor or 1.0)

    def get_corrected_value(self):
        v = self.get_baseline_corrected_value()

        if self.correct_for_blank:
            v = v - self.blank.uvalue

        return v - self.background.uvalue

    def set_blank(self, v, e):
        self.blank=Blank(_value=v, _error=e)

    def set_baseline(self, v, e):
        self.baseline=Baseline(_value=v, _error=e)

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
            return '{} {}'.format(self.name, self.get_baseline_corrected_value())
        except (OverflowError, ValueError, AttributeError, TypeError),e:
            return '{} {}'.format(self.name, e)
#============= EOF =============================================
