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
from traits.api import HasTraits, Str, Int, Any, on_trait_change, List, Event, Button, Date
from traitsui.api import View, UItem, Item, HGroup, VGroup, EnumEditor, spring
from traitsui.editors import DateEditor
from traitsui.handler import Controller, Handler
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter
from pyface.action.menu_manager import MenuManager
# ============= standard library imports ========================
from datetime import datetime, timedelta
import os
import pickle
# ============= local library imports  ==========================
from pychron.core.progress import progress_loader
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths


class TimeViewAdapter(TabularAdapter):
    columns = [('Date', 'rundate'),
               ('RunID', 'record_id'),
               ('Type', 'analysis_type'),
               ('Sample', 'sample'),
               ('Spectrometer', 'mass_spectrometer'),
               ('Project', 'project'),
               ('Irrad.', 'irradiation_info'),
               ('Device', 'extract_device')]

    record_id_width = Int(80)
    analysis_type_width = Int(80)
    sample_width = Int(95)
    project_width = Int(95)
    rundate_width = Int(95)
    irradiation_info_width = Int(60)
    mass_spectrometer_width = Int(80)
    extract_device_width = Int(95)
    font = 'Helvetica 9'

    def get_menu(self, obj, trait, row, column):
        if obj.context_menu_enabled:
            e = obj.append_replace_enabled
            actions = [Action(name='Unselect', action='unselect_analyses'),
                       Action(name='Replace', action='replace_items', enabled=e),
                       Action(name='Append', action='append_items', enabled=e),
                       Action(name='Open', action='recall_items'),
                       Action(name='Open Copy', action='recall_copies')]

            return MenuManager(*actions)


class TVHandler(Handler):
    def recall_copies(self, info, obj):
        if obj.selected:
            obj.context_menu_event = ('open', {'open_copy': True})

    def recall_items(self, info, obj):
        if obj.selected:
            obj.context_menu_event = ('open', {'open_copy': False})

    def unselect_analyses(self, info, obj):
        obj.selected = []

    def replace_items(self, info, obj):
        if obj.selected:
            obj.context_menu_event = ('replace', None)

    def append_items(self, info, obj):
        if obj.selected:
            obj.context_menu_event = ('append', None)


ATimeView = View(VGroup(icon_button_editor('clear_filter_button', 'clear'),
                        HGroup(UItem('help_str', style='readonly'), label='Help', show_border=True),
                        VGroup(
                            HGroup(UItem('mass_spectrometer', editor=EnumEditor(name='available_mass_spectrometers')),
                                   UItem('analysis_type', editor=EnumEditor(name='available_analysis_types')),
                                   UItem('extract_device', editor=EnumEditor(name='available_extract_devices'))),
                            HGroup(Item('lowdays', label='Greater Than'),
                                   UItem('lowdate', editor=DateEditor(strftime='%m/%d/%Y'),
                                         style='readonly'),
                                   spring,
                                   Item('highdays', label='Less Than'),
                                   UItem('highdate', editor=DateEditor(strftime='%m/%d/%Y'),
                                         style='readonly'),
                                   spring,
                                   Item('limit')),
                            label='Filter', show_border=True),
                        UItem('analyses', editor=myTabularEditor(adapter=TimeViewAdapter(),
                                                                 column_clicked='column_clicked',
                                                                 selected='selected',
                                                                 multi_select=True,
                                                                 refresh='refresh_table_needed',
                                                                 dclicked='dclicked',
                                                                 editable=False))))


