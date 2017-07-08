# ===============================================================================
# Copyright 2017 ross
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
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.plot.plotter.series import UAR4038, UAR4036, UAR4039, AR4039, AR4036, AR4038, AGE, \
    RADIOGENIC_YIELD, PEAK_CENTER, ANALYSIS_TYPE, LAB_HUM, LAB_TEMP
from pychron.pipeline.report_writer import ReportWriter, ReportOptions
from pychron.pychron_constants import AR40, AR39, AR36, AR38, UNKNOWN, COCKTAIL, DETECTOR_IC


class ReportNode(BaseNode):
    name = 'ReportNode'
    options_klass = ReportOptions

    def configure(self, *args, **kw):

        self._configure_hook()

        ret = super(ReportNode, self).configure(*args, **kw)
        self.options.dump(verbose=True)
        return ret

    def _configure_hook(self):
        names = []
        if self.unknowns:
            names = []
            for unk in self.unknowns:
                iso_keys = unk.isotope_keys

                if iso_keys:

                    if AR40 in iso_keys and AR40 not in names:
                        if AR39 in iso_keys:
                            names.extend([AR4039, UAR4039])
                        if AR36 in iso_keys:
                            names.extend([AR4036, UAR4036])
                        if AR38 in iso_keys:
                            names.extend([AR4038, UAR4038])

                    for k in iso_keys:
                        if k not in names:
                            names.append(k)
                            names.append('{}bs'.format(k))
                            names.append('{}ic'.format(k))
                    
                    # names.extend(iso_keys)
                    # names.extend(['{}bs'.format(ki) for ki in iso_keys])
                    # names.extend(['{}ic'.format(ki) for ki in iso_keys])

                    if unk.analysis_type in (UNKNOWN, COCKTAIL):
                        if AGE not in names:
                            names.append(AGE)
                        if RADIOGENIC_YIELD not in names:
                            names.append(RADIOGENIC_YIELD)

                    if unk.analysis_type in (DETECTOR_IC,):
                        isotopes = unk.isotopes
                        for vi in isotopes.values():
                            for vj in isotopes.values():
                                if vi == vj:
                                    continue
                                k = '{}/{} DetIC'.format(vj.detector, vi.detector)
                                if k not in names:
                                    names.append(k)

        names.extend([PEAK_CENTER, ANALYSIS_TYPE, LAB_TEMP, LAB_HUM])
        self.options.set_names(names)

    # def pre_run(self, state, configure=True):
    #     if not self.auto_configure:
    #         return True
    #
    #     if self._manual_configured:
    #         return True
    #     if state.unknowns:
    #         self.unknowns = state.unknowns
    #     if state.references:
    #         self.references = state.references
    #
    #     if configure:
    #         if self.skip_configure:
    #             return True
    #
    #         if self.configure(refresh=False, pre_run=True):
    #             return True
    #         else:
    #             state.canceled = True
    #     else:
    #         return True

    def run(self, state):
        ans = state.unknowns
        r = ReportWriter()
        r.options = self.options
        r.make_report(ans)



# ============= EOF =============================================
