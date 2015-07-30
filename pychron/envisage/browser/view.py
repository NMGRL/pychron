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
from traits.api import HasTraits, Str, Instance, Button
from traitsui.api import View, UItem, HGroup, VGroup, Group, spring
from traitsui.handler import Handler
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.browser.adapters import BrowserAdapter
from pychron.envisage.browser.sample_view import BrowserSampleView
from pychron.envisage.browser.time_view import TimeViewModel
from pychron.envisage.icon_button_editor import icon_button_editor


class AnalysisGroupAdapter(BrowserAdapter):
    all_columns = [('Name', 'name'),
                   ('Created', 'create_date'),
                   ('Modified', 'last_modified')]

    columns = [('Name', 'name'),
               ('Create Date', 'create_date'),
               ('Modified', 'last_modified')]


class BrowserViewHandler(Handler):
    def pane_append_button_changed(self, info):
        info.ui.context['pane'].is_append = True
        info.ui.dispose(True)

    def pane_replace_button_changed(self, info):
        info.ui.context['pane'].is_append = False
        info.ui.dispose(True)


class BaseBrowserView(HasTraits):
    name = 'Browser'
    id = 'pychron.browser'
    multi_select = True
    analyses_defined = Str('1')

    # labnumber_tabular_adapter = Instance(LabnumberAdapter, ())
    # analysis_tabular_adapter = Instance(AnalysisAdapter, ())
    # analysis_group_tabular_adapter = Instance(AnalysisGroupAdapter, ())

    sample_view = Instance(BrowserSampleView)
    # query_view = Instance(BrowserQueryView)
    time_view = Instance(TimeViewModel)

    model = Instance(HasTraits)

    def trait_context(self):
        """ Use the model object for the Traits UI context, if appropriate.
        """
        if self.model:
            return {'object': self.model, 'pane': self}
        return super(BrowserView, self).trait_context()

    def _get_browser_group(self):
        grp = Group(UItem('pane.sample_view',
                          style='custom',
                          visible_when='sample_view_active'),
                    UItem('time_view_model',
                          style='custom',
                          visible_when='not sample_view_active')
                    # UItem('pane.query_view',
                    # style='custom',
                    # visible_when='not sample_view_active')
                    )
        return grp

    def _sample_view_default(self):
        return BrowserSampleView(model=self.model, pane=self)

        # def _query_view_default(self):
        # return BrowserQueryView(model=self.model.data_selector, pane=self)


class StandaloneBrowserView(BaseBrowserView):
    def traits_view(self):
        main_grp = self._get_browser_group()

        hgrp = HGroup(icon_button_editor('filter_by_button',
                                         'find',
                                         tooltip='Filter analyses using defined criteria'),
                      icon_button_editor('graphical_filter_button',
                                         'chart_curve_go',
                                         tooltip='Filter analyses graphically'),
                      icon_button_editor('toggle_view',
                                         'arrow_switch',
                                         tooltip='Toggle between Sample and Time views'),
                      spring,
                      CustomLabel('datasource_url', color='maroon'))

        v = View(VGroup(hgrp, main_grp),
                 buttons=['OK', 'Cancel'],
                 title='Browser',
                 resizable=True)

        return v


class PaneBrowserView(BaseBrowserView):
    def traits_view(self):
        main_grp = self._get_browser_group()

        hgrp = HGroup(icon_button_editor('filter_by_button',
                                         'find',
                                         tooltip='Filter analyses using defined criteria'),
                      icon_button_editor('graphical_filter_button',
                                         'chart_curve_go',
                                         tooltip='Filter analyses graphically'),
                      icon_button_editor('toggle_view',
                                         'arrow_switch',
                                         tooltip='Toggle between Sample and Time views'),
                      spring,
                      CustomLabel('datasource_url', color='maroon'))

        v = View(VGroup(hgrp, main_grp))

        return v


class BrowserView(BaseBrowserView):
    is_append = False

    append_button = Button('Append')
    replace_button = Button('Replace')

    def traits_view(self):
        main_grp = self._get_browser_group()

        hgrp = HGroup(icon_button_editor('filter_by_button',
                                         'find',
                                         tooltip='Filter analyses using defined criteria'),
                      icon_button_editor('graphical_filter_button',
                                         'chart_curve_go',
                                         tooltip='Filter analyses graphically'),
                      icon_button_editor('toggle_view',
                                         'arrow_switch',
                                         tooltip='Toggle between Sample and Time views'),
                      spring,
                      CustomLabel('datasource_url', color='maroon'))

        bgrp = HGroup(spring, UItem('pane.append_button'), UItem('pane.replace_button'))
        v = View(VGroup(hgrp, main_grp, bgrp),
                 # buttons=['Cancel'],
                 # Action(name='Append',
                 #        action='append_analyses'),
                 # Action(name='Replace',
                 #        action='replace_analyses')],
                 handler=BrowserViewHandler(),
                 title='Browser',
                 resizable=True)

        return v
# ============= EOF =============================================
