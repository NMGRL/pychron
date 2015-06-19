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
from traits.api import List
from traitsui.api import View, Item, TableEditor, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.loggable import Loggable
from pychron.pychron_constants import ERROR_TYPES, PLUSMINUS_SIGMA


class InterpretedAgeFactory(Loggable):
    groups = List

    def traits_view(self):
        cols = [ObjectColumn(name='identifier', editable=False),
                ObjectColumn(name='preferred_age_kind',
                             editor=EnumEditor(name='preferred_ages'),
                             label='Age Type'),
                ObjectColumn(name='preferred_age_error_kind',
                             editor=EnumEditor(values=ERROR_TYPES),
                             label='Age Error Type'),
                ObjectColumn(name='preferred_age_value',
                             format='%0.3f', editable=False,
                             label='Age'),
                ObjectColumn(name='preferred_age_error', format='%0.4f', editable=False,
                             label=PLUSMINUS_SIGMA),
                ObjectColumn(name='preferred_kca_kind',
                             label='K/Ca Type',
                             editor=EnumEditor(values=['Weighted Mean', 'Arithmetic Mean'])),
                ObjectColumn(name='preferred_kca_value', format='%0.3f', editable=False,
                             label='K/Ca'),
                ObjectColumn(name='preferred_kca_error', format='%0.4f', editable=False,
                             label=PLUSMINUS_SIGMA),

                ObjectColumn(name='nanalyses',
                             label='N',
                             editable=False),
                ObjectColumn(name='preferred_mswd',
                             label='MSWD',
                             format='%0.3f',
                             editable=False),

                CheckboxColumn(name='use', label='Save DB')]
        editor = TableEditor(columns=cols)
        v = View(Item('groups', show_label=False, editor=editor),
                 resizable=True,
                 title='Set Interpreted Age',
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])

        return v

# ============= EOF =============================================
