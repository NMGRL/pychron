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
from traits.api import List, Int, Property, Event, Any, cached_property, Str, Bool
from traitsui.api import Item, TabularEditor, Group, VGroup
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.viewable import Viewable, ViewableHandler
from pychron.processing.analysis_group import AnalysisRatioMean, \
    AnalysisIntensityMean, Marker
from pychron.database.core.database_selector import ColumnSorterMixin
from pychron.pychron_constants import PLUSMINUS
from pychron.helpers.formatting import floatfmt
from pychron.helpers.color_generators import colornames


class AnalysisAdapter(TabularAdapter):
#    columns = [('Status', 'status'),
#               ('ID', 'record_id'),
#               ('Age', 'age'),
#               (u'{}1s'.format(PLUSMINUS), 'age_error')
# #               (unicode('03c3', encoding='symbol'), 'error')
#               ]
    columns = Property
    include_age = Bool(True)

    status_text = Property
    status_width = Int(40)
    age_text = Property
    age_error_text = Property
    #    age_error_format = Str('%0.4f')
    #    age_width = Int(80)
    #    age_error_width = Int(80)
    @cached_property
    def _get_columns(self):
        columns = [('Status', 'status'),
                   ('ID', 'record_id')]
        columns.extend(self._construct_columns())
        if self.include_age:
            a = [('Age', 'age'),
                 (u'{}1s'.format(PLUSMINUS), 'age_error')]
            columns.extend(a)
        return columns

    def _construct_columns(self):
        return []

    def _get_status_text(self):
        status = ''
        if self.item.status != 0 or self.item.temp_status != 0:
            status = 'X'
        return status

    def _get_age_text(self):
        return self._get_value('age')

    def _get_age_error_text(self):
        return self._get_error('age')

    def get_font(self, obj, trait, row):
        import wx

        s = 9
        f = wx.FONTFAMILY_DEFAULT
        st = wx.FONTSTYLE_NORMAL
        w = wx.FONTWEIGHT_NORMAL
        return wx.Font(s, f, st, w)

    def get_bg_color(self, obj, trait, row, column):
        bgcolor = 'white'
        if self.item.status != 0 or self.item.temp_status != 0:
            bgcolor = '#FF7373'

        elif row % 2 == 0:
            bgcolor = '#F0F8FF'

        return bgcolor

    def get_text_color(self, obj, trait, row):
        if isinstance(self.item, Marker):
            color = 'white'
        else:
            gid = self.item.group_id
            color = colornames[gid]
        return color

    def _floatfmt(self, f, n=5):
        return floatfmt(f, n, 3)

    def _get_value(self, k):
        v = ''
        vv = getattr(self.item, k)
        if vv is not None and not isinstance(vv, str):
            v = self._floatfmt(vv.nominal_value)
        return v

    def _get_error(self, k):
        e = ''
        ee = getattr(self.item, k)
        if ee is not None and not isinstance(ee, str):
            e = self._floatfmt(ee.std_dev, n=6)
        return e


class AnalysisIntensityAdapter(AnalysisAdapter):
    Ar40_text = Property
    Ar40_error_text = Property
    Ar39_text = Property
    Ar39_error_text = Property
    Ar38_text = Property
    Ar38_error_text = Property
    Ar37_text = Property
    Ar37_error_text = Property
    Ar36_text = Property
    Ar36_error_text = Property

    def _construct_columns(self):
        columns = [
            #               ('Status', 'status'),
            #               ('ID', 'record_id'),
            ('Ar40', 'Ar40'),
            (u'{}1s'.format(PLUSMINUS), 'Ar40_error'),
            ('Ar39', 'Ar39'),
            (u'{}1s'.format(PLUSMINUS), 'Ar39_error'),
            ('Ar38', 'Ar38'),
            (u'{}1s'.format(PLUSMINUS), 'Ar38_error'),
            ('Ar37', 'Ar37'),
            (u'{}1s'.format(PLUSMINUS), 'Ar37_error'),
            ('Ar36', 'Ar36'),
            (u'{}1s'.format(PLUSMINUS), 'Ar36_error'),
            #               ('Age', 'age'),
            #               (u'{}1s'.format(PLUSMINUS), 'age_error'),
        ]
        return columns

    def _get_Ar40_text(self):
        return self._get_value('Ar40')

    def _get_Ar40_error_text(self):
        return self._get_error('Ar40')

    def _get_Ar39_text(self):
        return self._get_value('Ar39')

    def _get_Ar39_error_text(self):
        return self._get_error('Ar39')

    def _get_Ar38_text(self):
        return self._get_value('Ar38')

    def _get_Ar38_error_text(self):
        return self._get_error('Ar38')

    def _get_Ar37_text(self):
        return self._get_value('Ar37')

    def _get_Ar37_error_text(self):
        return self._get_error('Ar37')

    def _get_Ar36_text(self):
        return self._get_value('Ar36')

    def _get_Ar36_error_text(self):
        return self._get_error('Ar36')


