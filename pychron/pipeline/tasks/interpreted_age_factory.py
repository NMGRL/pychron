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
from traits.api import List, HasTraits, Bool, Str, Instance, on_trait_change
from traitsui.api import View, Item, TableEditor, EnumEditor, Controller, UItem, VGroup
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pychron_constants import ERROR_TYPES, PLUSMINUS_ONE_SIGMA


class InterpretedAgeFactoryModel(HasTraits):
    groups = List


class UObjectColumn(ObjectColumn):
    editable = False
    width = 10


class InterpretedAgeFactoryView(Controller):
    repository_identifiers = List
    macrochron_enabled = Bool(False)

    lith_class = Str
    lith_classes = List

    lith_group = Str
    lith_groups = List

    lith_type = Str
    lith_types = List

    lith = Str
    liths = List

    macrochron = Instance('pychron.macrochron.macrostrat_api.MacroStrat')

    @on_trait_change('lith_class,lith_type,lith_group')
    def _handle_lith_change(self):
        self.macrochron.get_lithologies(lith_class=self.lith_class,
                                        lith_type=self.lith_type,
                                        lith_group=self.lith_group)

    def _edit_view(self):
        lithology_grp = VGroup(UItem('lith_class', editor=EnumEditor(name='lith_classes')),
                               UItem('lith_group', editor=EnumEditor(name='lith_group')),
                               UItem('lith_type', editor=EnumEditor(name='lith_types')),
                               UItem('lith', editor=EnumEditor(name='liths')))

        macrostrat_grp = VGroup(Item('reference'),
                                Item('lat_long'),
                                lithology_grp,
                                defined_when='macrostrat_enabled')
        v = View(Item('preferred_kca_kind'),
                 Item('preferred_kca_value'),
                 UItem('preferred_kca_error'),
                 macrostrat_grp)
        return v

    def traits_view(self):
        cols = [UObjectColumn(name='identifier'),
                ObjectColumn(name='name'),
                ObjectColumn(name='repository_identifier',
                             editor=EnumEditor(name='controller.repository_identifiers')),
                ObjectColumn(name='preferred_age_kind', label='Age Type',
                             editor=EnumEditor(name='preferred_ages')),

                ObjectColumn(name='preferred_age_error_kind', label='Age Error Type',
                             editor=EnumEditor(values=ERROR_TYPES)),
                UObjectColumn(name='preferred_age_value', format='%0.3f', label='Age'),
                UObjectColumn(name='preferred_age_error', format='%0.4f', label=PLUSMINUS_ONE_SIGMA),

                # ObjectColumn(name='preferred_kca_kind', label='K/Ca Type',
                #              editor=EnumEditor(values=['Weighted Mean', 'Arithmetic Mean'])),
                # UObjectColumn(name='preferred_kca_value', format='%0.3f', label='K/Ca'),
                # UObjectColumn(name='preferred_kca_error', format='%0.4f', label=PLUSMINUS_ONE_SIGMA),
                # UObjectColumn(name='nanalyses', label='N'),
                # UObjectColumn(name='preferred_mswd', format='%0.3f', label='MSWD'),
                CheckboxColumn(name='use', label='Save', width=10)]

        editor = TableEditor(columns=cols, edit_view=self._edit_view())
        v = View(Item('groups', show_label=False, editor=editor),
                 resizable=True,
                 title='Set Interpreted Age',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])

        return v


def set_interpreted_age(dvc, ias):
    repos = dvc.get_local_repositories()
    model = InterpretedAgeFactoryModel(groups=ias)
    iaf = InterpretedAgeFactoryView(model=model,
                                    repository_identifiers=repos)
    info = iaf.edit_traits()
    if info.result:
        dvc = dvc
        for ia in ias:
            if ia.use:
                dvc.add_interpreted_age(ia)
# ============= EOF =============================================