class TimeViewModel(HasTraits):
    db = Any
    oanalyses = List
    analyses = List
    column_clicked = Event
    dclicked = Event
    selected = List
    refresh_table_needed = Event
    clear_filter_button = Button
    help_str = 'Select an analysis. Click on the column label to filter results by the selected value'

    mass_spectrometer = Str
    analysis_type = Str
    extract_device = Str
    available_mass_spectrometers = List
    available_analysis_types = List
    available_extract_devices = List

    highdays = Int(0, enter_set=True, auto_set=False)
    lowdays = Int(30, enter_set=True, auto_set=False)
    lowdate = Date
    highdate = Date
    limit = Int(500)
    # days_spacer = Int(10000)
    _suppress_load_analyses = False
    context_menu_event = Event
    context_menu_enabled = True
    append_replace_enabled = True

    @on_trait_change('mass_spectrometer, analysis_type, extract_device, lowdate, highdate, limit')
    def _handle_filter(self):
        ms = self.mass_spectrometer
        at = self.analysis_type
        ed = self.extract_device
        self._load_analyses(mass_spectrometer=ms, analysis_type=at, extract_device=ed)

    def _clear_filter_button_fired(self):
        self.analyses = self.oanalyses
        self.refresh_table_needed = True

    def _column_clicked_changed(self, event):
        if event and self.selected:
            name, field = event.editor.adapter.columns[event.column]
            sattr = getattr(self.selected[0], field)
            self.analyses = [ai for ai in self.analyses if getattr(ai, field) == sattr]
            self.refresh_table_needed = True

    def _highdays_changed(self):
        self.highdate = datetime.now().date() - timedelta(days=self.highdays)

    def _lowdays_changed(self):
        self.lowdate = datetime.now().date() - timedelta(days=self.lowdays)

    def dump_filter(self):
        p = os.path.join(paths.hidden_dir, 'time_view.p')
        with open(p, 'w') as wfile:
            obj = {k: getattr(self, k) for k in
                   ('mass_spectrometer', 'analysis_type', 'extract_device',
                    'lowdays', 'highdays', 'limit')}
            pickle.dump(obj, wfile)

    def load_filter(self):
        p = os.path.join(paths.hidden_dir, 'time_view.p')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                obj = pickle.load(rfile)
                self._suppress_load_analyses = True
                self.trait_set(**obj)
                self._suppress_load_analyses = False
                self._handle_filter()
                return True

    def load(self):
        """
        get a set of analyses from the database.
        load the available mass spectrometers, analysis_types
        :return:
        """
        self._load_available()
        self._suppress_load_analyses = True
        self._highdays_changed()
        self._lowdays_changed()
        self._suppress_load_analyses = False

        if not self.load_filter():
            self._load_analyses()

    def _load_available(self):
        db = self.db
        with db.session_ctx():
            for attr in ('mass_spectrometer', 'analysis_type', 'extract_device'):
                func = getattr(db, 'get_{}s'.format(attr))
                ms = func()
                ms.sort()
                setattr(self, 'available_{}s'.format(attr), [''] + [mi.name for mi in ms])

    def _load_analyses(self, mass_spectrometer=None, analysis_type=None, extract_device=None):
        if self._suppress_load_analyses:
            return

        db = self.db
        with db.session_ctx():
            ma = self.highdate
            mi = self.lowdate
            ans = db.get_analyses_date_range(mi, ma,
                                             mass_spectrometers=mass_spectrometer,
                                             analysis_type=analysis_type,
                                             extract_device=extract_device,
                                             limit=self.limit, order='desc')
            self.oanalyses = self._make_records(ans)
            self.analyses = self.oanalyses[:]

    def _make_records(self, ans):
        def func(xi, prog, i, n):
            if prog:
                prog.change_message('Loading {}'.format(xi.record_id))
            return IsotopeRecordView(xi)

        return progress_loader(ans, func, threshold=25)

    def traits_view(self):
        v = ATimeView
        v.handler = TVHandler()
        return v


class TimeView(Controller):
    model = TimeViewModel

    def closed(self, info, is_ok):
        if is_ok:
            self.model.dump_filter()

    def traits_view(self):
        v = ATimeView

        v.trait_set(resizable=True,
                    width=900,
                    height=500,
                    title='Analysis Time View')
        return v

# ============= EOF =============================================



