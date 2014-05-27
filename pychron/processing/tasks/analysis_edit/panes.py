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
    Str, on_trait_change, Bool
from traitsui.api import View, Item, UItem, HGroup, VGroup, spring, EnumEditor, Handler
from pyface.tasks.traits_dock_pane import TraitsDockPane
# from pychron.processing.search.previous_selection import PreviousSelection
import os
import shelve
import hashlib
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.tasks.analysis_edit.table_filter import TableFilter
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.processing.tasks.analysis_edit.ianalysis_edit_tool import IAnalysisEditTool
from pychron.paths import paths
# from pychron.processing.analysis import Marker
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
    refresh_editor_needed = Event

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
                                                  multi_select=True,
                                                  update='update_needed',
                                                  refresh='refresh_needed'))))
        return v

    @property
    def no_update(self):
        return self._no_update


class HistoryTablePane(TablePane, ColumnSorterMixin):
    previous_selection = Any
    previous_selections = List(PreviousSelection)

    _add_tooltip = '''(u) Append unknowns'''
    _replace_tooltip = '''(Shift+u) Replace unknowns'''
    _clear_tooltip = '''Clear unknowns'''
    configure_button = Button
    clear_history_button = Button

    configure_filter_button = Button

    history_limit = Int(10)

    configure_history_tooltip = 'Configure previous selections'
    clear_prev_selection_tooltip = 'Clear previous selections'

    ps_label = Str('Previous Selections')
    cs_label = Property(depends_on='items[]')

    @on_trait_change('append_button, replace_button')
    def _on_append_replace(self):
        self.dump_selection()
        self.load_previous_selections()

    def load(self):
        self.load_previous_selections()

    def dump(self):
        self.dump_selection()

    #===============================================================================
    # previous selections
    #===============================================================================
    def load_previous_selections(self):
        try:
            self._load()
        except BaseException:
            import traceback

            traceback.print_exc()
            self._remove_shelve()

    def dump_selection(self):
        try:
            self._dump_selection()
        except BaseException:
            import traceback

            traceback.print_exc()
            self._remove_shelve()

    def _remove_shelve(self):
        os.unlink(self._get_shelve_path())

    def _load(self):
        d = self._open_shelve()
        keys = sorted(d.keys(), reverse=True)

        def get_value(k):
            try:
                return d[k]
            except BaseException:
                pass

        self.previous_selections = [PreviousSelection([], name='Previous Selections'),
                                    PreviousSelection([], name='')] + [get_value(ki) for ki in keys]
        self.previous_selection = self.previous_selections[0]

    def _dump_selection(self):
        records = self.items
        if not records:
            return

        # this is a set of NonDB analyses so no presistence
        if not hasattr(records[0], 'uuid'):
            return

        def make_name(rec):
            s = rec[0]
            e = rec[-1]
            samples = set((r.sample for r in rec))
            sname = ','.join(samples)
            if len(sname) > 20:
                sname = '{}...'.format(sname[:20])

            if s != e:
                if s.labnumber == e.labnumber:
                    start = s.record_id
                    end = e.aliquot_step_str
                else:
                    start = s.record_id
                    end = e.record_id
                return '{} ({} - {})'.format(sname, start, end)
            else:
                return '{} {}'.format(sname, s.record_id)

        def make_hash(rec):
            md5 = hashlib.md5()
            for r in rec:
                md5.update('{}{}{}'.format(r.uuid, r.group_id, r.graph_id))
            return md5.hexdigest()

        d = self._open_shelve()

        name = make_name(records)
        ha = make_hash(records)
        ha_exists = next((True for pi in d.itervalues() if pi.hash_str == ha), False)

        if not ha_exists:
            keys = sorted(d.keys())
            next_key = '001'
            if keys:
                next_key = '{:03n}'.format(int(keys[-1]) + 1)

            # records = filter(lambda ri: not isinstance(ri, Marker), records)

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

    def _get_shelve_path(self):
        return os.path.join(paths.hidden_dir, '{}_stored_selections'.format(self.id.split('.')[-1]))

    def _open_shelve(self):
        p = self._get_shelve_path()
        d = shelve.open(p)
        return d

    def _get_cs_label(self):
        m = 'Current Selection'
        if self.items:
            m = '{} n= {}'.format(m, len(self.items))
        return m

    def traits_view(self):
        v = View(VGroup(
            HGroup(icon_button_editor('append_button', 'add',
                                      tooltip=self._add_tooltip),
                   icon_button_editor('replace_button', 'arrow_refresh',
                                      tooltip=self._replace_tooltip),
                   icon_button_editor('clear_button', 'delete',
                                      tooltip=self._clear_tooltip),
                   icon_button_editor('configure_filter_button', 'filter',
                                      tooltip='Configure/Apply a filter',
                                      enabled_when='items')),
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
                                                  column_clicked='column_clicked'))),
                 handler=UnknownsHandler())
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
        self.items = []

    def _clear_history_button_fired(self):
        self._remove_shelve()
        self.load_previous_selections()

    def _configure_button_fired(self):
        self.edit_traits(view='configure_view', kind='livemodal')

    def _configure_filter_button_fired(self):
        tf = TableFilter(items=self.items)
        info = tf.edit_traits(kind='livemodal')
        if info.result:
            if not tf.filtered:
                tf.apply_filter()

            self.trait_set(items=tf.items, trait_change_notify=False)
            self.refresh_needed = True
            self.refresh_editor_needed = True


