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

import json
import os
from collections import OrderedDict
from datetime import datetime
from hashlib import md5
from operator import attrgetter

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from pyface.message_dialog import warning, information
from traits.api import List, Any, Str, Enum, Bool, Event, Property, cached_property, Instance, DelegatesTo, \
    CStr, Int, Button

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.core.helpers.iterfuncs import groupby_repo
from pychron.core.select_same import SelectSameMixin
from pychron.dvc.func import get_review_status
from pychron.envisage.browser import progress_bind_records
from pychron.envisage.browser.adapters import AnalysisAdapter
from pychron.envisage.browser.analysis_table_configurer import AnalysisTableConfigurer
from pychron.paths import paths
from pychron.pychron_constants import AUTO_SCROLL_KINDS, BOTTOM, TOP


def sort_items(ans):
    return sorted(ans, key=attrgetter('timestampf'))


class AnalysisTable(ColumnSorterMixin, SelectSameMixin):
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
    scroll_to_bottom = Event
    scroll_to_top = Event

    refresh_needed = Event
    tabular_adapter = Instance(AnalysisAdapter)
    append_replace_enabled = Bool(True)

    add_analysis_set_button = Button
    refresh_analysis_set_button = Button

    analysis_set = Str
    analysis_set_names = List
    _analysis_sets = None
    max_history = Int
    suppress_load_analysis_set = False

    default_attr = 'identifier'
    dvc = Instance('pychron.dvc.dvc.DVC')

    one_selected_is_all = Bool(True)
    auto_scroll_kind = Enum(AUTO_SCROLL_KINDS)

    def __init__(self, *args, **kw):
        super(AnalysisTable, self).__init__(*args, **kw)
        bind_preference(self, 'one_selected_is_all', 'pychron.browser.one_selected_is_all')
        bind_preference(self, 'auto_scroll_kind', 'pychron.browser.auto_scroll_kind')

        self._analysis_sets = OrderedDict()

    def _sorted_hook(self, vs):
        self.oanalyses = vs

    def load(self):
        p = paths.hidden_path('analysis_sets')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                try:
                    jd = json.load(rfile, object_pairs_hook=OrderedDict)
                except ValueError as e:
                    print('load sanlaysis set exception', e)
                    return

                self._analysis_sets = jd
                self.analysis_set_names = list(reversed([ji[0] for ji in jd.values()]))

        p = paths.hidden_path('selected_analysis_set')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                self.analysis_set = rfile.read().strip()

    def dump(self):
        p = paths.hidden_path('analysis_sets')
        if self._analysis_sets:
            with open(p, 'w') as wfile:
                json.dump(self._analysis_sets, wfile)

        p = paths.hidden_path('selected_analysis_set')
        with open(p, 'w') as wfile:
            wfile.write(self.analysis_set or '')

    def get_selected_analyses(self):
        if self.analyses:
            ans = self.selected
            if not ans:
                ans = self.analyses
            return ans

    def add_analysis_set(self):
        ans = self.get_selected_analyses()
        if ans:
            aset = [(a.uuid, a.record_id) for a in ans]
            if aset:
                if len(aset) > 1:
                    name = '{} -- {}'.format(aset[0][1], aset[-1][1])
                else:
                    name = aset[0][1]

            # sort by uuid, calculate md5 hash
            h = md5(''.join(sorted((ai[0] for ai in aset))).encode('utf-8')).hexdigest()

            if h not in self._analysis_sets:
                name = '{} ({})'.format(name, datetime.now().strftime('%m/%d/%y'))
                self._analysis_sets[h] = (name, aset)

                if self.max_history:
                    while len(self._analysis_sets) > self.max_history:
                        self._analysis_sets.popitem(last=False)
            return name

    def get_analysis_set(self, name):
        return next((a[1] for a in self._analysis_sets.values() if a[0] == name))

    def set_tags(self, tag, items):
        for i in items:
            ai = next((a for a in self.oanalyses if a.uuid == i.uuid), None)
            if ai:
                ai.set_tag(tag)

        self._analysis_filter_changed(self.analysis_filter)
        self.selected = []

    def remove_invalid(self):
        self.oanalyses = [ai for ai in self.oanalyses if ai.tag != 'invalid']
        self._analysis_filter_changed(self.analysis_filter)

    def add_analyses(self, ans):
        items = self.analyses
        items.extend(ans)
        self.oanalyses = self.analyses = sort_items(items)
        self.calculate_dts(self.analyses)
        # self.scroll_to_row = len(self.analyses) - 1
        self._auto_scroll()

    def clear_non_frozen(self):
        self.analyses = [a for a in self.analyses if a.frozen]
        self.oanalyses = self.analyses
        self.selected = []

    def clear(self):
        self.analyses = []
        self.oanalyses = []
        self.selected = []

    def set_analyses(self, ans, tc=None, page=None, reset_page=False, selected_identifiers=None):
        if selected_identifiers:
            aa = self.analyses
            aa = [ai for ai in aa if ai.identifier in selected_identifiers]
            aa.extend(ans)
        else:
            aa = ans

        new_items = sort_items(aa)
        items = [ai for ai in self.analyses if ai.frozen]

        new_items = [ai for ai in new_items if ai not in items]
        items.extend(new_items)

        self.selected = []
        self.oanalyses = self.analyses = items

        self.calculate_dts(self.analyses)
        self._auto_scroll()

    def calculate_dts(self, ans):
        if ans and len(ans) > 1:
            self._python_dt(ans)

    def _python_dt(self, ans):
        ans = sorted(ans, key=attrgetter('timestampf'))

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

    def remove_others(self):
        self.set_analyses(self.selected)

    def group_selected(self):
        max_gid = max([si.group_id for si in self.analyses]) + 1
        for s in self.get_selected_analyses():
            s.group_id = max_gid

        self.clear_selection()

    def clear_grouping(self):
        for s in self.get_selected_analyses():
            s.group_id = 0

        self.clear_selection()

    def clear_selection(self):
        self.selected = []
        self.refresh_needed = True

    def review_status_details(self):
        from pychron.envisage.browser.review_status_details import ReviewStatusDetailsView, ReviewStatusDetailsModel
        record = self.selected[0]
        self.dvc.sync_repo(record.repository_identifier)
        m = ReviewStatusDetailsModel(record)

        rsd = ReviewStatusDetailsView(model=m)
        rsd.edit_traits()

    def toggle_freeze(self):
        for ai in self.get_selected_analyses():
            ai.frozen = not ai.frozen
        self.refresh_needed = True

    def load_review_status(self):
        records = self.get_analysis_records()
        if records:
            for repoid, rs in groupby_repo(records):

                self.dvc.sync_repo(repoid)
                for ri in rs:
                    get_review_status(ri)
            self.refresh_needed = True

    def get_analysis_records(self):
        records = self.selected
        if not records or (len(records) == 1 and self.one_selected_is_all):
            records = self.analyses

        return records

    # private
    def _auto_scroll(self):
        if self.auto_scroll_kind == TOP:
            self.scroll_to_top = True
        elif self.auto_scroll_kind == BOTTOM:
            self.scroll_to_bottom = True

    # selectsame
    def _get_records(self):
        return self.analyses

    def _get_selection_attrs(self):
        return ['identifier', 'aliquot', 'step', 'comment', 'tag']

    # handlers
    def _refresh_analysis_set_button_fired(self):
        self._analysis_set_changed(self.analysis_set)

        # hack to get the analyses to display
        self.analysis_filter = 'a'
        self.analysis_filter = ''

    def _analysis_set_changed(self, new):
        if self.suppress_load_analysis_set or not new:
            return

        try:
            ans = self.get_analysis_set(new)
            if not ans:
                warning(None, 'Analysis set is empty')
                return

            ans = self.dvc.get_analyses_uuid([a[0] for a in ans])
            if not ans:
                information(None, 'Previously selected analyses not in the current database. This is not fatal. Its '
                                  'ok to continue')
                self.analysis_set = ''
                self.dump()
                return


            ans = progress_bind_records(ans)
            self.set_analyses(ans)
        except StopIteration:
            pass

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
                try:
                    self.oanalyses.remove(ai)
                except ValueError:
                    pass

    def _analysis_filter_changed(self, new):
        if new:
            name = self.analysis_filter_parameter
            self.analyses = fuzzyfinder(new, self.oanalyses, name)
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
        return AnalysisTableConfigurer(id='analysis.table', title='Configure Analysis Table')

    def _analysis_filter_parameter_default(self):
        return 'record_id'

    def _tabular_adapter_default(self):
        adapter = AnalysisAdapter()
        self.table_configurer.set_adapter(adapter)
        return adapter

# ============= EOF =============================================
