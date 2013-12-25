#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, List, Any, Str, Enum, Bool, Button, \
    Event
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.browser.table_configurer import TableConfigurer


class AnalysisTable(HasTraits):
    analyses = List
    oanalyses = List
    selected = Any
    dclicked = Any

    analysis_filter = Str
    analysis_filter_values = List
    analysis_filter_comparator = Enum('=', '<', '>', '>=', '<=', 'not =', 'startswith')
    analysis_filter_parameter = Str('Record_id')
    analysis_filter_parameters = List(['Record_id', 'Tag',
                                       'Age', 'Labnumber', 'Aliquot', 'Step'])

    omit_invalid = Bool(True)
    configure_analysis_table = Button

    # forward = Button
    # backward = Button
    # page_width = Int(1000)
    # page = Int(1, enter_set=True, auto_set=False)
    #
    # forward_enabled = Bool
    # backward_enabled = Bool
    # n_all_analyses = Int
    # npages = Property(depends_on='n_all_analyses,page_width')

    no_update = False
    scroll_to_row=Event
    refresh_needed=Event

    # def load(self):
    #     p = os.path.join(paths.hidden_dir, 'analysis_table')
    #     if os.path.isfile(p):
    #         d={}
    #         with open(p, 'r') as fp:
    #             try:
    #                d=pickle.load(fp)
    #             except (pickle.PickleError, OSError, EOFError):
    #                 pass
    #
    #         self.trait_set(**d)
    #
    # def dump(self):
    #     p=os.path.join(paths.hidden_dir, 'analysis_table')
    #     with open(p,'w') as fp:
    #         pickle.dump({'page_width':self.page_width}, fp)

    # def _forward_fired(self):
    #     if self.page < self.npages:
    #         self.page += 1
    #         #if self.oanalyses:
    #         #    self.page+=1
    #
    # def _backward_fired(self):
    #     p = self.page
    #     p -= 1
    #     self.page = max(1, p)

    def set_analyses(self, ans, tc=None, page=None, reset_page=False):
        self.analyses = ans
        self.oanalyses = ans
        if tc is None:
            tc=len(ans)

        self.n_all_analyses = tc
        # if reset_page:
        #     self.no_update = True
        #     if page<0:
        #         self.page=self.npages
        #         self.scroll_to_row=self.page_width
        #     else:
        #         self.page = 1
        #     self.no_update = False

    def _analysis_filter_changed(self, new):
        if new:
            name = self.analysis_filter_parameter
            comp = self.analysis_filter_comparator
            if name == 'Step':
                new = new.upper()

            self.analyses = filter(self._filter_func(new, name, comp), self.oanalyses)
        else:
            self.analyses = self.oanalyses

    def _configure_analysis_table_fired(self):

        c = TableConfigurer(adapter=self.tabular_adapter,
                            title='Configure Analysis Table')
        c.edit_traits()

    # def _get_npages(self):
    #     try:
    #         return int(math.ceil(self.n_all_analyses / float(self.page_width)))
    #     except ZeroDivisionError:
    #         return 0

    def _get_analysis_filter_parameter(self):
        p = self.analysis_filter_parameter
        return p.lower()

    def _analysis_filter_comparator_changed(self):
        self._analysis_filter_changed(self.analysis_filter)

    def _analysis_filter_parameter_changed(self, new):
        if new:
            vs = []
            p = self._get_analysis_filter_parameter()
            for si in self.oanalyses:
                v = getattr(si, p)
                if not v in vs:
                    vs.append(v)

            self.analysis_filter_values = vs

            #============= EOF =============================================
            #def filter_invalid(self, ans):
            #    if self.omit_invalid:
            #        ans = filter(self._omit_invalid_filter, ans)
            #    return ans

            #def _omit_invalid_filter(self, x):
            #    return x.tag != 'invalid'

            #def _omit_invalid_changed(self, new):
            #    if new:
            #        self._
            #        self.analyses = filter(self._omit_invalid_filter, self.oanalyses)
            #    else:
            #        self.analyses = self.oanalyses