class UnknownsHandler(Handler):
    def group_by_selected(self, info, obj):
        obj.group_by_selected()

    def clear_grouping(self, info, obj):
        obj.clear_grouping()

    def unselect(self, info, obj):
        obj.unselect()


class UnknownsPane(HistoryTablePane):
    id = 'pychron.processing.unknowns'
    name = 'Unknowns'

    def refresh(self):
        self.refresh_editor_needed = True

    def group_by_selected(self):
        max_gid = max([si.group_id for si in self.selected]) + 1

        for si in self.selected:
            si.group_id = max_gid

        self.refresh()

    def clear_grouping(self):
        if len(self.selected) > 1:
            items = self.selected
        else:
            items = self.items

        self._clear_grouping(items)
        self.refresh()

    def unselect(self):
        self.selected=[]
        self.refresh_needed=True

    def _clear_grouping(self, items):
        for si in items:
            si.group_id = 0


class ReferencesPane(HistoryTablePane):
    name = 'References'
    id = 'pychron.processing.references'

    _add_tooltip = '''(r) Append references'''
    _replace_tooltip = ''' (Shift+r) Replace references'''
    _clear_tooltip = '''Clear references'''
    auto_sort = Bool(True)

    def _auto_sort_changed(self):
        if self.auto_sort:
            self.items = self.sort_items(self.items)

    def sort_items(self, it):
        return sorted(it, key=lambda x: x.timestamp)

    def traits_view(self):
        v = View(VGroup(
            HGroup(icon_button_editor('append_button', 'add',
                                      tooltip=self._add_tooltip),
                   icon_button_editor('replace_button', 'arrow_refresh',
                                      tooltip=self._replace_tooltip),
                   icon_button_editor('clear_button', 'delete',
                                      tooltip=self._clear_tooltip),
                   icon_button_editor('configure_filter_button', 'filter',
                                      tooltip='Configure/Apply a filter',
                                      enabled_when='items')),
            HGroup(UItem('previous_selection',
                         editor=EnumEditor(name='previous_selections')),
                   icon_button_editor('configure_button', 'cog',
                                      tooltip=self.configure_history_tooltip)),
            HGroup(spring, CustomLabel('cs_label'), spring, Item('auto_sort')),
            UItem('items', editor=myTabularEditor(adapter=self.adapter_klass(),
                                                  operations=['move', 'delete'],
                                                  editable=True,
                                                  drag_external=True,
                                                  selected='selected',
                                                  dclicked='dclicked',
                                                  refresh='refresh_needed',
                                                  multi_select=True,
                                                  column_clicked='column_clicked'))))
        return v


class ControlsPane(TraitsDockPane):
    #dry_run = Bool(True)
    #save_button = Button('Save')
    tool = Instance(IAnalysisEditTool)
    id = 'pychron.processing.controls'
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
