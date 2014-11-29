# ===============================================================================
# Copyright 2014 Jake Ross
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
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Button, Instance, List, Property
from traitsui.api import View, VGroup, UItem, TabularEditor, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev
from pychron.core.helpers.formatting import floatfmt
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.processing.tasks.browser.panes import AnalysisGroupAdapter
from pychron.processing.tasks.recall.base_summary_editor import BaseSummaryEditor
from pychron.pychron_constants import PLUSMINUS_SIGMA


class AnalysisGroupAdapter(TabularAdapter):
    columns = [('Identifier', 'identifier'),
               ('Sample', 'sample'),
               ('N','nanalyses'),
               ('Wtd. Mean', 'weighted_age'),
               (PLUSMINUS_SIGMA, 'weighted_age_error')]

    weighted_age_text = Property
    weighted_age_error_text = Property

    font = '10'

    def _get_weighted_age_text(self):
        return floatfmt(nominal_value(self.item.weighted_age))

    def _get_weighted_age_error_text(self):
        return floatfmt(std_dev(self.item.weighted_age))


class SummaryProjectTool(HasTraits):
    ideogram_options_button = Button

    def traits_view(self):
        igrp = VGroup(icon_button_editor('ideogram_options_button', 'cog'),
                      label='Ideogram', show_border=True)
        v = View(VGroup(igrp))
        return v


class SummaryProjectEditor(BaseSummaryEditor):
    tool = Instance(SummaryProjectTool, ())
    analysis_groups = List

    def load(self):
        self._create_ideogram()
        self.analysis_groups = [f.analysis_group for f in self.ideogram_panel.figures]

    def traits_view(self):
        ideogram_grp = VGroup(UItem('ideogram_graph',
                                    visible_when='ideogram_visible',
                                    editor=ComponentEditor()),
                              label='Ideogram')
        stats_grp = VGroup(
            UItem('analysis_groups',
                  editor=TabularEditor(adapter=AnalysisGroupAdapter())),
            label='Stats')
        v = View(Tabbed(stats_grp, ideogram_grp))
        return v

# ============= EOF =============================================



