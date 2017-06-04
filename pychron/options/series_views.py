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
from traitsui.api import View, UItem, VGroup, EnumEditor

from pychron.options.options import SubOptions, AppearanceSubOptions, MainOptions, object_column, checkbox_column


class SeriesSubOptions(SubOptions):
    def traits_view(self):
        v = View('use_time_axis')
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


class SeriesMainOptions(MainOptions):
    def _get_columns(self):
        cols = [checkbox_column(name='plot_enabled', label='Use'),
                object_column(name='name',
                              width=130,
                              editor=EnumEditor(name='names')),
                object_column(name='scale'),
                object_column(name='height',
                              format_func=lambda x: str(x) if x else ''),
                checkbox_column(name='show_labels', label='Labels'),
                checkbox_column(name='x_error', label='X Err.'),
                checkbox_column(name='y_error', label='Y Err.'),
                checkbox_column(name='ytick_visible', label='Y Tick'),
                checkbox_column(name='ytitle_visible', label='Y Title'),
                checkbox_column(name='use_dev', label='Dev'),
                checkbox_column(name='use_percent_dev', label='Dev %')
                # checkbox_column(name='has_filter', label='Filter', editable=False)
                ]

        return cols
# ===============================================================
# ===============================================================
VIEWS = {'main': SeriesMainOptions, 'series': SeriesSubOptions, 'appearance': SeriesAppearance}
# VIEWS['series'] = SeriesSubOptions
# VIEWS['appearance'] = SeriesAppearance


# ===============================================================
# ===============================================================


# ============= EOF =============================================
