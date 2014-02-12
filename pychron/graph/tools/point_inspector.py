#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Callable
#============= standard library imports ========================
from numpy import where
#============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.graph.tools.info_inspector import InfoInspector, InfoOverlay


class PointInspector(InfoInspector):
    convert_index = Callable
    #    def _build_metadata(self, xy):
    #        point = self.component.hittest(xy)
    #        md = dict(point=point)
    #        return md
    def get_selected_index(self):
        xxyy = self.component.hittest(self.current_position)

        if xxyy:
            x, _ = self.component.map_data((xxyy))
            d = self.component.index.get_data()
            tol = 0.001
            return where(abs(d - x) < tol)[0]

    def percent_error(self, s, e):
        v ='(Inf%)'
        try:
            return '({:0.2f}%)'.format(abs(e / s) * 100)
        except ZeroDivisionError:
            pass
        return v

    def assemble_lines(self):
        pt = self.current_position
        if pt:
            x, y = self.component.map_data(pt)
            if self.convert_index:
                x = self.convert_index(x)
            else:
                x = '{:0.5f}'.format(x)

            inds = self.get_selected_index()
            lines=[]
            if inds is not None:
                he = hasattr(self.component, 'yerror')
                for i in inds:
                    if he:
                        ye = self.component.yerror.get_data()[i]
                        pe = self.percent_error(y, ye)

                        # fmt = '{:0.3e}' if abs(ye) < 10e-6 else '{:0.6f}'
                        # ye = fmt.format(ye)

                        # fmt = '{:0.3e}' if abs(y) < 10e-6 else '{:0.6f}'
                        # y = fmt.format(y)
                        ye = floatfmt(ye, n=6, s=3)
                        y = u'{} {}{} ({})'.format(y, '+/-', ye, pe)
                    else:
                        y = floatfmt(y, n=6, s=3)

                    lines.extend([u'x= {}'.format(x), u'y= {}'.format(y)])
                    if hasattr(self.component, 'display_index'):
                        x = self.component.display_index.get_data()[i]
                        lines.append(u'{}'.format(x))
                        # lines = [u'{}'.format(x)] + lines
            # else:
            #     lines = [u'x= {}'.format(x), u'y= {}'.format(y)]

            # if inds is not None and hasattr(self.component, 'display_index'):
            #     x = self.component.display_index.get_data()[ind][0]
            #     lines = [u'{}'.format(x)] + lines

            return lines
        else:
            return []


class PointInspectorOverlay(InfoOverlay):
    pass

#            print comp
#============= EOF =============================================
