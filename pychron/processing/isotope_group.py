# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import Property, Dict
# ============= standard library imports ========================
import os
from ConfigParser import ConfigParser
from uncertainties import ufloat
from numpy import hstack
# ============= local library imports  ==========================
from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.processing.isotope import Isotope, Baseline


class IsotopeGroup(Loggable):
    isotopes = Dict
    isotope_keys = Property
    conditional_modifier = None

    def clear_isotopes(self):
        for iso in self.isotopes:
            self.isotopes[iso] = Isotope(name=iso)

    def get_baseline(self, attr):
        if attr.endswith('bs'):
            attr = attr[:-2]

        if attr in self.isotopes:
            return self.isotopes[attr].baseline
        else:
            return Baseline()

    def has_attr(self, attr):
        if attr in self.computed:
            return True
        elif attr in self.isotopes:
            return True
        elif hasattr(self, attr):
            return True

    def get_current_intensity(self, attr):
        try:
            iso = self.isotopes[attr]
        except KeyError:
            return

        if self.conditional_modifier:
            try:
                iso = getattr(iso, self.conditional_modifier)
            except AttributeError:
                return
        return iso.ys[-1]

    def get_ratio(self, r, non_ic_corr=False):
        n, d = r.split('/')
        isos = self.isotopes

        if non_ic_corr:
            func = self.get_non_ic_corrected
        else:
            func = self.get_intensity

        if n in isos and d in isos:
            try:
                return func(n) / func(d)
            except ZeroDivisionError:
                pass

    def get_slope(self, attr, n=-1):
        try:
            r = self.isotopes[attr].get_slope(n)
        except KeyError:
            r = None
        return r

    def get_baseline_value(self, attr):
        try:
            r = self.isotopes[attr].baseline.uvalue
        except KeyError:
            r = None
        return r

    def get_values(self, attr, n):
        """
            return an array of floats

            attr: isotope key
            n: int, values from the end to slice off. e.g 10 means last 10 items in array
            return all values if n==-1
        """
        try:
            r = self.isotopes[attr].ys
            if not n == -1:
                r = r[-n:]
        except KeyError:
            r = None
        return r

    def get_non_ic_corrected(self, iso):
        try:
            return self.isotopes[iso].get_non_detector_corrected_value()
        except KeyError:
            return ufloat(0, 0, tag=iso)

    def get_intensity(self, iso):
        if iso in self.isotopes:
            return self.isotopes[iso].get_intensity()
        else:
            return ufloat(0, 0, tag=iso)

    def get_ic_factor(self, det):
        # storing ic_factor in preferences causing issues
        # ic_factor stored in detectors.cfg

        p = os.path.join(paths.spectrometer_dir, 'detectors.cfg')
        # factors=None
        ic = 1, 1e-20
        if os.path.isfile(p):
            c = ConfigParser()
            c.read(p)
            det = det.lower()
            for si in c.sections():
                if si.lower() == det:
                    v, e = 1, 1e-20
                    if c.has_option(si, 'ic_factor'):
                        v = c.getfloat(si, 'ic_factor')
                    if c.has_option(si, 'ic_factor_err'):
                        e = c.getfloat(si, 'ic_factor_err')
                    ic = v, e
                    break
        else:
            self.debug('no detector file {}. cannot retrieve ic_factor'.format(p))

        r = ufloat(*ic)
        return r

    def get_error_component(self, key):
        # for var, error in self.uage.error_components().items():
        #     print var.tag

        v = next((error for (var, error) in self.uage.error_components().items()
                  if var.tag == key), 0)

        ae = self.uage.std_dev
        if ae:
            return v ** 2 / ae ** 2 * 100
        else:
            return 0

    def append_data(self, iso, det, x, signal, kind):
        """
            if kind is baseline then key used to match isotope is `detector` not an `isotope_name`
        """

        def _append(isotope):
            if kind in ('sniff', 'baseline', 'whiff'):
                if kind == 'sniff':
                    isotope._value = signal
                    isotope.dirty = True

                isotope = getattr(isotope, kind)

            if kind == 'sniff':
                isotope._value = signal

            isotope.xs = hstack((isotope.xs, (x,)))
            isotope.ys = hstack((isotope.ys, (signal,)))
            isotope.dirty = True

        isotopes = self.isotopes
        if kind == 'baseline':
            ret = False
            #get the isotopes that match detector
            for i in isotopes.itervalues():
                if i.detector == det:
                    _append(i)
                    ret = True
            return ret

        else:
            for i in (iso, '{}{}'.format(iso, det)):
                if i in isotopes:
                    ii = isotopes[i]
                    _append(ii)
                    return True

    def clear_baselines(self):
        for k in self.isotopes:
            self.set_baseline(k, (0, 0))

    def clear_blanks(self):
        for k in self.isotopes:
            self.set_blank(k, (0, 0))

    def clear_error_components(self):
        for iso in self.isotopes.itervalues():
            iso.age_error_component = 0

    def isotope_factory(self, **kw):
        return Isotope(**kw)

    def set_isotope_detector(self, det, iso=None):
        name = None
        if iso:
            name = iso

        if not isinstance(det, str):
            name, det = det.isotope, det.name

        if name in self.isotopes:
            iso = self.isotopes[name]
        else:
            iso = Isotope(name, det)
            self.isotopes[name] = iso

        iso.detector = det
        iso.ic_factor = self.get_ic_factor(det)

    def get_baseline_corrected_value(self, iso):
        try:
            return self.isotopes[iso].get_baseline_corrected_value()
        except KeyError:
            return ufloat(0, 0, tag=iso)

    def get_isotopes(self, det):
        for iso in self.isotopes.itervalues():
            if iso.detector == det:
                yield iso

    def get_isotope(self, name=None, detector=None, kind=None):
        if name is None and detector is None:
            raise NotImplementedError('name or detector required')

        if name:
            try:
                iso = self.isotopes[name]
                if kind == 'sniff':
                    iso = iso.sniff
                elif kind == 'baseline':
                    iso = iso.baseline
                return iso
            except KeyError:
                pass
        else:
            attr = 'detector'
            value = detector
            return next((iso for iso in self.isotopes.itervalues()
                         if getattr(iso, attr) == value), None)

    def set_isotope(self, iso, v, det, **kw):
        # print 'set isotope', iso, v
        if iso not in self.isotopes:
            niso = Isotope(iso, det)
            self.isotopes[iso] = niso
        else:
            niso = self.isotopes[iso]

        niso.set_uvalue(v)
        for k,v in kw.iteritems():
            setattr(niso, k, v)
        # niso.trait_set(**kw)

        return niso

    def set_baseline(self, iso, v):
        if iso not in self.isotopes:
            niso = Isotope(name=iso)
            self.isotopes[iso] = niso

        self.isotopes[iso].baseline.set_uvalue(v)

    def set_blank(self, iso, v):
        if iso not in self.isotopes:
            niso = Isotope(name=iso)
            self.isotopes[iso] = niso

        self.debug('setting {} blank {}'.format(iso, v))
        self.isotopes[iso].blank.set_uvalue(v)

    # private
    def _get_iso_by_detector(self, det):
        return (i for i in self.isotopes if i.detector == det)

    def _get_isotope_keys(self):
        keys = self.isotopes.keys()
        return sort_isotopes(keys)

    def __getattr__(self, attr):
        if '/' in attr:
            # treat as ratio
            n, d = attr.split('/')
            try:
                return self.get_value(n) / self.get_value(d)
            except (ZeroDivisionError, TypeError):
                return ufloat(0, 1e-20)
        else:
            raise AttributeError(attr)
# ============= EOF =============================================



