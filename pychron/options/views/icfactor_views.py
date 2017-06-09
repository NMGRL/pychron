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
from enable.markers import marker_names
from traitsui.api import View, UItem, Item, HGroup, VGroup, EnumEditor, Label
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options import SubOptions, AppearanceSubOptions, MainOptions, object_column, checkbox_column


class ICFactorMainOptions(MainOptions):
    def _get_edit_view(self):
        f = VGroup(HGroup(UItem('numerator', editor=EnumEditor(name='detectors')), Label('/'),
                          UItem('denominator', editor=EnumEditor(name='detectors'))),
                   HGroup(Item('fit', editor=EnumEditor(name='fit_types')),
                          UItem('error_type', editor=EnumEditor(name='error_types'))),
                   Item('analysis_type', editor=EnumEditor(name='analysis_types')),
                   Item('standard_ratio'), show_border=True, label='IC')

        s = VGroup(HGroup(Item('marker', editor=EnumEditor(values=marker_names)),
                          Item('marker_size')), show_border=True, label='Scatter')
        y = VGroup(HGroup(Item('ymin', label='Min'),
                          Item('ymax', label='Max')), show_border=True, label='Y Limits')

        v = View(VGroup(f, s, y))
        return v

    def _get_columns(self):
        return [
            object_column(name='numerator', editor=EnumEditor(name='detectors')),
            object_column(name='denominator', editor=EnumEditor(name='detectors')),
            checkbox_column(name='plot_enabled', label='Plot'),
            checkbox_column(name='save_enabled', label='Save'),

            object_column(name='fit',
                          editor=EnumEditor(name='fit_types'),
                          width=75),
            object_column(name='error_type',
                          editor=EnumEditor(name='error_types'),
                          width=75, label='Error'),
            # checkbox_column(name='filter_outliers', label='Out.'),
            # object_column(name='filter_outlier_iterations', label='Iter.'),
            # object_column(name='filter_outlier_std_devs', label='SD'),
            # object_column(name='truncate', label='Trunc.'),
            # checkbox_column(name='include_baseline_error', label='Inc. BsErr')
        ]


class ICFactorSubOptions(SubOptions):
    def traits_view(self):
        v = View()
        return v


class ICFactorAppearance(AppearanceSubOptions):
    pass
    # def traits_view(self):
    #     fgrp = VGroup(UItem('fontname'),
    #                   self._get_xfont_group(),
    #                   self._get_yfont_group(),
    #                   label='Fonts', show_border=True)
    #
    #     v = View(VGroup(self._get_bg_group(),
    #                     self._get_padding_group(),
    #                     fgrp))
    #     return v


# ===============================================================
# ===============================================================
VIEWS = {}
VIEWS['main'] = ICFactorMainOptions
VIEWS['icfactor'] = ICFactorSubOptions
VIEWS['appearance'] = ICFactorAppearance

# def _get_edit_view(self):
#         f = VGroup(HGroup(UItem('numerator', editor=EnumEditor(name='detectors')), Label('/'),
#                           UItem('denominator', editor=EnumEditor(name='detectors'))),
#                    HGroup(Item('fit', editor=EnumEditor(name='fit_types')),
#                           UItem('error_type', editor=EnumEditor(name='error_types'))),
#                    Item('analysis_type', editor=EnumEditor(name='analysis_types')),
#                    Item('standard_ratio'), show_border=True, label='IC')
#
#         s = VGroup(HGroup(Item('marker', editor=EnumEditor(values=marker_names)),
#                           Item('marker_size')), show_border=True, label='Scatter')
#         y = VGroup(HGroup(Item('ymin', label='Min'),
#                           Item('ymax', label='Max')), show_border=True, label='Y Limits')
#
#         v = View(VGroup(f, s, y))
#         return v
#         # return View(VGroup(
#         #     Item('numerator', editor=EnumEditor(name='detectors')),
#         #     Item('denominator', editor=EnumEditor(name='detectors')),
#         #
#         #                 HGroup(Item('ymin', label='Min'),
#         #                        Item('ymax', label='Max'),
#         #                        show_border=True,
#         #                        label='Y Limits'),
#         #                 show_border=True))
#
#     def _get_columns(self):
#         return [
#             object_column(name='numerator', editor=EnumEditor(name='detectors')),
#             object_column(name='denominator', editor=EnumEditor(name='detectors')),
#             checkbox_column(name='plot_enabled', label='Plot'),
#             checkbox_column(name='save_enabled', label='Save'),
#
#             object_column(name='fit',
#                           editor=EnumEditor(name='fit_types'),
#                           width=75),
#             object_column(name='error_type',
#                           editor=EnumEditor(name='error_types'),
#                           width=75, label='Error'),
#             # checkbox_column(name='filter_outliers', label='Out.'),
#             # object_column(name='filter_outlier_iterations', label='Iter.'),
#             # object_column(name='filter_outlier_std_devs', label='SD'),
#             # object_column(name='truncate', label='Trunc.'),
#             # checkbox_column(name='include_baseline_error', label='Inc. BsErr')
#         ]
# ===============================================================
# ===============================================================


# ============= EOF =============================================
