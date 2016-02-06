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
from traitsui.api import View, UItem, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options import SubOptions, AppearanceSubOptions


class SeriesSubOptions(SubOptions):
    def traits_view(self):
        v = View()
        return v


class SeriesAppearance(AppearanceSubOptions):
    def traits_view(self):
        fgrp = VGroup(UItem('fontname'),
                      self._get_xfont_group(),
                      self._get_yfont_group(),
                      label='Fonts', show_border=True)

        g = VGroup(self._get_bg_group(),
                   self._get_padding_group())
        return self._make_view(VGroup(g, fgrp))


# ===============================================================
# ===============================================================
VIEWS = {}
VIEWS['series'] = SeriesSubOptions
VIEWS['appearance'] = SeriesAppearance


# ===============================================================
# ===============================================================


# ============= EOF =============================================
