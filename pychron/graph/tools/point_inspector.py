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
from traits.api import Callable
# ============= standard library imports ========================
from numpy import where, vstack
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.graph.tools.info_inspector import InfoInspector, InfoOverlay
from pychron.pychron_constants import PLUSMINUS


class PointInspector(InfoInspector):
    convert_index = Callable
    additional_info = Callable

    single_point = True

    def get_selected_index(self, threshold=5):
        if self.single_point:
            idx = self.component.map_index(self.current_position, threshold=threshold)
            if idx is not None:
                return (idx,)
        else:
            xs = self.component.index.get_data()
            ys = self.component.value.get_data()

            d = vstack((xs, ys)).T
            spts = self.component.map_screen(d)

            cx, cy = self.current_position
            distances = ((spts[:, 0] - cx) ** 2 + (spts[:, 1] - cy) ** 2) ** 0.5
            return where(distances <= threshold * 2)[0]

    def percent_error(self, s, e):
        v = '(Inf%)'
        try:
            return '({:0.2f}%)'.format(abs(e / s) * 100)
        except ZeroDivisionError:
            pass
        return v

    def assemble_lines(self):
        pt = self.current_position
        if pt:
            # x, y = self.component.map_data(pt)

            comp = self.component
            inds = self.get_selected_index()
            lines = []
            convert_index = self.convert_index
            if inds is not None:
                he = hasattr(self.component, 'yerror')

                ys = comp.value.get_data()[inds]
                xs = comp.index.get_data()[inds]
                for i, x, y in zip(inds, xs, ys):
                    if he:
                        ye = comp.yerror.get_data()[i]
                        pe = self.percent_error(y, ye)

                        ye = floatfmt(ye, n=6, s=3)
                        sy = u'{} {}{} ({})'.format(y, PLUSMINUS, ye, pe)
                    else:
                        sy = floatfmt(y, n=6, s=3)

                    if convert_index:
                        x = convert_index(x)
                    else:
                        x = '{:0.5f}'.format(x)

                    lines.extend([u'pt={:03d}, x= {}, y= {}'.format(i + 1, x, sy)])
                    if hasattr(comp, 'display_index'):
                        x = comp.display_index.get_data()[i]
                        lines.append('{}'.format(x))

                    if self.additional_info is not None:
                        ad = self.additional_info(i)
                        if isinstance(ad, (list, tuple)):
                            lines.extend(ad)
                        else:
                            lines.append(ad)

            return lines
            # delim_n = max([len(li) for li in lines])
            # return intersperse(lines, '-' * delim_n)
        else:
            return []


class PointInspectorOverlay(InfoOverlay):
    pass

# print comp
# ============= EOF =============================================
