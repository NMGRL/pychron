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
from traits.api import List, HasTraits
from traitsui.api import View, Item, TableEditor, EnumEditor, Controller
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
    experiment_identifiers = List

    def traits_view(self):
        cols = [UObjectColumn(name='identifier'),
                ObjectColumn(name='name'),
                ObjectColumn(name='experiment_identifier',
                             editor=EnumEditor(name='controller.experiment_identifiers')),
                ObjectColumn(name='preferred_age_kind', label='Age Type',
                             editor=EnumEditor(name='preferred_ages')),
                ObjectColumn(name='preferred_age_error_kind', label='Age Error Type',
                             editor=EnumEditor(values=ERROR_TYPES)),
                UObjectColumn(name='preferred_age_value', format='%0.3f', label='Age'),
                UObjectColumn(name='preferred_age_error', format='%0.4f', label=PLUSMINUS_ONE_SIGMA),
                ObjectColumn(name='preferred_kca_kind', label='K/Ca Type',
                             editor=EnumEditor(values=['Weighted Mean', 'Arithmetic Mean'])),
                UObjectColumn(name='preferred_kca_value', format='%0.3f', label='K/Ca'),
                UObjectColumn(name='preferred_kca_error', format='%0.4f', label=PLUSMINUS_ONE_SIGMA),
                UObjectColumn(name='nanalyses', label='N'),
                UObjectColumn(name='preferred_mswd', format='%0.3f', label='MSWD'),
                CheckboxColumn(name='use', label='Save', width=10)]
        editor = TableEditor(columns=cols)
        v = View(Item('groups', show_label=False, editor=editor),
                 resizable=True,
                 title='Set Interpreted Age',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])

        return v

# ============= EOF =============================================