class AnalysisRatioAdapter(AnalysisAdapter):
    Ar40_39_text = Property
    Ar40_39_error_text = Property
    Ar37_39_text = Property
    Ar37_39_error_text = Property
    Ar36_39_text = Property
    Ar36_39_error_text = Property
    kca_text = Property
    kca_error_text = Property
    kcl_text = Property
    kcl_error_text = Property

    def _construct_columns(self):
        columns = [
            #               ('Status', 'status'),
            #               ('ID', 'record_id'),
            ('40*/K39', 'Ar40_39'),
            (u'{}1s'.format(PLUSMINUS), 'Ar40_39_error'),
            ('Ar37/Ar39', 'Ar37_39'),
            (u'{}1s'.format(PLUSMINUS), 'Ar37_39_error'),
            ('Ar36/Ar39', 'Ar36_39'),
            (u'{}1s'.format(PLUSMINUS), 'Ar36_39_error'),
            ('K/Ca', 'kca'),
            (u'{}1s'.format(PLUSMINUS), 'kca_error'),
            ('K/Cl', 'kcl'),
            (u'{}1s'.format(PLUSMINUS), 'kcl_error'),
            #               ('Age', 'age'),
            #               (u'{}1s'.format(PLUSMINUS), 'age_error'),
        ]
        return columns

    def _get_Ar40_39_text(self):
        return self._get_value('Ar40_39')

    def _get_Ar40_39_error_text(self):
        return self._get_error('Ar40_39')

    def _get_Ar37_39_text(self):
        return self._get_value('Ar37_39')

    def _get_Ar37_39_error_text(self):
        return self._get_error('Ar37_39')

    def _get_Ar36_39_text(self):
        return self._get_value('Ar36_39')

    def _get_Ar36_39_error_text(self):
        return self._get_error('Ar36_39')

    def _get_kca_text(self):
        return self._get_value('kca')

    def _get_kca_error_text(self):
        return self._get_error('kca')

    def _get_kcl_text(self):
        return self._get_value('kcl')

    def _get_kcl_error_text(self):
        return self._get_error('kcl')


class MeanAdapter(AnalysisAdapter):
    nanalyses_width = Int(40)

    weighted_age_text = Property
    arith_age_text = Property
    age_se_text = Property
    age_sd_text = Property

    def get_text_color(self, *args):
        return 'black'

    def _get_weighted_age_text(self):
        return self._get_value('weighted_age')

    def _get_arith_age_text(self):
        return self._get_value('arith_age')

    def _get_age_se_text(self):
        return self._get_error('weighted_age')

    def _get_age_sd_text(self):
        return self._get_error('arith_age')

    def get_bg_color(self, obj, trait, row, column):
        bgcolor = 'white'
        if row % 2 == 0:
            bgcolor = '#F0F8FF'

        return bgcolor

    @cached_property
    def _get_columns(self):
        columns = [('N', 'nanalyses'),
                   ('ID', 'identifier')]
        columns.extend(self._construct_columns())
        if self.include_age:
            a = [
                ('Wtd. Age', 'weighted_age'),
                ('S.E', 'age_se'),
                ('Arith. Age', 'arith_age'),
                ('S.D', 'age_sd')
                #                 (u'{}1s'.format(PLUSMINUS), 'age_error')
            ]
            columns.extend(a)
        return columns


class AnalysisRatioMeanAdapter(MeanAdapter, AnalysisRatioAdapter):
    def _construct_columns(self):
        columns = [
            #                   ('N', 'nanalyses'),
            #                   ('ID', 'identifier'),
            ('40*/K39', 'Ar40_39'),
            ('S.E.', 'Ar40_39_error'),
            #                   (u'{}1s'.format(PLUSMINUS), 'Ar40_39_error'),
            ('Ar37/Ar39', 'Ar37_39'),
            #                   (u'{}1s'.format(PLUSMINUS), 'Ar37_39_error'),
            ('S.E.', 'Ar37_39_error'),
            ('Ar36/Ar39', 'Ar36_39'),
            #                   (u'{}1s'.format(PLUSMINUS), 'Ar36_39_error'),
            ('S.E.', 'Ar36_39_error'),
            ('K/Ca', 'kca'),
            #                   (u'{}1s'.format(PLUSMINUS), 'kca_error'),
            ('S.E.', 'kca_error'),
            ('K/Cl', 'kcl'),
            #                   (u'{}1s'.format(PLUSMINUS), 'kcl_error'),
            ('S.E.', 'kcl_error'),
            #                   ('Age', 'age'),
            #                   (u'{}1s'.format(PLUSMINUS), 'age_error'),
        ]
        return columns


