#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Str, Property, cached_property
from traitsui.api import Item, EnumEditor
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.pyscripts.commands.core import Command
from pychron.paths import paths
from pychron.extraction_line.valve_parser import ValveParser


class ValveCommand(Command):
    valve = Str
    valve_names = Property
    valve_name_dict = Property

    def _get_valve_name_dict(self):
        return dict(self.valve_names)

    @cached_property
    def _get_valve_names(self):
        setup_file = os.path.join(paths.extraction_line_dir, 'valves.xml')
        parser = ValveParser(setup_file)

        valves = [(v.text.strip(),
                      v.find('description').text.strip())
                        for g in parser.get_groups() + [None]
                            for v in parser.get_valves(group=g) ]
        self.valve = valves[0][0]
        return valves

    def _get_view(self):
        return Item('valve', editor=EnumEditor(name='valve_name_dict'))

    def _to_string(self):
        return self._keywords([('name', self.valve),
                               ('description', self.valve_name_dict[self.valve])
                               ])

#        return 'name{}, description={}'.format(self._quote(self.item),
#                                           self._quote(self.items[self.item]))

#============= EOF =============================================
