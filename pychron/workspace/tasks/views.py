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
from traits.api import HasTraits, Str, Bool, List, Button, Float, Property, Int, Any
from traitsui.api import View, UItem, TableEditor, HGroup, spring, TabularEditor, VGroup, Item
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.helpers.formatting import floatfmt
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pychron_constants import LIGHT_RED_COLOR


class NewBranchView(HasTraits):
    name = Str

    def traits_view(self):
        v = View(UItem('name'),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'], title='New Branch')
        return v


class NewTagView(HasTraits):
    tag_name = Str
    branch = Str

    def traits_view(self):
        v = View(UItem('tag_name'),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'], title='Tag Branch {}'.format(self.branch))
        return v


class Existing(HasTraits):
    name = Str
    recheckout = Bool


class ChooseReheckoutAnalysesView(HasTraits):
    existing = List
    toggle_recheckout = Button
    _toggle_recheckout_state = Bool

    def _toggle_recheckout_fired(self):
        s = self._toggle_recheckout_state
        self._toggle_recheckout_state = s = not s
        for e in self.existing:
            e.recheckout = s

    def get_analyses_to_checkout(self):
        return [e.name for e in self.existing if e.recheckout]

    def get_analyses_to_skip(self):
        return [e.name for e in self.existing if not e.recheckout]

    def __init__(self, existing, *args, **kw):
        self.existing = [Existing(name=os.path.splitext(n)[0]) for n in existing]
        super(ChooseReheckoutAnalysesView, self).__init__(*args, **kw)

    def traits_view(self):
        cols = [CheckboxColumn(name='recheckout', label='Recheckout'),
                ObjectColumn(name='name', editable=False)]
        editor = TableEditor(columns=cols, sortable=False)

        v = View(UItem('existing', editor=editor),
                 HGroup(icon_button_editor('toggle_recheckout', 'tick', tooltip='Toggle recheckout for all analyses'),
                        spring),
                 width=300,
                 resizable=True,
                 title='Choose analyses to recheckout',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v


class DiffAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Left', 'left'),
               ('Right', 'right'), ('Diff', 'diff'), ('%', 'percent_diff')]

    diff_text = Property
    percent_diff_text = Property
    left_text = Property
    right_text = Property

    percent_diff_width = Int(60)

    font = '10'

    def get_bg_color(self, object, trait, row, column=0):
        color = 'white'
        if not object.show_diffs_only and self.item.diff:
            color = LIGHT_RED_COLOR

        return color

    def _get_left_text(self):
        if self.item.name=='lambda_k':
            v = self._floatfmt(self.item.left, use_scientific=True)
        else:
            v = self._floatfmt(self.item.left, n=7)
        return v if v is not None else ''

    def _get_right_text(self):
        if self.item.name=='lambda_k':
            v = self._floatfmt(self.item.right, use_scientific=True)
        else:
            v = self._floatfmt(self.item.right, n=7)

        return v if v is not None else ''

    def _get_diff_text(self):
        if self.item.diff:
            return self._floatfmt(self.item.diff)
        else:
            return ''

    def _get_percent_diff_text(self):
        if self.item.percent_diff:
            return self._floatfmt(self.item.percent_diff, n=2)
        else:
            return ''

    def _floatfmt(self, v, n=4, **kw):
        if isinstance(v, bool):
            return 'X' if v else ''
        else:
            return floatfmt(v, n=n, **kw)


class DiffRecord(HasTraits):
    name = Str
    left = None
    right = None
    diff = Any
    percent_diff = Float

    def __init__(self, name, left, right, *args, **kw):
        self.right = right
        self.left = left
        self.name = name
        if left is not None and right is not None:
            try:
                self.diff = left - right
                try:
                    self.percent_diff = self.diff / self.left * 100
                except ZeroDivisionError:
                    self.percent_diff = 0

            except TypeError:
                self.diff = bool(left!=right)

        super(DiffRecord, self).__init__(*args, **kw)


class DiffView(HasTraits):
    left_summary = Str
    right_summary = Str

    diffs = List
    filtered_diffs = List

    filter_str = Str
    show_diffs_only = Bool

    def __init__(self, left_summary, right_summary, diffs, *args, **kw):
        self.left_summary = left_summary
        self.right_summary = right_summary
        self.diffs = [DiffRecord(*di) for di in diffs]
        self.filtered_diffs = self.diffs[:]
        super(DiffView, self).__init__(*args, **kw)

    def _filter_str_changed(self, new):
        def func(di, sdo):
            try:
                v = getattr(di, 'name')
                r=v.startswith(new)
                if sdo and not di.diff:
                    r=None
                return r
            except AttributeError:
                pass

        sdo=self.show_diffs_only
        self.filtered_diffs = [fi for fi in self.diffs if func(fi, sdo)]

    def _show_diffs_only_changed(self, new):
        if new:
            self.filtered_diffs = [fi for fi in self.filtered_diffs if fi.diff]
        else:
            self._filter_str_changed(self.filter_str)

    def traits_view(self):
        v = View(VGroup(
            VGroup(Item('left_summary', label='Left', style='readonly'),
                   Item('right_summary', label='Right', style='readonly'),
                   HGroup(Item('filter_str',label='Filter'),
                          Item('show_diffs_only'))),
            UItem('filtered_diffs',
                  editor=TabularEditor(
                      editable=False,
                      adapter=DiffAdapter()))),
                 width=600,
                 height=800,
                 title='Diff',
                 resizable=True)
        return v

# ============= EOF =============================================



