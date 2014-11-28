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

#============= enthought library imports =======================
from pychron.core.helpers.formatting import floatfmt, format_percent_error
from pychron.graph.tools.info_inspector import InfoInspector, InfoOverlay
#============= standard library imports ========================
#============= local library imports  ==========================


class RegressionInspectorTool(InfoInspector):
    def assemble_lines(self):
        reg = self.component.regressor

        v, e = reg.predict(0), reg.predict_error(0)
        lines = [reg.make_equation(),
                 'x=0, y={} +/-{}({}%)'.format(floatfmt(v, n=5),
                                               floatfmt(e, n=5),
                                               format_percent_error(v, e))]

        if not reg.mswd in ('NaN', None):
            valid = '' if reg.valid_mswd else '*'
            lines.append('MSWD= {}{}, n={}'.format(valid,
                                                   floatfmt(reg.mswd, n=3), reg.n))

        lines.extend(map(unicode.strip, map(unicode, reg.tostring().split(','))))

        return lines

class RegressionInspectorOverlay(InfoOverlay):
    pass

# ============= EOF =============================================
