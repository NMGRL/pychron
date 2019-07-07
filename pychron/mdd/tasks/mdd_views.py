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
from traitsui.api import View, HGroup, VGroup, UItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options import AppearanceSubOptions, SubOptions


class MDDFigureAppearanceOptions(AppearanceSubOptions):
    pass


class MDDFigureMainOptions(SubOptions):
    def traits_view(self):
        r1 = HGroup(UItem('panel_ul'), UItem('panel_ur'))
        r2 = HGroup(UItem('panel_ll'), UItem('panel_lr'))

        panel_grp = VGroup(r1, r2, show_border=True, label='Panels')
        v = View(panel_grp)
        return v


VIEWS = {'main': MDDFigureMainOptions, 'appearance': MDDFigureAppearanceOptions}

# ============= EOF =============================================
