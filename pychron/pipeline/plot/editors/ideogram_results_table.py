# ===============================================================================
# Copyright 2018 ross
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
from traits.api import HasTraits, List, Property, Int
from traitsui.api import View, UItem, TabularEditor
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import std_dev, nominal_value

from pychron.core.helpers.formatting import floatfmt
from pychron.core.pychron_traits import BorderVGroup


class IdeogramResultsAdapter(TabularAdapter):
    columns = [('Name', 'group_id'),
               ('Identifier', 'identifier'),
               ('Sample', 'sample'),
               ('Age Span', 'age_span'),
               ('Weighted Mean Age', 'weighted_mean_age'),
               ('Weighted Mean Age Err.', 'weighted_mean_age_error'),
               ('N', 'nanalyses'),
               ('MSWD', 'mswd')]

    group_id_width = Int(50)
    identifier_width = Int(75)
    sample_width = Int(200)
    age_span_width = Int(150)
    weighted_mean_age_width = Int(150)
    weighted_mean_age_error_width = Int(150)
    n_width = Int(50)

    weighted_mean_age_text = Property
    weighted_mean_age_error_text = Property
    mswd_text = Property
    age_span_text = Property
    nsigma = Int(1)

    def get_text_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        return item.color

    def _get_age_span_text(self):
        return floatfmt(self.item.age_span, n=5)

    def _get_mswd_text(self):
        m, v, n = self.item.get_mswd_tuple()
        return '{}{}'.format('' if v else '*', floatfmt(m, n=3))

    def _get_weighted_mean_age_text(self):
        wt = self.item.weighted_age
        return floatfmt(nominal_value(wt), n=5)

    def _get_weighted_mean_age_error_text(self):
        wt = self.item.weighted_age
        return floatfmt(std_dev(wt)*self.nsigma, n=5)


class IdeogramResultsTable(HasTraits):
    analysis_groups = List

    def __init__(self, analysis_groups, nsigma, *args, **kw):
        super(IdeogramResultsTable, self).__init__(*args, **kw)
        self.analysis_groups = analysis_groups
        self.adapter = IdeogramResultsAdapter(nsigma=nsigma)

    def traits_view(self):
        v = View(BorderVGroup(UItem('analysis_groups',
                                    editor=TabularEditor(adapter=self.adapter)),
                              label='Summary'))
        return v
# ============= EOF =============================================
