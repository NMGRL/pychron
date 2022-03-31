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
import logging
import os

from numpy import append as npappend
from traits.api import Property, Dict, Str
from traits.has_traits import HasTraits
from uncertainties import ufloat

from pychron.core.helpers.isotope_utils import sort_isotopes, convert_detector
from pychron.core.helpers.strtools import streq
from pychron.core.yaml import yload
from pychron.paths import paths
from pychron.processing.isotope import Isotope, Baseline

logger = logging.getLogger("ISO")


class IsotopeGroup(HasTraits):
    isotopes = Dict
    isotope_keys = Property
    conditional_modifier = None
    name = Str

    def keys(self):
        return list(self.isotopes.keys())

    def __getitem__(self, item):
        return self.isotopes[item]

    def iteritems(self):
        return self.isotopes.items()

    def itervalues(self):
        return self.isotopes.values()

    def values(self):
        return list(self.isotopes.values())

    def sorted_values(self, reverse=False):
        keys = self.isotope_keys
        if reverse:
            keys = reversed(keys)
        return [self.isotopes[k] for k in keys]

    def items(self):
        return list(self.isotopes.items())

    def pop(self, key):
        return self.isotopes.pop(key)

    def debug(self, msg, *args, **kw):
        self._log(logger.debug, msg)

    def info(self, msg, *args, **kw):
        self._log(logger.info, msg)

    def warning(self, msg, *args, **kw):
        self._log(logger.warning, msg)

    def critical(self, msg, *args, **kw):
        self._log(logger.critical, msg)

    def set_stored_value_states(self, state, save=True):
        if save:
            self.save_stored_value_state()

        for i in self.iter_isotopes():
            i.use_stored_value = state
            i.baseline.use_stored_value = state

    def revert_use_stored_values(self):
        if self._sv:
            for i, v in zip(self.iter_isotopes(), self._sv):
                i.use_stored_value = v[0]
                i.baseline.use_stored_value = v[1]

    _sv = None

    def save_stored_value_state(self):
        self._sv = [
            (i.use_stored_value, i.baseline.use_stored_value)
            for i in self.iter_isotopes()
        ]

    def iter_isotopes(self):
        return (self.isotopes[k] for k in self.isotope_keys)

    def clear_isotopes(self):
        for iso in self.iter_isotopes():
            self.isotopes[iso.name] = Isotope(iso.name, iso.detector)

    def get_baseline(self, attr):
        if attr.endswith("bs"):
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

    def map_isotope_key(self, k):
        return k

    def get_ratio(self, r, non_ic_corr=False):
        if "/" in r:
            n, d = r.split("/")
        else:
            n, d = r.split("_")
        n = self.map_isotope_key(n)
        d = self.map_isotope_key(d)
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
            iso = self.isotopes[attr]
        except KeyError:
            iso = next((i for i in self.itervalues() if i.detector == attr), None)

        if iso is not None:
            return iso.get_slope(n)
        else:
            return 0

    def get_baseline_value(self, attr):
        try:
            r = self.isotopes[attr].baseline.uvalue
        except KeyError:
            r = next(
                (
                    iso.baseline.uvalue
                    for iso in self.itervalues()
                    if iso.detector == attr
                ),
                None,
            )
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
        viso = next((i for i in self.itervalues() if i.name == iso), None)
        if viso is not None:
            return viso.get_intensity()
        else:
            return ufloat(0, 0, tag=iso)

    def get_ic_factor(self, det):
        # storing ic_factor in preferences causing issues
        # ic_factor stored in detectors.cfg

        p = os.path.join(paths.spectrometer_dir, "detectors.cfg")

        ic = 1, 0
        if os.path.isfile(p):
            from configparser import ConfigParser

            c = ConfigParser()
            c.read(p)
            det = det.lower()
            for si in c.sections():
                if si.lower() == det:
                    v, e = 1, 0
                    if c.has_option(si, "ic_factor"):
                        v = c.getfloat(si, "ic_factor")
                    if c.has_option(si, "ic_factor_err"):
                        e = c.getfloat(si, "ic_factor_err")
                    ic = v, e
                    break

        else:
            p = os.path.join(paths.spectrometer_dir, "detectors.yaml")
            if os.path.isfile(p):
                for i, di in enumerate(yload(p)):
                    if streq(di.get("name", ""), det):
                        v = di.get("ic_factor", 1)
                        e = di.get("ic_factor_err", 0)
                        ic = v, e
                        break
                else:
                    self.debug("no detector '{}' found in {}".format(det, p))
            else:
                self.debug("no detector file {}. cannot retrieve ic_factor".format(p))

        r = ufloat(*ic)
        return r

    def append_data(self, iso, det, x, signal, kind):
        """
        if kind is baseline then key used to match isotope is `detector` not an `isotope_name`
        """

        def _append(isotope):
            if kind in ("sniff", "baseline", "whiff"):
                if kind == "sniff":
                    isotope._value = signal
                    # isotope.dirty = True

                isotope = getattr(isotope, kind)

            if kind == "sniff":
                isotope._value = signal

            xs = npappend(isotope.xs, x)
            ys = npappend(isotope.ys, signal)
            isotope.xs = xs
            isotope.ys = ys
            # isotope.dirty = True

        isotopes = self.isotopes
        if kind == "baseline":
            ret = False
            # get the isotopes that match detector
            for i in self.itervalues():
                if i.detector == det:
                    _append(i)
                    ret = True
            return ret

        else:
            for i in ("{}{}".format(iso, det), iso):
                if i in isotopes:
                    _append(isotopes[i])
                    return True

    def clear_baselines(self):
        for k in self.isotopes:
            self.set_baseline(k, None, (0, 0))

    def clear_blanks(self):
        for k in self.isotopes:
            self.set_blank(k, None, (0, 0))

    def clear_error_components(self):
        for iso in self.itervalues():
            iso.age_error_component = 0

    def isotope_factory(self, **kw):
        return Isotope(**kw)

    def detectors(self):
        return [v.detector for k, v in self.isotopes.items()]

    def pairs(self):
        return [(k, v.name, v.detector) for k, v in self.isotopes.items()]

    def set_isotope_detector(self, det, add=False):
        det, name = det.name, det.isotope

        if name in self.isotopes:
            iso = self.isotopes[name]
            if add:
                if iso.detector != det:
                    nn = "{}{}".format(iso.name, iso.detector)
                    self.isotopes[nn] = iso

                    iso = Isotope(name, det)
                    name = "{}{}".format(name, det)
                    self.isotopes[name] = iso
        else:
            iso = Isotope(name, det)
            self.isotopes[name] = iso

        iso.detector = det
        iso.ic_factor = self.get_ic_factor(det)

    def get_baseline_corrected_value(self, iso, default=0):
        try:
            return self.isotopes[iso].get_baseline_corrected_value()
        except KeyError:
            if default is not None:
                return ufloat(default, 0, tag=iso)

    def get_isotopes_for_detector(self, det):
        det = convert_detector(det)

        for iso in self.itervalues():
            idet = convert_detector(iso.detector)
            if idet == det:
                yield iso

    def get_isotope_title(self, name, detector):
        iso = self.isotopes[name]
        title = name
        if iso.detector != detector:
            title = "{}{}".format(name, detector)
        return title

    def get_isotope(self, name=None, detector=None, kind=None):
        if name is None and detector is None:
            raise NotImplementedError("name or detector required")
        if detector and ":" in detector:
            name, detector = detector.split(":")

        iso = None
        if name:
            if ":" in name:
                name, detector = name.split(":")

            try:
                iso = self.isotopes[name]
                if detector:
                    if iso.detector != detector:
                        iso = next(
                            (
                                i
                                for i in self.itervalues()
                                if i.name == name and i.detector == detector
                            ),
                            None,
                        )
                        if not iso:
                            return
            except KeyError:
                if detector:
                    try:
                        iso = self.isotopes["{}{}".format(name, detector)]
                    except KeyError:
                        self.isotopes[name] = iso = Isotope(name, detector)
        else:
            iso = next(
                (iso for iso in self.itervalues() if iso.detector == detector), None
            )

        if iso:
            if kind == "sniff":
                iso = iso.sniff
            elif kind == "baseline":
                iso = iso.baseline
        return iso

    def set_isotope(self, iso, det, v, **kw):
        if iso not in self.isotopes:
            niso = Isotope(iso, det)
            self.isotopes[iso] = niso
        else:
            niso = self.isotopes[iso]

        niso.set_uvalue(v)
        for k, v in kw.items():
            setattr(niso, k, v)

        return niso

    def set_baseline(self, iso, detector, v):
        for iso in ("{}{}".format(iso, detector), iso):
            if iso in self.isotopes:
                self.debug("setting {} baseline {}".format(iso, v))
                self.isotopes[iso].baseline.set_uvalue(v)
                break

    def set_blank(self, iso, detector, v):
        for iso in ("{}{}".format(iso, detector), iso):
            if iso in self.isotopes:
                self.debug("setting {} blank {}".format(iso, v))
                self.isotopes[iso].blank.set_uvalue(v)
                break

    # private
    def _get_isotope_keys(self):
        keys = list(self.isotopes.keys())
        return sort_isotopes(keys)

    def _log(self, func, msg):
        func("{} - {}".format(self.name, msg))

    def __getattr__(self, attr):
        if "/" in attr:
            # treat as ratio
            n, d = attr.split("/")
            try:
                return self.get_value(n) / self.get_value(d)
            except (ZeroDivisionError, TypeError):
                return ufloat(0, 0)
        elif attr != "unit" and (attr.startswith("u") or attr in self.isotope_keys):
            return self.get_value(attr)
        else:
            raise AttributeError(attr)


# ============= EOF =============================================
