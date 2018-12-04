# ===============================================================================
# Copyright 2018 ross
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
import os
import re
import shutil

from apptools.preferences.preference_binding import bind_preference
from traits.api import Str, List, Button, HasTraits, Any
from traitsui.api import View, HGroup, UItem, EnumEditor, Item, VGroup, TabularEditor, TextEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.extraction_line.switch_parser import SwitchParser
from pychron.loggable import Loggable
from pychron.paths import r_mkdir


class ScriptItem(HasTraits):
    path = Str
    name = Str

    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.directory = os.path.dirname(path)


class ScriptItemAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Directory', 'directory')]


PATTERN = '[\'\"]{}[\'\"]'


class SwitchRenamer(Loggable):
    description = Str
    descriptions = List
    new_description = Str

    scan_button = Button
    apply_button = Button
    valves_path = Str
    script_root = Str
    script_text = Str

    found = List
    selected = Any

    def __init__(self, *args, **kw):
        super(SwitchRenamer, self).__init__(*args, **kw)

        if not self.valves_path:
            bind_preference(self, 'valves_path', 'pychron.extraction_line.valves_path')

        if not self.script_root:
            from pychron.paths import paths
            self.script_root = paths.scripts_dir

        self._load_descriptions()

    # private
    def _selected_changed(self, new):
        if len(new) == 1:
            with open(new[0].path, 'r') as rfile:
                self.script_text = rfile.read()
        else:
            self.script_text = ''

    def _apply_button_fired(self):
        sel = self.selected
        if not sel:
            sel = self.found

        for s in sel:
            root = self.script_root
            dest = os.path.join(root, 'backup', os.path.relpath(s.directory, root))
            r_mkdir(dest)

            destpath = os.path.join(dest, s.name)

            self.info('backup script to {}'.format(destpath))
            shutil.copyfile(s.path, destpath)

            self._modify_file(s.path)

            self.info('updated script {}'.format(s.path))

        self._update_valve()
        self._scan()

    def _update_valve(self):
        src = self.valves_path
        dest = os.path.join(os.path.dirname(src), '~{}'.format(os.path.basename(src)))
        shutil.copyfile(src, dest)
        self._modify_file(src)

    def _modify_file(self, path):
        with open(path, 'r') as rfile:
            text = rfile.read()

        with open(path, 'w') as wfile:
            pattern = PATTERN.format(self.description)
            re.sub(pattern, '"{}"'.format(self.new_description), text)
            wfile.write(text)

    def _scan_button_fired(self):
        self._scan()

    def _scan(self):
        found = []
        exclude = ['zobs', 'zbos', 'backup']
        self.info('scanning {}'.format(self.script_root))
        for root, subdirs, files in os.walk(self.script_root, topdown=True):
            subdirs[:] = [d for d in subdirs if d not in exclude]

            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    if self._find_description(path):
                        found.append(ScriptItem(path))

        self.found = found
        self.selected = []

    def _find_description(self, path):
        pattern = re.compile(PATTERN.format(self.description))
        with open(path, 'r') as rfile:
            for line in rfile:
                if pattern.search(line):
                    return True

    def _load_descriptions(self):
        descriptions = []
        parser = SwitchParser()
        if not parser.load(self.valves_path):
            self.warning_dialog('"{}" not a valid file'.format(self.valves_path))
        else:

            for v in parser.get_all_switches():
                d = v.find('description')
                if d is not None:
                    descriptions.append(d.text)

        if descriptions:
            self.description = descriptions[0]
        self.descriptions = descriptions

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('description', editor=EnumEditor(name='descriptions')),
                               Item('new_description', width=-250)),
                        HGroup(icon_button_editor('scan_button', 'foo',
                                                  tooltip='Scan pyscripts for occurences of the valve/switch '
                                                          'description'),
                               icon_button_editor('apply_button', 'bar', enabled_when='new_description')),
                        UItem('found', editor=TabularEditor(selected='selected',
                                                            multi_select=True,
                                                            adapter=ScriptItemAdapter())),
                        UItem('script_text',
                              style='custom',
                              editor=TextEditor(read_only=True))),
                 title='Switch Renamer',
                 resizable=True, width=700, height=500)
        return v


if __name__ == '__main__':
    vp = '/Users/ross/Pychron3/setupfiles/extractionline/valves.xml'
    sp = '/Users/ross/Pychron3/scripts'
    v = SwitchRenamer(valves_path=vp, script_root=sp, new_description='foo')
    v.description = 'Outer Pipette 2'
    v.configure_traits()
# ============= EOF =============================================
