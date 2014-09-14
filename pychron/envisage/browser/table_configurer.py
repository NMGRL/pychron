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

from traits.api import HasTraits, List, Any, Bool, Int, Instance, Enum
from traits.trait_errors import TraitError
from traitsui.api import View, Item, UItem, CheckListEditor, VGroup, Handler, HGroup, Tabbed
import apptools.sweet_pickle as pickle
# ============= standard library imports ========================
from datetime import datetime
import os
#============= local library imports  ==========================
from pychron.paths import paths

SIZES = (6, 8, 9, 10, 11, 12, 14, 15, 18, 24, 36)


class TableConfigurerHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            info.object.closed()
            # info.object.dump()
            # info.object.set_columns()


class TableConfigurer(HasTraits):
    columns = List
    available_columns = List
    adapter = Any
    id = 'table'
    font = Enum(*SIZES)

    def closed(self):
        self.dump()
        self.set_columns()
        self.set_font()


    def load(self):
        self._load_state()

    def dump(self):
        self._dump_state()

    def _adapter_changed(self, adp):
        if adp:
            acols = [c for c, _ in adp.all_columns]

            #set currently visible columns
            t = [c for c, _ in adp.columns]
            cols = [c for c in acols if c in t]

            self.trait_setq(columns=cols)

            #set all available columns
            self.available_columns = acols

            self._set_font(adp.font)
            self._load_state()

    def _set_font(self, f):
        s = f.pointSize()
        self.font = s

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

            font = state.get('font', None)
            if font:
                self.font = font

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
        obj = dict(columns=self.columns,
                   font=self.font)
        return obj

    def _load_hook(self, state):
        pass

    def set_font(self):
        if self.adapter:
            self.adapter.font = 'arial {}'.format(self.font)

    def set_columns(self):
        # def _columns_changed(self):
        cols = self._assemble_columns()
        self.adapter.columns = cols

    def _assemble_columns(self):
        d = self.adapter.all_columns_dict
        return [(k, d[k]) for k, v in self.adapter.all_columns if k in self.columns]

    def _get_columns_grp(self):
        return


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


class AnalysisTableConfigurer(TableConfigurer):
    id = 'analysis.table'
    limit = Int

    def _get_dump(self):
        obj = super(AnalysisTableConfigurer, self)._get_dump()
        obj['limit'] = self.limit

        return obj

    def _load_hook(self, obj):
        self.limit = obj.get('limit', 500)

    def traits_view(self):
        v = View(VGroup(VGroup(UItem('columns',
                                     style='custom',
                                     editor=CheckListEditor(name='available_columns', cols=3)),
                               label='Columns', show_border=True),
                        # Group(
                        # VGroup(HGroup(Heading('Lower Bound'), UItem('use_low_post')),
                        #            UItem('low_post', style='custom', enabled_when='use_low_post')),
                        #     VGroup(HGroup(Heading('Upper Bound'), UItem('use_high_post')),
                        #            UItem('high_post', style='custom', enabled_when='use_high_post')),
                        #     VGroup(HGroup(Heading('Named Range'), UItem('use_named_date_range')),
                        #            UItem('named_date_range', enabled_when='use_named_date_range'))),
                        Item('limit',
                             tooltip='Limit number of displayed analyses',
                             label='Limit'),
                        show_border=True,
                        label='Limiting'),
                 buttons=['OK', 'Cancel', 'Revert'],
                 kind='modal',
                 title=self.title,
                 handler=TableConfigurerHandler,
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


class IsotopeTableConfigurer(TableConfigurer):
    id = 'recall.isotopes'

    def traits_view(self):
        v = View(VGroup(UItem('columns',
                              style='custom',
                              editor=CheckListEditor(name='available_columns', cols=3)),
                        Item('font'),
                        show_border=True,
                        label='Isotopes'))
        return v


class IntermediateTableConfigurer(TableConfigurer):
    id = 'recall.intermediate'

    def traits_view(self):
        v = View(VGroup(UItem('columns',
                              style='custom',
                              editor=CheckListEditor(name='available_columns', cols=3)),
                        Item('font'),
                        show_border=True,
                        label='Intermediate'))
        return v


class RecallTableConfigurer(TableConfigurer):
    isotope_table_configurer = Instance(IsotopeTableConfigurer, ())
    intermediate_table_configurer = Instance(IntermediateTableConfigurer, ())
    show_intermediate = Bool
    experiment_fontsize = Enum(*SIZES)
    measurement_fontsize = Enum(*SIZES)
    extraction_fontsize = Enum(*SIZES)

    view_names = ('experiment', 'measurement', 'extraction')
    # def closed(self):
    #     super(RecallTableConfigurer, self).closed()
    #     self.experiment_view

    def _get_dump(self):
        obj = super(RecallTableConfigurer, self)._get_dump()
        obj['show_intermediate'] = self.show_intermediate
        for a in self.view_names:
            a = '{}_fontsize'.format(a)
            obj[a] = getattr(self, a)

        return obj

    def _load_hook(self, obj):
        self.show_intermediate = obj.get('show_intermediate', True)
        self.isotope_table_configurer.load()
        self.intermediate_table_configurer.load()

        for a in self.view_names:
            a = '{}_fontsize'.format(a)
            setattr(self, a, obj.get(a, 10))

    def dump(self):
        super(RecallTableConfigurer, self).dump()
        self.intermediate_table_configurer.dump()
        self.isotope_table_configurer.dump()

    def set_columns(self):
        self.isotope_table_configurer.set_columns()
        self.intermediate_table_configurer.set_columns()

    def set_font(self):
        self.isotope_table_configurer.set_font()
        self.intermediate_table_configurer.set_font()

    def set_fonts(self, av):
        for a in self.view_names:
            s = getattr(self, '{}_fontsize'.format(a))
            av.update_fontsize(a, s)

    def traits_view(self):
        main_view = VGroup(UItem('isotope_table_configurer', style='custom'),
                           HGroup(Item('show_intermediate', label='Show Intermediate Table')),
                           UItem('intermediate_table_configurer', style='custom', enabled_when='show_intermediate'),
                           label='Main')

        experiment_view = VGroup(Item('experiment_fontsize',label='Size'),
                                 show_border=True,
                                 label='Experiment')
        measurement_view = VGroup(Item('measurement_fontsize', label='Size'),
                                  show_border=True,
                                  label='Measurement')
        extraction_view = VGroup(Item('extraction_fontsize', label='Size'),
                                 show_border=True,
                                 label='Extraction')
        v = View(Tabbed(main_view,
                        VGroup(experiment_view,
                        measurement_view,
                        extraction_view, label='Text')),
                 buttons=['OK', 'Cancel', 'Revert'],
                 kind='modal',
                 title='Configure Table',
                 handler=TableConfigurerHandler,
                 resizable=True,
                 width=300)
        return v

#============= EOF =============================================
