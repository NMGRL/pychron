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
from itertools import groupby

from traits.api import List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.panels.figure_panel import FigurePanel


class ReferencesPanel(FigurePanel):
    references = List

    def _make_figures(self):
        gs = super(ReferencesPanel, self)._make_figures()

        key = lambda x: x.group_id
        refs = sorted(self.references, key=key)
        gg = groupby(refs, key=key)
        for gi in gs:
            try:
                _, refs = gg.next()
                gi.references = list(refs)
            except StopIteration:
                break

        return gs

# ============= EOF =============================================
