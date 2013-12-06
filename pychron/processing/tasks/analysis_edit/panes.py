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
from traits.api import Button, List, Instance, Property, Any, Event, Int, \
    Str
from traitsui.api import View, Item, UItem, HGroup, VGroup, spring, EnumEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
# from pychron.processing.search.previous_selection import PreviousSelection
import os
import shelve
import hashlib
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.ui.custom_label_editor import CustomLabel
from pychron.ui.tabular_editor import myTabularEditor
from pychron.processing.tasks.analysis_edit.ianalysis_edit_tool import IAnalysisEditTool
from pychron.paths import paths
from pychron.processing.analysis import Marker
from pychron.processing.selection.previous_selection import PreviousSelection
from pychron.column_sorter_mixin import ColumnSorterMixin


class TablePane(TraitsDockPane):
    append_button = Button
    replace_button = Button
    clear_button = Button

    items = List

    _no_update = False
    update_needed = Event
    refresh_needed = Event
    selected = Any
    dclicked = Any

    def load(self):
        pass

    def dump(self):
        pass

    def traits_view(self):
        v = View(VGroup(
            UItem('items', editor=myTabularEditor(adapter=self.adapter_klass(),
                                                  operations=['move', 'delete'],
                                                  editable=True,
                                                  drag_external=True,
                                                  selected='selected',
                                                  dclicked='dclicked',
                                                  update='update_needed',
                                                  refresh='refresh_needed'))))
        return v


class HistoryTablePane(TablePane, ColumnSorterMixin):
    previous_selection = Any
    previous_selections = List(PreviousSelection)

    _add_tooltip = '''(u) Append unknowns'''
    _replace_tooltip = '''(Shift+u) Replace unknowns'''
    _clear_tooltip = '''Clear unknowns'''
    configure_button = Button
    clear_history_button = Button

    history_limit = Int(10)

    configure_history_tooltip = 'Configure previous selections'
    clear_prev_selection_tooltip = 'Clear previous selections'

    ps_label = Str('Previous Selections')
    cs_label = Property(depends_on='items[]')

    def load(self):
        self.load_previous_selections()

    def dump(self):
        try:
            self.dump_selection()
        except ImportError:
            pass

    #===============================================================================
    # previous selections
    #===============================================================================
    def load_previous_selections(self):
        d = self._open_shelve()
        keys = sorted(d.keys(), reverse=True)

        def get_value(k):
            try:
                return d[k]
            except Exception:
                pass

        self.previous_selections = [PreviousSelection([], name='Previous Selections'),
                                    PreviousSelection([], name='')] + [get_value(ki) for ki in keys]
        self.previous_selection = self.previous_selections[0]
        #self.previous_selections = filter(None, [get_value(ki) for ki in keys])

    def dump_selection(self):
        records = self.items
        if not records:
            return

        # this is a set of NonDB analyses so no presistence
        if not hasattr(records[0], 'uuid'):
            return

        def make_name(rec):
            s = rec[0]
            e = rec[-1]
            if s != e:
                return '{} - {}'.format(s.record_id, e.record_id)
            else:
                return s.record_id

        def make_hash(rec):
            md5 = hashlib.md5()
            for r in rec:
                md5.update('{}{}{}'.format(r.uuid, r.group_id, r.graph_id))
            return md5.hexdigest()

        try:
            d = self._open_shelve()
        except Exception:
            import traceback

            traceback.print_exc()
            return

        name = make_name(records)
        ha = make_hash(records)
        ha_exists = next((True for pi in d.itervalues() if pi.hash_str == ha), False)

        if not ha_exists:
            keys = sorted(d.keys())
            next_key = '001'
            if keys:
                next_key = '{:03n}'.format(int(keys[-1]) + 1)

            records = filter(lambda ri: not isinstance(ri, Marker), records)

            name_exists = next((True for pi in d.itervalues() if pi.name == name), False)
            if name_exists:
                stored_name = sum([1 for pi in d.itervalues() if pi.name == name])
                if stored_name:
                    name = '{} ({})'.format(name, stored_name)

            ps = PreviousSelection(records, hash_str=ha, name=name)

            d[next_key] = ps

        #trim
        keys = sorted(d.keys())
        t = len(keys)
        n = t - self.history_limit

        if n > 0:
            for ki in keys[:n]:
                d.pop(ki)

        d.close()

    def _open_shelve(self):
        p = os.path.join(paths.hidden_dir, 'stored_selections')
        d = shelve.open(p)
        return d

    def traits_view(self):
        v = View(VGroup(
            HGroup(icon_button_editor('append_button', 'add',
                                      tooltip=self._add_tooltip),
                   icon_button_editor('replace_button', 'arrow_refresh',
                                      tooltip=self._replace_tooltip),
                   icon_button_editor('clear_button', 'delete',
                                      tooltip=self._clear_tooltip),
                   ),
            HGroup(UItem('previous_selection',
                         editor=EnumEditor(name='previous_selections')),
                   icon_button_editor('configure_button', 'cog',
                                      tooltip=self.configure_history_tooltip)),
            HGroup(spring, CustomLabel('cs_label'), spring),
            UItem('items', editor=myTabularEditor(adapter=self.adapter_klass(),
                                                  operations=['move', 'delete'],
                                                  editable=True,
                                                  drag_external=True,
                                                  selected='selected',
                                                  dclicked='dclicked',
                                                  refresh='refresh_needed',
                                                  multi_select=True,
                                                  column_clicked='column_clicked'
            ))))
        return v

    def configure_view(self):
        v = View(
            Item('history_limit', label='Max. N History'),
            icon_button_editor('clear_history_button', 'delete',
                               label='Clear',
                               tooltip=self.clear_prev_selection_tooltip),
            buttons=['OK', 'Cancel', 'Revert'],
            title='Configure History')
        return v

    def _clear_button_fired(self):
        self.items=[]

    def _clear_history_button_fired(self):
        d = self._open_shelve()
        d.update(dict())
        d.close()

    def _configure_button_fired(self):
        self.edit_traits(view='configure_view', kind='livemodal')

    def _get_cs_label(self):
        m = 'Current Selection'
        if self.items:
            m = '{} n= {}'.format(m, len(self.items))
        return m


class UnknownsPane(HistoryTablePane):
    id = 'pychron.analysis_edit.unknowns'
    name = 'Unknowns'


class ReferencesPane(HistoryTablePane):
    name = 'References'
    id = 'pychron.analysis_edit.references'

    _add_tooltip = '''(r) Append references'''
    _replace_tooltip = ''' (Shift+r) Replace references'''
    _clear_tooltip = '''Clear references'''


class ControlsPane(TraitsDockPane):
    #dry_run = Bool(True)
    #save_button = Button('Save')
    tool = Instance(IAnalysisEditTool)
    id = 'pychron.analysis_edit.controls'
    name = 'Controls'

    def traits_view(self):
        v = View(
            VGroup(
                UItem('tool', style='custom'),
                #HGroup(spring, UItem('save_button'), Item('dry_run'))
            )
        )
        return v


#============= EOF =============================================