class AnalysisIntensityMeanAdapter(MeanAdapter, AnalysisIntensityAdapter):
    def _construct_columns(self):
        columns = [
            ('Ar40', 'Ar40'),
            ('S.E.', 'Ar40_error'),
            #                   (u'{}1s'.format(PLUSMINUS), 'Ar40_error'),
            ('Ar39', 'Ar39'),
            ('S.E.', 'Ar39_error'),
            #                   (u'{}1s'.format(PLUSMINUS), 'Ar39_error'),
            ('Ar38', 'Ar38'),
            ('S.E.', 'Ar38_error'),
            #                   (u'{}1s'.format(PLUSMINUS), 'Ar38_error'),
            ('Ar37', 'Ar37'),
            ('S.E.', 'Ar37_error'),
            #                   (u'{}1s'.format(PLUSMINUS), 'Ar37_error'),
            ('Ar36', 'Ar36'),
            ('S.E.', 'Ar36_error')
            #                   (u'{}1s'.format(PLUSMINUS), 'Ar36_error')
        ]
        return columns


class TabularAnalysisHandler(ViewableHandler):
    def object_title_changed(self, info):
        if info.initialized:
            info.ui.title = info.object.title


class TabularAnalysisManager(Viewable, ColumnSorterMixin):
    analyses = List
    ratio_means = Property(depends_on='analyses.[temp_status,status]')
    intensity_means = Property(depends_on='analyses.[temp_status,status]')

    include_age = Property

    update_selected_analysis = Event
    selected_analysis = Any
    db = Any
    window_x = 50
    window_y = 200
    window_width = 0.85
    window_height = 500
    title = Str('Analysis Table')
    handler_klass = TabularAnalysisHandler


    def set_analyses(self, ans):
        curgrp = 0
        aans = []
        for ai in ans:
            if ai.group_id != curgrp:
                aans.append(Marker())
                curgrp += 1
            aans.append(ai)

        self.analyses = aans

    def set_title(self, title):
        self.title = 'Table {}'.format(title)

    def _get_include_age(self):
        for a in self.analyses:
            if a.analysis_type not in ['unknown', 'cocktail']:
                return False
        else:
            return True

    @cached_property
    def _get_ratio_means(self):
        return self._get_means(AnalysisRatioMean)

    #        means = [AnalysisRatioMean(analyses=ans) for ans in grps]
    #        means = [AnalysisRatioMean(analyses=self.analyses)]
    #        return means

    @cached_property
    def _get_intensity_means(self):
        return self._get_means(AnalysisIntensityMean)

    #        means = [AnalysisIntensityMean(analyses=self.analyses)]
    #        return means

    def _get_means(self, klass):
        means = []
        grp = []
        for ai in self.analyses:
            if isinstance(ai, Marker):
                means.append(klass(analyses=grp))
                #                grps.append(grp)
                grp = []
            else:
                grp.append(ai)

        means.append(klass(analyses=grp))
        return means

    def _editor_factory(self, adapter_klass, **kw):

        ta = TabularEditor(adapter=adapter_klass(include_age=self.include_age),
                           column_clicked='column_clicked',
                           editable=False,
                           auto_update=True,
                           **kw
        )
        return ta

    def traits_view(self):


        intensity = VGroup(Item('analyses',
                                height=300,
                                show_label=False,
                                editor=self._editor_factory(AnalysisIntensityAdapter,
                                                            dclicked='update_selected_analysis',
                                                            selected='selected_analysis')
        ),
                           Item('intensity_means',
                                height=100,
                                show_label=False,
                                editor=self._editor_factory(AnalysisIntensityMeanAdapter)
                           )
        )
        ratio = VGroup(
            Item('analyses',
                 height=300,
                 show_label=False,
                 editor=self._editor_factory(AnalysisRatioAdapter,
                                             dclicked='update_selected_analysis',
                                             selected='selected_analysis'
                 )
            ),
            Item('ratio_means',
                 height=100,
                 show_label=False,
                 editor=self._editor_factory(AnalysisRatioMeanAdapter)
                 #                          editor=TabularEditor(adapter=AnalysisRatioMeanAdapter(),
                 #                                               editable=False,
                 #                                               auto_update=True,
                 #                                               column_clicked='column_clicked',
                 #                                               )
            )

        )

        return self.view_factory(Group(
            Group(intensity, label='Intensities'),
            Group(ratio, label='Ratios'),
            layout='tabbed'
        ),
        )

    def _update_selected_analysis_fired(self):
        sa = self.selected_analysis
        if sa is not None:
            dbr = sa.isotope_record
            if self.db:
                self.db.selector.open_record(dbr)

#            dbr.load_graph()
#            dbr.edit_traits()
#============= EOF =============================================
#    def _set_Ar40_text(self, v):
#        pass
#
#    def _set_Ar40_error_text(self, v):
#        pass
#
#    def _set_Ar39_text(self, v):
#        pass
#
#    def _set_Ar39_error_text(self, v):
#        pass
#
#    def _set_Ar38_text(self, v):
#        pass
#
#    def _set_Ar38_error_text(self, v):
#        pass
#
#    def _set_Ar37_text(self, v):
#        pass
#
#    def _set_Ar37_error_text(self, v):
#        pass
#
#    def _set_Ar36_text(self, v):
#        pass
#
#    def _set_Ar36_error_text(self, v):
#        pass
#
#    def _set_age_text(self, v):
#        pass
#
#    def _set_age_error_text(self, v):
#        pass
