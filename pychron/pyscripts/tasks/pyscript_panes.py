#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
import os
from traits.api import List, Instance, Str, Property, Any, String, Button
from traitsui.api import View, Item, UItem, InstanceEditor, ButtonEditor, VGroup, TabularEditor, \
    HGroup, spring, VSplit, Label
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traitsui.tabular_adapter import TabularAdapter
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.tabular_editor import myTabularEditor

# from pychron.pyscripts.commands.core import ICommand
#============= standard library imports ========================
#============= local library imports  ==========================

class ControlPane(TraitsDockPane):
    name = 'Control'
    id = 'pychron.pyscript.control'

    def traits_view(self):
        v = View(
            VGroup(
                UItem('execute',
                      editor=ButtonEditor(label_value='execute_label')
                ),
                VGroup(
                    UItem('use_trace'),
                    UItem('trace_delay', label='Delay (ms)'),
                    show_border=True,
                    label='Trace'
                )
            )
        )
        return v


class DescriptionPane(TraitsDockPane):
    name = 'Description'
    id = 'pychron.pyscript.description'

    def traits_view(self):
        v = View(
            UItem('description',
                  style='readonly'
            )

            #                 'object.selected_command_object',
            #                 show_label=False,
            #                 style='custom',
            #                 height=0.25,
            #                 editor=InstanceEditor(view='help_view')
        )
        return v


class ExamplePane(TraitsDockPane):
    name = 'Example'
    id = 'pychron.pyscript.example'

    def traits_view(self):
        v = View(
            UItem('example',
                  style='readonly'
            )

            #                 'object.selected_command_object',
            #                 show_label=False,
            #                 style='custom',
            #                 height=0.25,
            #                 editor=InstanceEditor(view='help_view')
        )
        return v


class EditorPane(TraitsDockPane):
    name = 'Editor'
    id = 'pychron.pyscript.editor'
    editor = Instance('pychron.pyscripts.parameter_editor.ParameterEditor')

    def traits_view(self):
        v = View(UItem('editor', style='custom'))
        return v


class CommandsAdapter(TabularAdapter):
    columns = [('Name', 'name')]
    name_text = Property
    #
    def _get_name_text(self, *args, **kw):
        return self.item


class CommandEditorPane(TraitsDockPane):
    name = 'Commands Editor'
    id = 'pychron.pyscript.commands_editor'
    command_object = Any

    def traits_view(self):
        v = View(UItem('command_object',
                       width=-275,
                       editor=InstanceEditor(),
                       style='custom'))
        return v


class CommandsPane(TraitsDockPane):
    name = 'Commands'
    id = 'pychron.pyscript.commands'

    commands = Property(depends_on='_commands')
    _commands = List
    name = Str

    selected_command = Any
    command_object = Any
    command_objects = List

    def set_command(self, line):
        args=line.split('(')
        cmd=args[0]
        if cmd:
            self.selected_command=cmd
            s='('.join(args[1:])
            s=s[:-1]
            self.command_object.load_str(s)


    def _selected_command_changed(self):
        if self.selected_command:
            obj = next((ci for ci in self.command_objects
                        if ci.name == self.selected_command), None)
            self.command_object = obj

    def _set_commands(self, cs):
        self._commands = cs

    def _get_commands(self):
        return sorted(self._commands)

    def traits_view(self):
        v = View(Item('commands',
                      style='custom',
                      show_label=False,
                      editor=myTabularEditor(operations=['move'],
                                             adapter=CommandsAdapter(),
                                             editable=True,
                                             selected='selected_command'
                      ),
                      width=200,
        )
        )
        return v


class ScriptBrowserAdapter(TabularAdapter):
    columns = [('Name', 'name')]
    name_text = Property

    def _get_name_text(self):
        return self.item


class ScriptBrowserPane(TraitsDockPane):
    id = 'pychron.pyscript.script_browser'
    items = List
    root = String
    selected = String
    dclicked = Any
    directory_dclicked = Any
    selected_directory = String
    selected_directory_name = Property(depends_on='selected_directory')
    up_directory_name = Property(depends_on='selected_directory')
    directories = List
    name = 'Browser'
    up_button = Button
    forward_button = Button

    def _up_button_fired(self):
        self.root = os.path.dirname(self.root)

    def _root_changed(self):
        root = self.root

        ps = [p for p in os.listdir(root)]
        self.items = filter(lambda x: not (x.startswith('.') or os.path.isdir(os.path.join(root, x))), ps)
        self.directories = filter(lambda x: os.path.isdir(os.path.join(root, x)), ps)
        self.selected_directory = self.root

    def _directory_dclicked_changed(self):
        if self.selected_directory:
            p = os.path.join(self.root, self.selected_directory)
            self.root = p

    def traits_view(self):
        v = View(VGroup(HGroup(icon_button_editor('up_button', 'arrow_left', tooltip='Go back one directory'),
                               CustomLabel('up_directory_name', size=14, color='maroon'), spring),
                        VSplit(VGroup(UItem('directories',
                                            editor=TabularEditor(selected='selected_directory',
                                                                 dclicked='directory_dclicked',
                                                                 editable=False,
                                                                 adapter=ScriptBrowserAdapter()),
                                            height=0.25),
                                      HGroup(Label('Current Dir.'), CustomLabel('selected_directory_name',
                                                                                size=14, color='maroon'))),
                               UItem('items', editor=TabularEditor(selected='selected',
                                                                   dclicked='dclicked',
                                                                   editable=False,
                                                                   adapter=ScriptBrowserAdapter()),
                                     height=0.75))))
        return v

    def _get_up_directory_name(self):
        return os.path.basename(os.path.dirname(self.root))

    def _get_selected_directory_name(self):
        return os.path.basename(self.root)

#============= EOF =============================================
