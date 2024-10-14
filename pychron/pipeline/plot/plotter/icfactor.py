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
# ============= standard library imports ========================
from __future__ import absolute_import

from logging import warning

from numpy import array
from six.moves import zip

# ============= local library imports  ==========================
from uncertainties import std_dev, nominal_value, ufloat, umath

from pychron.pipeline.plot.plotter.references_series import ReferencesSeries


class ICFactor(ReferencesSeries):
    # def set_interpolated_values(self, iso, reg, fit):
    # if self.options.use_source_correction:
    #     for a in self.sorted_analyses:
    #
    #         a.set_air_source_correction(r)
    # else:
    #     return super(ICFactor, self).set_interpolated_values(iso, reg, fit)
    # mi, ma = self._get_min_max()
    # # mi =
    # ans = self.sorted_analyses
    #
    # xs = [(ai.timestamp - ma) / self._normalization_factor for ai in ans]
    # p_uys = reg.predict(xs)
    # p_ues = reg.predict_error(xs)
    #
    # if p_ues is None or any(isnan(p_ues)) or any(isinf(p_ues)):
    #     p_ues = zeros_like(xs)
    #
    # if p_uys is None or any(isnan(p_uys)) or any(isinf(p_uys)):
    #     p_uys = zeros_like(xs)
    #
    # self._set_interpolated_values(iso, fit, ans, p_uys, p_ues)
    # return asarray(p_uys), asarray(p_ues)

    def _get_plot_label_text(self, po):
        n, d = po.name.split("/")

        analysis = self.sorted_references[0]

        niso = analysis.get_isotope(detector=n)
        if niso:
            n = niso.name

        diso = analysis.get_isotope(detector=d)
        if diso:
            d = diso.name

        return "{}/{}".format(n, d)

    def _get_interpolated_value(self, po, analysis):
        n, d = po.name.split("/")
        # iso = next((i for i in analysis.isotopes.itervalues() if i.detector == d), None)
        v, e = 0, 0
        if d in analysis.temporary_ic_factors:
            ticf = analysis.temporary_ic_factors[d]
            ic = ticf["value"]
            v, e = nominal_value(ic), std_dev(ic)

        return v, e

    def _set_interpolated_values(self, iso, fit, ans, p_uys, p_ues):
        n, d = iso.split("/")

        is_peak_hop = False
        for ai in self.references:
            dets = ai.detectors()

            # print("dets", dets, len(dets), len(set(dets)))
            # a detector is used more than once
            if len(dets) > len(set(dets)):
                is_peak_hop = True
                break

        # print("---------------- ispeakhop", is_peak_hop)
        for ui, v, e in zip(ans, p_uys, p_ues):
            if v is not None and e is not None:
                if self.options.use_source_correction:
                    # this is all hard coded stuff and would need to be
                    # made much more configurable in the future
                    # see comment in `set_beta`
                    m40 = 39.9624
                    m36 = 35.9675
                    ic = 1 / ufloat(v, e)
                    beta = umath.log(ic) / umath.log(m40 / m36)
                    ui.set_beta(n, beta, is_peak_hop)
                elif self.options.use_discrimination:
                    # assumes 40/36 discrimination
                    ui.set_discrimination(ufloat(v, e))
                else:
                    if d == "rad40":
                        iso = ui.get_isotope(name="Ar40")
                        d = iso.detector

                    ui.set_temporary_ic_factor(n, d, v, e)

    def _get_current_data(self, po):
        if "/" in po.name:
            n, d = po.name.split("/")
            nys = array([ri.get_ic_factor(n) for ri in self.sorted_analyses])
            dys = array([ri.get_ic_factor(d) for ri in self.sorted_analyses])
            return dys / nys
        else:
            return array([ri.get_value(po.name) for ri in self.sorted_analyses])

    def _get_reference_data(self, po):
        if "/" in po.name:
            n, d = po.name.split("/")
            if n in ("rad40",):
                nys = [ri.get_value(n) for ri in self.sorted_references]
            else:
                nys = [ri.get_isotope(detector=n) for ri in self.sorted_references]
                nys = array(
                    [ni.get_decay_corrected_value() for ni in nys if ni is not None]
                )

            if d in ("rad40",):
                dys = [ri.get_value(d) for ri in self.sorted_references]
            else:
                dys = [ri.get_isotope(detector=d) for ri in self.sorted_references]
                dys = array(
                    [di.get_decay_corrected_value() for di in dys if di is not None]
                )

            try:
                rys = nys / dys
            except ZeroDivisionError:
                warning(
                    None,
                    "The data you trying to fit is not complete. One or more analyses are missing "
                    "measurements for detector {}. Can not proceed".format(d),
                )
                return
        else:
            rys = array([ri.get_value(po.name) for ri in self.sorted_references])
        rys = rys / po.standard_ratio
        return self.sorted_references, self.rxs, rys


# ============= EOF =============================================
