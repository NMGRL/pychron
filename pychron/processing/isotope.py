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
from binascii import hexlify
from itertools import izip
import struct
import re

from uncertainties import ufloat
from numpy import array, Inf, polyfit




# ============= local library imports  ==========================
from pychron.core.helpers.fits import natural_name_fit, fit_to_degree
from pychron.core.regression.mean_regressor import MeanRegressor


def fit_abbreviation(fit, ):
    f = ''
    if fit:
        f = fit[0].upper()
    return f


class BaseMeasurement(object):
    # xs = Array
    # ys = Array
    # xs = None
    # ys = None

    # n = Property(depends_on='xs')
    # _n = Int
    # name = Str
    # mass = Float
    # detector = Str

    unpack_error = None
    endianness = '>'
    reverse_unpack = False
    # time_zero_offset = Float
    # offset_xs = Property

    # __slots__ = ['xs', 'ys', 'n', 'name', 'mass', 'detector', 'time_zero_offset']
    @property
    def n(self):
        return self.xs.shape[0]

    @property
    def offset_xs(self):
        return self.xs - self.time_zero_offset

    def __init__(self, name, detector):
        self.name = name
        self.detector = detector
        self.xs, self.ys = array([]), array([])
        self.mass = 0
        self.time_zero_offset = 0

        # def __init__(self, dbrecord=None, unpack=False, unpacker=None, *args, **kw):
        # super(BaseMeasurement, self).__init__(*args, **kw)
        # if dbrecord and unpack:
        #     if unpacker is None:
        #         unpacker = lambda x: x.signal.data
        #
        #     blob = unpacker(dbrecord)
        #     self.unpack_data(blob)

    def pack(self, endianness=None, as_hex=True):
        if endianness is None:
            endianness = self.endianness

        fmt = '{}ff'.format(endianness)
        txt = ''.join((struct.pack(fmt, x, y) for x, y in izip(self.xs, self.ys)))
        if as_hex:
            txt = hexlify(txt)
        return txt

    def unpack_data(self, blob):
        try:
            xs, ys = self._unpack_blob(blob)
        except (ValueError, TypeError, IndexError, AttributeError), e:
            self.unpack_error = e
            print e
            return

        self.xs = array(xs)
        self.ys = array(ys)
        # print self.name, self.xs.shape, self.ys.shape
        # print self.name, self.ys

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

    # def _get_n(self):
    #     if not self._n:
    #         return len(self.xs)
    #     else:
    #         return self._n

    # def _set_n(self, v):
    #     self._n = v
    #
    # def _get_offset_xs(self):
    #     return self.xs - self.time_zero_offset

    def get_slope(self, n):
        if self.xs.shape[0] and self.ys.shape[0] and self.xs.shape[0] == self.ys.shape[0]:
            xs = self.xs
            ys = self.ys
            if n != -1:
                xs = xs[-n:]
                ys = ys[-n:]

            return polyfit(xs, ys, 1)[0]


