# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import

from traits.api import List, HasTraits, Tuple

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.editors.figure_editor import FigureEditor


def bin_analyses(ans):
    ans = iter(sorted(ans, key=lambda x: x.timestamp))

    def _bin():
        ai = next(ans)
        pt = ai.timestamp
        g = [ai]
        tol = 60 * 60
        while 1:
            try:
                ai = next(ans)
                dev = ai.timestamp - pt
                pt = ai.timestamp
                if dev > tol:
                    yield g
                    g = [ai]
                else:
                    g.append(ai)

            except StopIteration:
                break

        yield g

    return _bin()


def get_bounds(groups):
    bs = []
    for i, gi in enumerate(groups):

        try:
            gii = groups[i + 1]
        except IndexError:
            break

        ua = gi[-1].timestamp
        bi = (gii[0].timestamp - ua) / 2.0 + ua
        bs.append(bi)

    return bs


class BinGroup(HasTraits):
    unknowns = List
    references = List
    bounds = Tuple


class InterpolationEditor(FigureEditor):

    def set_references(self, refs):
        self.clear_aux_plot_limits()
        self.references = refs

# ============= EOF =============================================
