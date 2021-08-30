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
from pychron.core.helpers.formatting import floatfmt, format_percent_error, errorfmt
from pychron.core.regression.mean_regressor import MeanRegressor, WeightedMeanRegressor
from pychron.graph.tools.info_inspector import InfoInspector, InfoOverlay
from pychron.pychron_constants import PLUSMINUS


def make_correlation_statistics(reg):
    lines = ['R\u00b2={}, R\u00b2-Adj.={}'.format(floatfmt(reg.rsquared), floatfmt(reg.rsquared_adj))]
    return lines


def make_statistics(reg, x=None, options=None):
    if options is None:
        options = {}

    display_min_max = options.get('display_min_max', True)

    v, e = reg.predict(0), reg.predict_error(0)

    lines = [reg.make_equation(),
             'x=0, y={} {}{}'.format(floatfmt(v, n=6),
                                          PLUSMINUS,
                                          errorfmt(v, e))]
    if x is not None:
        vv, ee = reg.predict(x), reg.predict_error(x)

        lines.append('x={:0.5f}, y={} {} {}'.format(x, floatfmt(vv, n=6), PLUSMINUS, errorfmt(vv, ee)))

    if reg.mswd not in ('NaN', None):
        lines.append('Fit MSWD={}, N={}'.format(reg.format_mswd(), reg.n))

    if display_min_max:
        mi, ma = reg.min, reg.max
        lines.append('Min={}, Max={}, Dev={}%'.format(floatfmt(mi),
                                                      floatfmt(ma),
                                                      floatfmt((ma - mi) / ma * 100, n=2)))

    d = {'mean': floatfmt(reg.mean),
         'std': floatfmt(reg.std),
         'sem': floatfmt(reg.sem),
         'n': reg.n}

    if isinstance(reg, WeightedMeanRegressor):
        fmt = 'Wtd. Mean={mean:}, SD={std:}, SEWM={sem:}, N={n:}'
    else:
        fmt = 'Mean={mean:}, SD={std:}, SEM={sem:}, N={n:}'

    lines.append(fmt.format(**d))

    mean_mswd = reg.mean_mswd
    if mean_mswd is not None:
        lines.append('Mean MSWD={}'.format(reg.format_mswd(mean=True)))

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