class IsotopicMeasurement(BaseMeasurement):
    # uvalue = Property(depends_on='dirty')  # depends_on='value, error, _value, _error, dirty')

    # value = Property(depends_on='_value, dirty')
    # error = Property(depends_on='_error, dirty')
    # value = Property(Float(enter_set=True, auto_set=False),
    # depends_on='dirty')
    # error = Property(Float(enter_set=True, auto_set=False),
    #                  depends_on='dirty')
    _value = 0
    _error = 0
    _regressor = None

    # _uvalue = None
    _fit = None
    # _fit = String
    # fit_abbreviation = Property(depends_on='dirty')
    fit_blocks = None
    error_type = None
    #
    filter_outliers_dict = None
    #
    # regressor = Property(depends_on='fit, time_zero_offset, dirty')
    # # regressor = Property(depends_on='fit, dirty, error_type')
    include_baseline_error = False
    #
    use_static = False
    user_defined_value = False
    user_defined_error = False

    _oerror = None
    _ovalue = None
    _dirty = False

    # __slots__ = ['_fit', '_value', '_error', 'filter_outliers_dict',
    # 'include_baseline_error',
    # '_ovalue', '_oerror',
    #              'include_baseline_error', 'use_static',
    #              'user_defined_value',
    #              'user_defined_error', 'fit_blocks', 'error_type']

    # def __init__(self, dbresult=None, *args, **kw):

    # if dbresult:
    #     self._value = dbresult.signal_
    #     self._error = dbresult.signal_err
    # else:
    #     kw['unpack'] = True

    # super(IsotopicMeasurement, self).__init__(*args, **kw)

    # @property
    # def uvalue(self):
    #     return ufloat((1,0))

    def __init__(self, *args, **kw):
        super(IsotopicMeasurement, self).__init__(*args, **kw)
        self.filter_outliers_dict = dict()

    def set_filtering(self, d):
        self.filter_outliers_dict = d.copy()
        # self.dirty = True
        # print self.filter_outliers_dict
        # self.regressor.filter_outliers_dict=self.filter_outliers_dict
        # self.regressor.calculate()

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

        if re.match(r'\([\w\d\s,]*\)', fit):
            fs = []
            for m in re.finditer(r'\([\w\d\s,]*\)', fit):
                a = m.group(0)
                a = a[1:-1]
                s, e, f = map(str.strip, a.split(','))

                if s is '':
                    s = -1
                else:
                    s = int(s)

                if e is '':
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

    def set_filter_outliers_dict(self, filter_outliers=True, iterations=1, std_devs=2, notify=True):
        self.filter_outliers_dict = {'filter_outliers': filter_outliers,
                                     'iterations': iterations,
                                     'std_devs': std_devs}
        self._dirty = notify

    def attr_set(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def set_fit(self, fit, notify=True):
        if fit is not None:
            self.user_defined_value = False
            self.user_defined_error = False

            if isinstance(fit, (int, str, unicode)):
                self.attr_set(fit=fit)
            else:

                self.filter_outliers_dict = dict(filter_outliers=bool(fit.filter_outliers),
                                                 iterations=int(fit.filter_outlier_iterations or 0),
                                                 std_devs=int(fit.filter_outlier_std_devs or 0))
                # self.error_type=fit.error_type or 'SEM'
                self.attr_set(fit=fit.fit,
                              time_zero_offset=fit.time_zero_offset or 0,
                              error_type=fit.error_type or 'SEM',
                              include_baseline_error=fit.include_baseline_error or False)
                if self._regressor:
                    self._regressor.error_calc_type = self.error_type
                    # self.include_baseline_error = fit.include_baseline_error or False

                    # self._value = 0
                    # self._error = 0
            if notify:
                self._dirty = True

    def set_uvalue(self, v):
        if isinstance(v, tuple):
            self._value, self._error = v

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
        if self.use_static and self._value:
            return self._value
        elif self.user_defined_value:
            return self._value

        if self.xs.shape[0] > 1:
            # print 'useing regressor'
            v = self.regressor.predict(0)
            # print 'using regressor', self.regressor, v
            return v
        else:
            return self._value

    @property
    def error(self):
        if self.use_static and self._error:
            return self._error
        elif self.user_defined_error:
            return self._error

        if self.xs.shape[0] > 1:
            v = self.regressor.predict_error(0)
            return v
        else:
            return self._error

    @error.setter
    def error(self, v):
        self.user_defined_error = True
        try:
            self._oerror = self._error
            self._error = float(v)
        except ValueError:
            pass

    @value.setter
    def value(self, v):
        self.user_defined_value = True
        try:
            self._ovalue = self._value
            self._value = float(v)
        except ValueError:
            pass

    def _mean_regressor_factory(self):
        # from pychron.core.regression.mean_regressor import MeanRegressor

        xs = self.offset_xs
        reg = MeanRegressor(xs=xs, ys=self.ys,
                            filter_outliers_dict=self.filter_outliers_dict,
                            error_calc_type=self.error_type or 'SEM')
        return reg

    @property
    def regressor(self):
        # print self.name, self.fit, self.__class__.__name__
        is_mean = 'average' in self.fit.lower()
        reg = self._regressor
        if reg is None:
            if is_mean:
                reg = self._mean_regressor_factory()
            else:
                # print 'doing import of regressor {}'.format(self.__class__)
                # st=time.time()
                from pychron.core.regression.ols_regressor import PolynomialRegressor
                # print 'doing import of regressor {}'.format(time.time()-st)

                reg = PolynomialRegressor(tag=self.name,
                                          xs=self.offset_xs,
                                          ys=self.ys,
                                          # fit=self.fit,
                                          # filter_outliers_dict=self.filter_outliers_dict,
                                          error_calc_type=self.error_type)
        elif is_mean and not isinstance(reg, MeanRegressor):
            reg = self._mean_regressor_factory()

        if not is_mean:
            reg.set_degree(fit_to_degree(self.fit), refresh=False)
        reg.filter_outliers_dict = self.filter_outliers_dict
        self._regressor = reg
        reg.calculate()
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
        return '{}{}'.format(fit_abbreviation(self.fit),
                             '*' if self.filter_outliers_dict.get('filter_outliers') else '')

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
    _kind = 'baseline'


class Sniff(BaseMeasurement):
    pass


class Whiff(BaseMeasurement):
    pass


class BaseIsotope(IsotopicMeasurement):
    baseline = None
    # baseline_fit_abbreviation = Property(depends_on='baseline:fit')

    @property
    def baseline_fit_abbreviation(self):
        if self.baseline:
            return self.baseline.fit_abbreviation
        else:
            return ''

    def __init__(self, name, detector):
        IsotopicMeasurement.__init__(self, name, detector)
        self.baseline = Baseline(name, detector)

    def get_baseline_corrected_value(self):
        b = self.baseline.uvalue
        if not self.include_baseline_error:
            b = b.nominal_value
            nv = self.uvalue - b
            return ufloat(nv.nominal_value, nv.std_dev, tag=self.name)
        else:
            return self.uvalue - b

    def _get_baseline_fit_abbreviation(self):
        return self.baseline.fit_abbreviation


class Blank(BaseIsotope):
    pass


class Isotope(BaseIsotope):
    _kind = 'signal'

    # blank = Instance(Blank)
    # background = Instance(Background)
    # sniff = Instance(Sniff)
    temporary_blank = None
    ic_factor = None
    correct_for_blank = True
    # ic_factor = Either(Variable, AffineScalarFunc)

    age_error_component = 0.0
    # temporary_ic_factor = None
    # temporary_blank = Instance(Blank)
    decay_corrected = None

    discrimination = None
    interference_corrected_value = None

    def __init__(self, name, detector):
        BaseIsotope.__init__(self, name, detector)
        self.blank = Blank(name, detector)
        self.sniff = Sniff(name, detector)
        self.background = Background(name, detector)

    def get_filtered_data(self):
        return self.regressor.calculate_filtered_data()

    def revert_user_defined(self):
        self.blank._revert_user_defined()
        self.baseline._revert_user_defined()
        self._revert_user_defined()

    def get_decay_corrected_value(self):
        if self.decay_corrected is not None:
            return self.decay_corrected
        else:
            return self.get_interference_corrected_value()

    def get_interference_corrected_value(self):
        if self.interference_corrected_value is not None:
            return self.interference_corrected_value
        else:
            return ufloat(0, 0, tag=self.name)

    def get_intensity(self):
        """
            return the discrimination and ic_factor corrected value
        """
        # st=time.time()
        v = self.get_disc_corrected_value() * (self.ic_factor or 1.0)

        # this is a temporary hack for handling Minna bluff data
        if self.detector.lower() == 'faraday':
            v = v - self.blank.uvalue
        # print self.name, time.time()-st
        return v

    def get_disc_corrected_value(self):
        disc = self.discrimination
        if disc is None:
            disc = 1

        return self.get_non_detector_corrected_value() * disc

    def get_ic_corrected_value(self):
        return self.get_non_detector_corrected_value() * (self.ic_factor or 1.0)

    def get_non_detector_corrected_value(self):
        v = self.get_baseline_corrected_value()

        # this is a temporary hack for handling Minna bluff data
        if self.correct_for_blank and self.detector.lower() != 'faraday':
            v = v - self.blank.uvalue

        if self.background:
            v = v - self.background.uvalue

        return v

    def set_blank(self, v, e):
        self.blank = Blank(_value=v, _error=e)

    def set_baseline(self, v, e):
        self.baseline = Baseline(_value=v, _error=e)

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
            return '{} {}'.format(self.name, self.get_baseline_corrected_value())
        except (OverflowError, ValueError, AttributeError, TypeError), e:
            return '{} {}'.format(self.name, e)

# ============= EOF =============================================
