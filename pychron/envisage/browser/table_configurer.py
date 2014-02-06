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
import os

from traits.api import HasTraits, List, Any, Bool
from traits.trait_errors import TraitError
from traitsui.api import View, Item, UItem, CheckListEditor, VGroup, Handler
import apptools.sweet_pickle as pickle

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths


class TableConfigurerHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            info.object.dump()
            info.object.set_columns()


class TableConfigurer(HasTraits):
    columns = List
    available_columns = List
    adapter = Any
    id = 'table'

    def load(self):
        self._load_state()

    def dump(self):
        self._dump_state()

    def _adapter_changed(self):
        #cols=self.adapter.column_dict.keys()
        adp = self.adapter

        #acols=adp.ocolumns
        #if not acols:
        #    adp.ocolumns=acols=[c for c,_ in adp.columns]
        acols = [c for c, _ in adp.all_columns]

        t = [c for c, _ in adp.columns]
        cols = [c for c in acols if c in t]

        self.trait_set(columns=cols, trait_change_notify=False)
        self.available_columns = acols
        self._load_state()

    def _load_state(self):
        p = os.path.join(paths.hidden_dir, self.id)
        if os.path.isfile(p):
            try:
                with open(p, 'rb') as fp:
                    state = pickle.load(fp)

            except (pickle.PickleError, OSError, EOFError, TraitError):
                return

            cols = state.get('columns')
            if cols:
                ncols = []
                for ai in self.available_columns:
                    if ai in cols:
                        ncols.append(ai)

                self.columns = ncols

            self._load_hook(state)
            self.set_columns()

    def _dump_state(self):
        p = os.path.join(paths.hidden_dir, self.id)
        obj = self._get_dump()

        with open(p, 'wb') as fp:
            try:
                pickle.dump(obj, fp)
            except pickle.PickleError:
                pass

    def _get_dump(self):
        obj = dict(columns=self.columns)
        return obj

    def _load_hook(self, state):
        pass

    def set_columns(self):
        # def _columns_changed(self):
        cols = self._assemble_columns()
        self.adapter.columns = cols

    def _assemble_columns(self):
        d = self.adapter.all_columns_dict
        return [(k, d[k]) for k, _ in self.adapter.all_columns if k in self.columns]

    def _get_columns_grp(self):
        return

    def traits_view(self):
        v = View(UItem('columns',
                       style='custom',
                       editor=CheckListEditor(name='available_columns', cols=3)),
                 buttons=['OK', 'Revert'],
                 kind='livemodal',
                 handler=TableConfigurerHandler,
                 title=self.title,
                 resizable=True,
                 width=300)
        return v


class SampleTableConfigurer(TableConfigurer):
    title = 'Configure Sample Table'
    # parent = Any
    id = 'sample.table'
    filter_non_run_samples = Bool(True)

    def _get_dump(self):
        obj = super(SampleTableConfigurer, self)._get_dump()
        obj['filter_non_run_samples'] = self.filter_non_run_samples

        return obj

    def _load_hook(self, obj):
        self.filter_non_run_samples = obj.get('filter_non_run_samples', True)

    def traits_view(self):
        v = View(VGroup(
            VGroup(UItem('columns',
                         style='custom',
                         editor=CheckListEditor(name='available_columns', cols=3)),
                   label='Columns', show_border=True),
            Item('filter_non_run_samples',
                 tooltip='Omit samples that have not been analyzed to date',
                 label='Exclude Non-Run')),
                 buttons=['OK', 'Cancel', 'Revert'],
                 kind='modal',
                 title=self.title,
                 handler=TableConfigurerHandler,
                 resizable=True,
                 width=300)
        return v



#    column_mapper={'Sample':'name',
#                   'Material':'material'}
#    available_columns=(['Sample','Material'])
#
#class AnalysisTableConfigurer(HasTraits):
#
#    available_columns=(['Sample','Material'])
#============= EOF =============================================

