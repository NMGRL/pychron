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
from datetime import datetime, timedelta
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, List, Event, Button
from traitsui.api import View, UItem, Item, HGroup, VGroup, TabularEditor
from traitsui.handler import Controller
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.progress import progress_loader
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.envisage.icon_button_editor import icon_button_editor


class TimeViewAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('Sample', 'sample'),
               ('Project', 'project'),
               ('Date', 'rundate'),
               ('Irrad.', 'irradiation_info'),
               ('Spectrometer', 'mass_spectrometer'),
               ('Device', 'extract_device')]

    record_id_width = Int(90)
    sample_width = Int(160)
    project_width = Int(120)
    rundate_width = Int(160)
    irradiation_info_width = Int(100)
    mass_spectrometer_width = Int(80)
    extract_device_width = Int(80)


class TimeViewModel(HasTraits):
    oanalyses = List
    analyses = List
    column_clicked=Event
    selected = Any
    refresh_table_needed = Event
    clear_filter_button = Button

    def _clear_filter_button_fired(self):
        self.analyses = self.oanalyses
        self.refresh_table_needed = True

    def _column_clicked_changed(self, event):
        if event and self.selected:
            name, field = event.editor.adapter.columns[event.column]
            sattr = getattr(self.selected, field)
            self.analyses = [ai for ai in self.analyses if getattr(ai, field)==sattr]
            self.refresh_table_needed=True

    def load(self):
        db = self.manager.db
        with db.session_ctx():
            ma = datetime.now()
            mi = ma - timedelta(days=10000)
            ans = db.get_analyses_date_range(mi, ma, limit=50, order='desc')
            self.oanalyses = self._make_records(ans)
            self.analyses = self.oanalyses[:]

    def _make_records(self, ans):
        def func(xi, prog, i, n):
            if prog:
                prog.change_message('Loading {}'.format(xi.record_id))
            return IsotopeRecordView(xi)

        return progress_loader(ans, func, threshold=25)


class TimeView(Controller):
    model = TimeViewModel

    def traits_view(self):
        v = View(VGroup(icon_button_editor('clear_filter_button','clear'),

                                           UItem('analyses', editor=TabularEditor(adapter=TimeViewAdapter(),
                                                        column_clicked='column_clicked',
                                                        selected='selected',
                                                        refresh = 'refresh_table_needed',
                                                        editable=False))),
                 resizable=True,
                 width=900,
                 height=500)
        return v

# ============= EOF =============================================



