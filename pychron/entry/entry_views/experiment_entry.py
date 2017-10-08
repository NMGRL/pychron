# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import Str
from traitsui.api import Item, VGroup, UItem

from pychron.core.ui.strings import SpacelessStr
from pychron.entry.entry_views.entry import BaseEntry


class ExperimentIdentifierEntry(BaseEntry):
    tag = 'Experiment Identifier'
    name = SpacelessStr
    description = Str
    help_str = Str('<font>Enter an Experiment ID and optional description.<br/>'
                   'Spaces are not allowed in the Experiment ID.<br/><br/>The Experiment ID is used '
                   'to group a set of analyses that answer a specific geologic question.<br/>For example '
                   'good Experiment IDs are <br/>'
                   '<big>SanJuanBasinDetrital</big>, <big>LatirVolcanicField</big>, or '
                   '<big>KTBoundary</big></font>')

    def _add_item(self):
        return self.dvc.add_experiment(self.name, description=self.description)

    def traits_view(self):
        return self._new_view(UItem('help_str', style='readonly',
                                    style_sheet=''),
                              Item('name',
                                   label='Experiment ID',
                                   tooltip='Enter an experiment identifier. '
                                           'Spaces are not allowed, use underscores (e.g _ ) if necessary'),
                              VGroup(UItem('description', style='custom'),
                                     show_border=True, label='Description (optional)'),
                              title='New Experiment Identifier')


if __name__ == '__main__':
    e = ExperimentIdentifierEntry()
    e.configure_traits()
# ============= EOF =============================================
