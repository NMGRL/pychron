# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Str, Property, cached_property
from traitsui.api import Item, EnumEditor, VGroup
# ============= standard library imports ========================
import os
import re
# ============= local library imports  ==========================
from pychron.pyscripts.commands.core import Command
from pychron.paths import paths
from pychron.extraction_line.valve_parser import ValveParser


name_re=re.compile(r'''name\s*=\s*["']+\w+["']''')
desc_re=re.compile(r'''description\s*=\s*["']+[\w\s]+["']''')
attr_re=re.compile(r'''["']+[\w\s]+["']''')

class ValveCommand(Command):
    valve = Str
    valve_names = Property
    valve_name_dict = Property

    def load_str(self, txt):
        m = name_re.match(txt)
        if m:
            a = self._extract_attr(m)
            if a:
                self.valve = a
                return

        m = desc_re.match(txt)
        if m:
            a = self._extract_attr(m)
            v = next((k for k, v in self.valve_name_dict.iteritems() if v == a), None)
            if v:
                self.valve = v
                return

        if attr_re.match(txt):
            self.valve = txt[1:-1]

    def _extract_attr(self, m):
        name = m.group(0)
        a = attr_re.findall(name)[0]
        if a:
            return a[1:-1]

    def _get_valve_name_dict(self):
        return dict(self.valve_names)

    @cached_property
    def _get_valve_names(self):
        setup_file = os.path.join(paths.extraction_line_dir, 'valves.xml')
        if os.path.isfile(setup_file):
            parser = ValveParser(setup_file)

            valves = [(v.text.strip(),
                          v.find('description').text.strip())
                            for g in parser.get_groups() + [None]
                                for v in parser.get_valves(group=g) ]
            self.valve = valves[0][0]
        else:
            valves = []

        return valves

    def _get_view(self):
        return VGroup(Item('valve', editor=EnumEditor(name='valve_name_dict')),
                      Item('valve', style='readonly', label='Name')
                      )

    def _to_string(self):
        return self._keywords([('name', self.valve),
                               ('description', self.valve_name_dict[self.valve])
                               ])

#        return 'name{}, description={}'.format(self._quote(self.item),
#                                           self._quote(self.items[self.item]))

# ============= EOF =============================================
