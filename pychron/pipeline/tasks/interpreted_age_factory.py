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
from __future__ import absolute_import

from traits.api import List, HasTraits
from traitsui.api import View, Item, TableEditor, EnumEditor, Controller, UItem, VGroup, TextEditor, HGroup, spring
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup
from pychron.pychron_constants import ERROR_TYPES, PLUSMINUS_ONE_SIGMA


class BaseColumn(ObjectColumn):
    text_font = 'arial 10'


class UObjectColumn(BaseColumn):
    editable = False


lithology_grp = VGroup(UItem('lithology_class', editor=EnumEditor(name='lithology_classes')),
                       UItem('lithology_group', editor=EnumEditor(name='lithology_groups')),
                       UItem('lithology_type', editor=EnumEditor(name='lithology_types')),
                       UItem('lithology', editor=EnumEditor(name='lithologies')),
                       show_border=True, label='Lithology')

macrostrat_grp = VGroup(Item('reference'),
                        Item('rlocation'),
                        Item('lat_long'),
                        lithology_grp,
                        show_border=True,
                        label='MacroChron')


class TItem(Item):
    def _editor_default(self):
        return TextEditor(read_only=True, format_str='%0.3f')


preferred_grp = VGroup(
    HGroup(TItem('preferred_age_value', label='Age', format_str='%0.3f'),
           TItem('preferred_age_error', format_str='%0.3f', show_label=False),
           spring,
           UItem('preferred_age_kind')),
    HGroup(TItem('preferred_kca_value', label='K/Ca', format_str='%0.3f'),
           TItem('preferred_kca_error', format_str='%0.3f', show_label=False),
           spring,
           UItem('preferred_kca_kind')),
    HGroup(TItem('preferred_kcl_value', label='K/Cl'),
           TItem('preferred_kcl_error', show_label=False),
           spring,
           UItem('preferred_kcl_kind')),
    HGroup(TItem('preferred_rad40_percent_value', label='%40Ar*'),
           TItem('preferred_rad40_percent_error', show_label=False),
           spring,
           UItem('preferred_rad40_percent_kind')),
    HGroup(TItem('preferred_moles_k39_value', label='mol 39K'),
           TItem('preferred_moles_k39_error', show_label=False),
           spring,
           UItem('preferred_moles_k39_kind')),
    label='Preferred', show_border=True, )

EDIT_VIEW = View(HGroup(preferred_grp,
                        macrostrat_grp))

cols = [
    CheckboxColumn(name='use', label='Save', width=10),
    UObjectColumn(name='identifier', width=50),
    BaseColumn(name='name', width=50),
    BaseColumn(name='repository_identifier',
               width=50,
               editor=EnumEditor(name='controller.repository_identifiers')),
    BaseColumn(name='preferred_age_kind',
               width=50,
               label='Age Type',
               editor=EnumEditor(name='preferred_ages')),

    BaseColumn(name='preferred_age_error_kind',
               label='Age Error Type',
               editor=EnumEditor(values=ERROR_TYPES)),
    UObjectColumn(name='preferred_age_value', format='%0.3f', label='Age',
                  width=70),
    UObjectColumn(name='preferred_age_error', format='%0.4f', label=PLUSMINUS_ONE_SIGMA,
                  width=70)]

editor = TableEditor(columns=cols, orientation='vertical', edit_view=EDIT_VIEW)
VIEW = View(Item('items', show_label=False, editor=editor),
            resizable=True,
            width=800,
            title='Set Interpreted Age',
            kind='livemodal',
            buttons=['OK', 'Cancel'])


class InterpretedAgeFactoryModel(HasTraits):
    items = List


class InterpretedAgeFactoryView(Controller):
    repository_identifiers = List
    traits_view = VIEW


def set_interpreted_age(dvc, ias):
    repos = dvc.get_local_repositories()
    model = InterpretedAgeFactoryModel(items=ias)
    iaf = InterpretedAgeFactoryView(model=model,
                                    repository_identifiers=repos)
    info = iaf.edit_traits()
    if info.result:
        for ia in ias:
            if ia.use:
                dvc.add_interpreted_age(ia)


if __name__ == '__main__':
    m = InterpretedAgeFactoryModel()
    m.items = [InterpretedAgeGroup()]
    c = InterpretedAgeFactoryView(model=m)
    c.configure_traits()
# ============= EOF =============================================
