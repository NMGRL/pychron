# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt, format_percent_error
from pychron.core.regression.mean_regressor import MeanRegressor
from pychron.graph.tools.info_inspector import InfoInspector, InfoOverlay
from pychron.pychron_constants import PLUSMINUS

def make_correlation_statistics(reg):
    lines = ['R\u00b2={}, R\u00b2-Adj.={}'.format(floatfmt(reg.rsquared), floatfmt(reg.rsquared_adj))]
    return lines


def make_statistics(reg, x=None):
    v, e = reg.predict(0), reg.predict_error(0)

    lines = [reg.make_equation(),
             'x=0, y={} {}{}({}%)'.format(floatfmt(v, n=6),
                                          PLUSMINUS,
                                          floatfmt(e, n=6),
                                          format_percent_error(v, e))]
    if x is not None:
        vv, ee = reg.predict(x), reg.predict_error(x)

        lines.append('x={}, y={} +/-{}({}%)'.format(x, floatfmt(vv, n=6),
                                                    floatfmt(ee, n=6),
                                                    format_percent_error(vv, ee)))

    if reg.mswd not in ('NaN', None):
        valid = '' if reg.valid_mswd else '*'
        lines.append('Fit MSWD= {}{}, N={}'.format(valid,
                                               floatfmt(reg.mswd, n=3), reg.n))

    mi, ma = reg.min, reg.max
    lines.append('Min={}, Max={}, Dev={}%'.format(floatfmt(mi),
                                                  floatfmt(ma),
                                                  floatfmt((ma - mi) / ma * 100, n=2)))

    lines.append('Mean={}, SD={}, SEM={}, N={}'.format(floatfmt(reg.mean), floatfmt(reg.std),
                                                       floatfmt(reg.sem), reg.n))

    mean_mswd = reg.mean_mswd
    if mean_mswd is not None:
        valid = '' if reg.valid_mean_mswd else '*'
        lines.append('Mean MSWD= {}{}'.format(valid, floatfmt(reg.mean_mswd, n=3)))

    if not isinstance(reg, MeanRegressor):
        lines.append('R\u00b2={}, R\u00b2-Adj.={}'.format(floatfmt(reg.rsquared), floatfmt(reg.rsquared_adj)))
        lines.extend([l.strip() for l in reg.tostring().split(',')])
    return lines


class RegressionInspectorTool(InfoInspector):
    def assemble_lines(self):
        lines = []
        if self.current_position:
            reg = self.component.regressor
            x = self.current_position[0]
            lines = make_statistics(reg, x=x)
        return lines


class RegressionInspectorOverlay(InfoOverlay):
    pass

# ============= EOF =============================================
