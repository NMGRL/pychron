#===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt

set_qt()


#============= enthought library imports =======================
from traitsui.menu import Action
from traits.api import HasTraits, Instance, List, Button, Float, \
    on_trait_change, Str, Either, Event
from traitsui.api import View, UItem, Controller, TabularEditor, HGroup, VGroup, Item, Group
from traitsui.tabular_adapter import TabularAdapter
from enable.component_editor import ComponentEditor
from pyface.file_dialog import FileDialog

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D


class ELAction(HasTraits):
    name = Str
    value = Either(Float, Str)

    def to_string(self):
        value = self.value
        if value == 'close':
            txt = "    close('{}')".format(self.name)
        elif value == 'open':
            txt = "    open('{}')".format(self.name)
        else:
            txt = '    sleep({})'.format(self.value)

        return txt


class ExtractionLineScriptWriter(Loggable):
    canvas = Instance(ExtractionLineCanvas2D)
    actions = List
    add_sleep_button = Button('Add Sleep')
    duration = Float(1.0)
    script_text = Str
    selected = List
    refresh_needed = Event

    def set_selected_explanation_item(self, obj):
        pass

    def open_valve(self, name, **kw):
        self.actions.append(ELAction(name=name, value='open'))
        return True, True

    def close_valve(self, name, **kw):
        self.actions.append(ELAction(name=name, value='close'))
        return True, True


    def _generate_text(self):
        txt = """'''
'''
def main():
{}""".format('\n'.join([a.to_string() for a in self.actions]))
        self.script_text = txt

    def _selected_changed(self, new):
        if new:
            new = new[0]
            if new.name == 'sleep':
                self.duration = new.value

    def _duration_changed(self):
        for si in self.selected:
            if si.name == 'sleep':
                si.value = self.duration
        self.refresh_needed = True
        self._generate_text()

    @on_trait_change('actions[]')
    def _actions_changed(self):

        self._generate_text()

    def save(self):
        dlg = FileDialog(value='save as',
                         default_directory=paths.extraction_dir)
        dlg.open()
        p = dlg.path
        if p:
            p = add_extension(p, ext='.py')
            self.debug('saving script to path {}'.format(p))
            with open(p, 'w') as fp:
                fp.write(self.script_text)

    def _add_sleep_button_fired(self):
        self.actions.append(ELAction(name='sleep', value=self.duration))

    def _canvas_default(self):
        elc = ExtractionLineCanvas2D(manager=self,
                                     confirm_open=False)
        elc.load_canvas_file('canvas_config.xml')
        return elc


class ActionsAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value')]

    def get_bg_color(self, *args, **kw):
        color = 'white'
        if self.item.value == 'open':
            color = 'lightgreen'
        elif self.item.value == 'close':
            color = 'lightcoral'
        return color


class ExtractionLineScriptWriterView(Controller):
    model = ExtractionLineScriptWriter

    def save(self, info):
        self.model.save()

    def traits_view(self):
        action_grp = VGroup(HGroup(UItem('add_sleep_button'),
                                   Item('duration')),
                            UItem('actions', editor=TabularEditor(adapter=ActionsAdapter(),
                                                                  operations=['move', 'delete'],
                                                                  selected='selected',
                                                                  refresh='refresh_needed',
                                                                  multi_select=True,
                            )))

        canvas_group = HGroup(
            UItem('canvas', style='custom',
                  editor=ComponentEditor()),
            label='Canvas')

        script_group = VGroup(UItem('script_text', style='custom'),
                              label='script')

        tgrp = Group(canvas_group, script_group, layout='tabbed')

        v = View(
            tgrp,
            # HGroup(action_grp, tgrp),
            buttons=['OK', Action(action='save', name='Save')],
            resizable=True,
            width=700, height=700)
        return v


if __name__ == '__main__':
    ew = ExtractionLineScriptWriter()
    e = ExtractionLineScriptWriterView(model=ew)
    e.configure_traits()
#============= EOF =============================================

