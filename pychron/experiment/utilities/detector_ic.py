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
from __future__ import absolute_import
import csv
import os

from traits.api import HasTraits, Str, Float

# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.core.helpers.filetools import add_extension
from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.strtools import streq
from pychron.paths import paths
from pychron.pychron_constants import DETECTOR_ORDER, PLUSMINUS_ONE_SIGMA


class RatioItem(HasTraits):
    name = Str
    refvalue = 1.0
    intensity = Str
    intensity_err = Str

    def add_ratio(self, detector, v):
        v /= self.refvalue
        # v = x.get_non_detector_corrected_value() / self.refvalue
        # print 'asfasfd', self.name, x.detector, nominal_value(v)
        # self.add_trait(x.detector, Float(round(nominal_value(v), 5)))
        # self.add_trait('{}_err'.format(x.detector), Float(round(std_dev(v), 5)))
        self.add_trait(detector, Float(nominal_value(v)))
        self.add_trait("{}_err".format(detector), Float(std_dev(v)))

    def to_row(self):
        vs = [self.name, self.intensity, self.intensity_err]
        for det in DETECTOR_ORDER:
            try:
                v = getattr(self, det)
                ve = getattr(self, "{}_err".format(det))
                vs.append(v)
                vs.append(ve)
            except AttributeError:
                vs.append(0)
                vs.append(0)
        return vs


def make_items(isotopes):
    items = []
    for di in DETECTOR_ORDER:
        ai = next((aii for aii in isotopes if aii.detector.upper() == di), None)
        if ai:
            rv = ai.get_non_detector_corrected_value()
            r = RatioItem(
                name=ai.detector,
                refvalue=rv,
                intensity=floatfmt(nominal_value(rv)),
                intensity_err=floatfmt(std_dev(rv)),
            )
            for dj in DETECTOR_ORDER:
                bi = next(
                    (aii for aii in isotopes if aii.detector.upper() == dj),
                    None,
                )
                if bi:
                    r.add_ratio(bi.detector, bi.get_non_detector_corrected_value())

            items.append(r)
    return items


def save_csv(record_id, items):
    path = os.path.join(paths.data_det_ic_dir, add_extension(record_id, ".csv"))
    with open(path, "w") as wfile:
        wrt = csv.writer(wfile, delimiter="\t")

        ds = [(det, "{}_err".format(det)) for det in DETECTOR_ORDER]
        ds = [dj for di in ds for dj in di]
        wrt.writerow(["#det", "intensity", "err"] + ds)
        for i in items:
            wrt.writerow(i.to_row())
    return path


def get_columns(isos):
    def closure():
        for det in DETECTOR_ORDER:
            iso = next((iso for iso in isos if streq(iso.detector, det)), None)
            if iso:
                yield det, iso.detector
                yield PLUSMINUS_ONE_SIGMA, "{}_err".format(det)

    return list(closure())


# ============= EOF =============================================
