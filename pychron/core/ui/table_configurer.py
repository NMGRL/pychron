# ===============================================================================
# Copyright 2013 Jake Ross
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
# ============= standard library imports ========================
import os
import pickle
import shutil
from datetime import datetime

import yaml
from traits.api import HasTraits, List, Bool, Instance, Enum, \
    Str, Callable, Button, Property, Int
from traits.trait_errors import TraitError
from traitsui.api import Item, UItem, CheckListEditor, VGroup, Handler, HGroup
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup
from pychron.core.yaml import yload
from pychron.paths import paths
from pychron.pychron_constants import SIZES


# ============= local library imports  ==========================


class TableConfigurerHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            info.object.closed(is_ok)
            # info.object.dump()
            # info.object.set_columns()


def get_columns_group():
    col_grp = BorderVGroup(UItem('columns',
                                 style='custom',
                                 editor=CheckListEditor(name='available_columns', cols=3)),
                           label='Columns')
    return col_grp


class TableConfigurer(HasTraits):
    columns = List
    children = List(TabularAdapter)
    available_columns = List
    sparse_columns = List
    adapter = Instance(TabularAdapter)
    id = 'table'
    font = Enum(*SIZES)
    auto_set = Bool(False)
    auto_set_str = Str

    fontsize_enabled = Bool(True)
    title = Str('Configure Table')
    refresh_func = Callable
    show_all = Button('Show All')

    set_sparse = Button('Define Sparse')
    toggle_sparse = Button('Toggle Sparse')

    sparse_enabled = Property(depends_on='columns[]')

    _toggle_sparse_enabled = Bool(False)

    default_button = Button('Default')
    defaults_path = Str

    def _get_sparse_enabled(self):
        return self.sparse_columns != self.columns and len(self.columns) < 5

    def __init__(self, *args, **kw):
        super(TableConfigurer, self).__init__(*args, **kw)
        if self.auto_set:
            s = self.auto_set_str
            if not s:
                s = 'font, columns[]'
            self.on_trait_change(self.update, s)

        self._load_state()

    def closed(self, is_ok):
        if is_ok:
            self.dump()
            self.update()

    def load(self):
        self._load_state()

    def dump(self):
        self._dump_state()

    def update(self):
        self.set_font()
        self.set_columns()
        self.set_column_widths()
        self.update_hook()

    def set_column_widths(self, adapter=None):
        if adapter is None:
            adapter = self.adapter

        if adapter:
            ctx = {}
            for w in self.trait_names(kind='column_width'):
                v = getattr(self, w)
                # trim off cw_
                attr = w[3:]
                if hasattr(adapter, attr):
                    setattr(adapter, attr, v)
                    ctx[attr] = v

            try:
                adapter.column_widths = ctx
            except TraitError:
                pass

    def update_hook(self):
        pass

    def set_font(self):
        if self.adapter:
            font = 'arial {}'.format(self.font)
            self.adapter.font = font
            for ci in self.children:
                ci.font = font

            if self.refresh_func:
                self.refresh_func()

    def set_columns(self):
        if self.adapter:
            cols = self._assemble_columns()
            for ci in self.children:
                ci.columns = cols

            cols = [ci for ci in cols if ci in self.adapter.all_columns]
            self.adapter.columns = cols

    def _set_font(self, f):
        s = f.pointSize()
        self.font = s

    def _get_state(self):
        p = os.path.join(paths.appdata_dir, self.id)
        state = None

        if os.path.isfile(p):
            try:
                with open(p, 'rb') as rfile:
                    state = pickle.load(rfile)
            except (pickle.PickleError, OSError, EOFError, TraitError):
                return
        elif os.path.isfile('{}.yaml'.format(p)):
            state = yload('{}.yaml'.format(p))

        return state

    def _load_state(self):
        state = self._get_state()
        if state:
            try:
                self.sparse_columns = state.get('sparse_columns')
            except:
                pass

            cols = state.get('columns')
            if cols:
                ncols = []
                for ai in self.available_columns:
                    if ai in cols:
                        ncols.append(ai)

                self.columns = ncols

            font = state.get('font', None)
            if font:
                self.font = font
            self._load_column_widths(state)
            self._load_hook(state)
            self.update()

    def _dump_state(self):
        p = os.path.join(paths.appdata_dir, self.id)
        obj = self._get_dump()

        with open('{}.yaml'.format(p), 'w') as wfile:
            yaml.dump(obj, wfile)

        # remove the deprecated pickle file
        if os.path.isfile(p):
            shutil.move(p, os.path.join(paths.appdata_dir, '~{}'.format(self.id)))

    def _get_dump(self):
        obj = dict(columns=list(self.columns),
                   font=self.font,
                   sparse_columns=list(self.sparse_columns))

        cws = {w: getattr(self, w) for w in self.trait_names(kind='column_width')}
        obj['column_widths'] = cws
        return obj

    def _add_column_width(self, k):
        self.add_trait(k, Int(kind='column_width'))

    def _load_column_widths(self, state):
        widths = state.get('column_widths')
        if widths:
            for k, v in widths.items():
                if not hasattr(self, k):
                    self._add_column_width(k)
                setattr(self, k, int(v) or 50)

    def _load_hook(self, state):
        pass

    def _assemble_columns(self):
        d = self.adapter.all_columns_dict
        return [(k, d[k]) for k, v in self.adapter.all_columns if k in self.columns]

    def _get_columns_grp(self):
        return

    def _set_defaults(self):
        p = self.defaults_path
        if os.path.isfile(p):
            # import yaml
            # with open(p, 'r') as rfile:
            #     yd = yaml.load(rfile)
            yd = yload(p)
            try:
                self.columns = yd['columns']
            except KeyError:
                pass
            self.set_columns()

    def _default_button_fired(self):
        self._set_defaults()

    def _set_sparse_fired(self):
        self.sparse_columns = self.columns

    def _toggle_sparse_fired(self):
        if self._toggle_sparse_enabled:
            columns = self._prev_columns
        else:
            self._prev_columns = self.columns
            columns = self.sparse_columns

        self.columns = columns
        self.set_columns()

        self._toggle_sparse_enabled = not self._toggle_sparse_enabled

    def _show_all_fired(self):
        self.columns = self.available_columns
        self.set_columns()

    def set_adapter(self, adp):
        self.adapter = adp

        acols = [c for c, _ in adp.all_columns]

        # set currently visible columns
        t = [c for c, _ in adp.columns]

        cols = [c for c in acols if c in t]
        self.trait_set(columns=cols)

        # set all available columns
        self.available_columns = acols
        if adp.font:
            self._set_font(adp.font)

        self._load_state()

        for name in adp.trait_names():
            if name != 'width' and name.endswith('width'):
                tag = 'cw_{}'.format(name)
                if not hasattr(self, tag):
                    self._add_column_width(tag)

                setattr(self, tag, getattr(adp, name))

    def _get_column_width_group(self):
        n = len(self.adapter.all_columns)
        aitems = []
        for label, name in self.adapter.all_columns[:n // 2]:
            aitems.append(Item('cw_{}_width'.format(name), label=label))

        bitems = []
        for label, name in self.adapter.all_columns[n // 2:]:
            bitems.append(Item('cw_{}_width'.format(name), label=label))

        widths_grp = BorderVGroup(HGroup(VGroup(*aitems),
                                         VGroup(*bitems)),
                                  label='Column Widths')
        return widths_grp

    def traits_view(self):
        v = okcancel_view(VGroup(HGroup(UItem('show_all', tooltip='Show all columns'),
                                        UItem('set_sparse',
                                              tooltip='Set the current set of columns to the Sparse Column Set',
                                              enabled_when='sparse_enabled'),
                                        UItem('toggle_sparse',
                                              tooltip='Display only Sparse Column Set'),
                                        UItem('default_button',
                                              tooltip='Set to Laboratory defaults. File located at '
                                                      '[root]/experiments/experiment_defaults.yaml')),
                                 BorderVGroup(UItem('columns',
                                                    style='custom',
                                                    editor=CheckListEditor(name='available_columns', cols=3)),
                                              Item('font', enabled_when='fontsize_enabled'))),
                          handler=TableConfigurerHandler(),
                          title=self.title)
        return v


def str_to_time(lp):
    lp = lp.replace('/', '-')
    if lp.count('-') == 2:
        y = lp.split('-')[-1]
        y = 'y' if len(y) == 2 else 'Y'

        fmt = '%m-%d-%{}'.format(y)
    elif lp.count('-') == 1:
        y = lp.split('-')[-1]
        y = 'y' if len(y) == 2 else 'Y'

        fmt = '%m-%{}'.format(y)
    else:
        fmt = '%Y' if len(lp) == 4 else '%y'

    return datetime.strptime(lp, fmt)


class ExperimentTableConfigurer(TableConfigurer):
    defaults_path = paths.experiment_defaults


def width_test(v):
    return v.startswith('cw') and v.endswith('width')


class SampleTableConfigurer(TableConfigurer):
    title = 'Configure Sample Table'
    id = 'sample.table'
    filter_non_run_samples = Bool(True)

    def _get_dump(self):
        obj = super(SampleTableConfigurer, self)._get_dump()
        obj['filter_non_run_samples'] = self.filter_non_run_samples

        return obj

    def _load_hook(self, obj):
        self.filter_non_run_samples = obj.get('filter_non_run_samples', True)

    def traits_view(self):
        v = okcancel_view(VGroup(get_columns_group(),
                                 Item('filter_non_run_samples',
                                      tooltip='Omit samples that have not been analyzed to date',
                                      label='Exclude Non-Run')),
                          buttons=['OK', 'Cancel', 'Revert'],
                          title=self.title,
                          handler=TableConfigurerHandler,
                          width=300)
        return v

# ============= EOF =============================================
