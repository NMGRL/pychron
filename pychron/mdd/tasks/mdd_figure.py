# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import Enum

from pychron.mdd.tasks.mdd_views import VIEWS
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options import FigureOptions
from pychron.pychron_constants import NULL_STR, MAIN, APPEARANCE

PANELS = [NULL_STR, 'Arrhenius', 'LogR Ro', 'Spectrum', 'Cooling History']


def make_panel(p):
    if p == 'Arrhenius':
        ret = ('Arrhenius', 'Model Arrhenius')
    elif p == 'Spectrum':
        ret = ('Spectrum', 'Model Spectrum')
    else:
        ret = (p,)
    return ret


class MDDFigureOptions(FigureOptions):

    panel_ul = Enum(*PANELS)
    panel_ur = Enum(*PANELS)
    panel_ll = Enum(*PANELS)
    panel_lr = Enum(*PANELS)

    def initialize(self):
        self.subview_names = [MAIN, APPEARANCE]

    def panels(self):
        ps = self.panel_ul, self.panel_ur, self.panel_ll, self.panel_lr
        return [(i, make_panel(p)) for i, p in enumerate(ps) if not p == NULL_STR]

    def rc(self):
        kind, n, r, c = 'g', 4, 2, 2

        if (self.panel_ul == NULL_STR and self.panel_ur == NULL_STR) or \
                (self.panel_ll == NULL_STR and self.panel_lr == NULL_STR):
            r = 1
            kind = 'h'
            n = 2

        if self.panel_ul == NULL_STR and self.panel_ll == NULL_STR or \
                self.panel_ur == NULL_STR and self.panel_lr == NULL_STR or \
                self.panel_ur == NULL_STR and self.panel_ll == NULL_STR:
            c = 1
            kind = 'v'
            n = 2

        return kind, n, r, c

    def _get_subview(self, name):
        return VIEWS[name]

    def _panel_ul_default(self):
        return 'Spectrum'

    def _panel_ur_default(self):
        return 'LogR Ro'

    def _panel_ll_default(self):
        return 'Arrhenius'

    def _panel_lr_default(self):
        return 'Cooling History'

# ============= EOF =============================================
