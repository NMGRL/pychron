# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import List, Any, Str, Enum, Bool, Event, Property, cached_property, Instance, DelegatesTo, \
    CStr, Int, Button
# ============= standard library imports ========================
import json
import os
from collections import OrderedDict
from datetime import datetime
# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.envisage.browser.adapters import AnalysisAdapter
from pychron.core.ui.table_configurer import AnalysisTableConfigurer
from pychron.paths import paths


def sort_items(ans):
    return sorted(ans, key=lambda x: x.timestampf)


class AnalysisTable(ColumnSorterMixin):
    analyses = List
    oanalyses = List
    selected = Any
    dclicked = Any

    context_menu_event = Event

    analysis_filter = CStr
    analysis_filter_values = List
    analysis_filter_comparator = Enum('=', '<', '>', '>=', '<=', 'not =', 'startswith')
    analysis_filter_parameter = Str
    analysis_filter_parameters = Property(List, depends_on='tabular_adapter.columns')

    # omit_invalid = Bool(True)
    table_configurer = Instance(AnalysisTableConfigurer)

    limit = DelegatesTo('table_configurer')
    omit_invalid = DelegatesTo('table_configurer')

    no_update = False
    scroll_to_row = Event
    refresh_needed = Event
    tabular_adapter = Instance(AnalysisAdapter)
    append_replace_enabled = Bool(True)

    add_analysis_set_button = Button
    analysis_set = Str
    analysis_set_names = List
    _analysis_sets = None
    max_history = Int
    suppress_load_analysis_set = False

    def __init__(self, *args, **kw):
        super(AnalysisTable, self).__init__(*args, **kw)

        self._analysis_sets = OrderedDict()

    def load(self):
        p = paths.hidden_path('analysis_sets')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                jd = json.load(rfile, object_pairs_hook=OrderedDict)
                self._analysis_sets = jd
                self.analysis_set_names = list(reversed(jd.keys()))

    def dump(self):
        p = paths.hidden_path('analysis_sets')
        with open(p, 'w') as wfile:
            json.dump(self._analysis_sets, wfile)

    def add_analysis_set(self, current=False):
        if self.analyses:
            aset = [(a.uuid, a.record_id) for a in self.analyses]
            if aset:
                if len(aset) > 1:
                    name = '{} -- {}'.format(aset[0][1], aset[-1][1])
                else:
                    name = aset[0][1]

            name = '{} ({})'.format(name, datetime.now().strftime('%m/%d/%y'))
            self._analysis_sets[name] = aset

            if self.max_history:
                while len(self._analysis_sets) > self.max_history:
                    self._analysis_sets.popitem(last=False)
            return name

    def get_analysis_set(self, key):
        return self._analysis_sets[key]

    def set_tags(self, tag, items):
        for i in items:
            ai = next((a for a in self.oanalyses if a.uuid == i.uuid), None)
            if ai:
                ai.tag = tag

        self._analysis_filter_changed(self.analysis_filter)

    def remove_invalid(self):
        self.oanalyses = [ai for ai in self.oanalyses if ai.tag != 'invalid']
        self._analysis_filter_changed(self.analysis_filter)

    def add_analyses(self, ans):
        items = self.analyses
        items.extend(ans)
        self.oanalyses = self.analyses = sort_items(items)
        self.calculate_dts(self.analyses)

    def set_analyses(self, ans, tc=None, page=None, reset_page=False, selected_identifiers=None):
        if selected_identifiers:
            aa = self.analyses
            aa = [ai for ai in aa if ai.identifier in selected_identifiers]
            aa.extend(ans)
        else:
            aa = ans

        self.oanalyses = self.analyses = sort_items(aa)

        self.calculate_dts(self.analyses)
        self.add_analysis_set()

    def calculate_dts(self, ans):
        if ans and len(ans) > 1:
            self._python_dt(ans)

    def _python_dt(self, ans):
        ref = ans[0]
        prev = ref.timestampf
        ref.delta_time = 0
        for ai in ans[1:]:
            t = ai.timestampf
            dt = (t - prev) / 60.
            ai.delta_time = dt
            prev = t

    def configure_table(self):
        self.table_configurer.edit_traits(kind='livemodal')

    def review_status_details(self):
        from pychron.envisage.browser.review_status_details import ReviewStatusDetailsView, ReviewStatusDetailsModel
        m = ReviewStatusDetailsModel(self.selected[0])
        rsd = ReviewStatusDetailsView(model=m)
        rsd.edit_traits()

    # handlers
    def _add_analysis_set_button_fired(self):
        name = self.add_analysis_set()
        if name:
            self.dump()
            self.load()

            self.suppress_load_analysis_set = True
            self.analysis_set = name
            self.suppress_load_analysis_set = False

    def _analyses_items_changed(self, old, new):
        if self.sort_suppress:
            return

        self.calculate_dts(self.analyses)

        if new.removed:
            for ai in new.removed:
                self.oanalyses.remove(ai)

    def _analysis_filter_changed(self, new):
        if new:
            name = self.analysis_filter_parameter
            self.analyses = fuzzyfinder(new, self.oanalyses, name)
            # self.analyses = filter(filter_func(new, name), self.oanalyses)
        else:
            self.analyses = self.oanalyses

    def _analysis_filter_comparator_changed(self):
        self._analysis_filter_changed(self.analysis_filter)

    def _get_analysis_filter_parameter(self):
        p = self.analysis_filter_parameter
        return p.lower()

    @cached_property
    def _get_analysis_filter_parameters(self):
        return dict([(ci[1], ci[0]) for ci in self.tabular_adapter.columns])

    # defaults
    def _table_configurer_default(self):
        return AnalysisTableConfigurer(id='analysis.table',
                                       title='Configure Analysis Table')

    def _analysis_filter_parameter_default(self):
        return 'record_id'

    def _tabular_adapter_default(self):
        adapter = AnalysisAdapter()
        self.table_configurer.adapter = adapter
        self.table_configurer.load()
        return adapter

# ============= EOF =============================================
