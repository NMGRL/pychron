# ===============================================================================
# Copyright 2019 ross
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
from traits.api import List, HasTraits, Str, Int
from traitsui.api import TabularEditor, View, UItem
from traitsui.tabular_adapter import TabularAdapter


class Identifier(HasTraits):
    identifier = Str
    irradiation = Str
    level = Str
    position = Int


class Adapter(TabularAdapter):
    columns = [('Identifier', 'identifier'),
               ('Irradiation', 'irradiation'),
               ('Level', 'level'),
               ('Position', 'position')]


class AssociatedIdentifiersView(HasTraits):
    items = List

    def add_items(self, irposs):
        def factory(irpos):
            i = Identifier(identifier=irpos.identifier,
                           irradiation=irpos.level.irradiation.name,
                           level=irpos.level.name,
                           position=irpos.position)
            return i

        self.items.extend([factory(i) for i in irposs])

    def traits_view(self):
        v = View(UItem('items', editor=TabularEditor(adapter=Adapter())),
                 width=500, resizable=True, title='Associated Irradiation Positions')
        return v
# ============= EOF =============================================
