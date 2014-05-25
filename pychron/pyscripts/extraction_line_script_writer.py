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
import os
import re

from pyface.constant import OK

from pychron.core.ui import set_qt


set_qt()


#============= enthought library imports =======================
from traits.api import HasTraits, Instance, List, Button, Float, \
    on_trait_change, Str, Event, Bool
from pyface.file_dialog import FileDialog

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension, fileiter
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
from pychron.extraction_line.graph.extraction_line_graph import ExtractionLineGraph


class BaseAction(HasTraits):
    name = Str
    value = Str

    def to_string(self):
        return '    {}'.format(self.value)


class ValveAction(HasTraits):
    def to_string(self):
        if self.name == 'close':
            txt = "    close('{}')".format(self.value)
        else:
            txt = "    open('{}')".format(self.value)

        return txt


class SleepAction(BaseAction):
    value = Float
    name = 'sleep'

    def to_string(self):
        return '    sleep({})'.format(self.value)


class InfoAction(BaseAction):
    name = 'info'

    def to_string(self):
        return "    info('{}')".format(self.value)


class ExtractionLineScriptWriter(Loggable):
    canvas = Instance(ExtractionLineCanvas2D)
    network = Instance(ExtractionLineGraph)

    actions = List

    record_valve_actions = Bool(False)
    add_sleep_button = Button('Sleep')
    duration = Float(1.0)

    add_info_button = Button('Info')
    info_str = Str

    script_text = Str
    selected = List
    refresh_needed = Event

    docstring = Str

    def set_default_states(self):
        self.network.set_default_states(self.canvas)

    def open_file(self, p=''):
        if not os.path.isfile(p):
            dlg = FileDialog(action='open', default_directory=paths.extraction_dir)
            if dlg.open() == OK and dlg.path:
                p = dlg.path
        if p:
            self._open_file(p)
            return True

    #elm protocol
    def set_selected_explanation_item(self, obj):
        pass

    def open_valve(self, valve, **kw):
        if self.record_valve_actions:
            self.actions.append(ValveAction(value=valve, name='open'))
        self._update_network(valve, True)
        return True, True

    def close_valve(self, valve, **kw):
        if self.record_valve_actions:
            self.actions.append(ValveAction(value=valve, name='close'))
        self._update_network(valve, False)
        return True, True

    #private
    def _open_file(self, p):

        if not os.path.isfile(p):
            self.debug('{} does not exist'.format(p))
            return
        if not p.endswith('.py'):
            self.debug('{} is not a valid pyscript file'.format(p))
            return

        valve_re = re.compile(r'''(?P<action>(open|close)+)\((name *= *)*['"]{1}(?P<name>[\w\d])+['"]{1}\,*[\w\s]*\)''')
        sleep_re = re.compile(r'''(?P<action>(sleep\())+((?P<value>(\d+.*\d*)))\)''')
        info_re = re.compile(r'''(info\()+['"]{1}(?P<value>[\w\s\d'"]*)['"]{1}\)''')
        actions = []
        with open(p, 'r') as fp:
            docstring_started = False
            has_docstring = False
            ds = []
            for li in fileiter(fp):
                if not has_docstring and (li.startswith('"""') or li.startswith("'''")):
                    if docstring_started:
                        has_docstring = True
                        docstring_started = False
                    else:
                        docstring_started = True
                    continue

                if docstring_started:
                    ds.append(li)
                    continue

                sli = li.strip()
                m = valve_re.match(sli)
                if m:
                    action = m.group('action')
                    name = m.group('name')
                    actions.append(ValveAction(name=action, value=name))
                    continue

                m = sleep_re.match(sli)
                if m:
                    actions.append(SleepAction(value=float(m.group('value'))))
                    continue

                m = info_re.match(sli)
                if m:
                    actions.append(InfoAction(value=m.group('value')))
                    continue

                if li.startswith('def main'):
                    continue

                actions.append(BaseAction(value=sli))

        self.docstring = '\n'.join(ds)
        self.actions = actions

    def _update_network(self, name, state):
        self.network.set_valve_state(name, state)
        self.network.set_canvas_states(self.canvas, name)

    def _generate_text(self):
        print self.docstring
        if self.docstring:
            ds = self.docstring
        else:
            ds = ''

        txt = """'''\n{}'''
def main():
{}""".format(ds,
             '\n'.join([a.to_string() for a in self.actions]))

        self.script_text = txt

    def _refresh(self):
        self.refresh_needed = True
        self._generate_text()

    #handlers
    def _selected_changed(self, new):
        if new:
            new = new[0]
            if isinstance(new, SleepAction):
                self.duration = new.value
            elif isinstance(new, InfoAction):
                self.info_str = new.value

    def _duration_changed(self):
        for si in self.selected:
            if isinstance(si, SleepAction):
                si.value = self.duration

        self._refresh()

    def _info_str_changed(self):
        for si in self.selected:
            if isinstance(si, InfoAction):
                si.value = self.info_str
        self._refresh()

    @on_trait_change('actions[]')
    def _actions_changed(self):
        self._generate_text()

    def save(self):
        dlg = FileDialog(action='save as',
                         default_directory=paths.extraction_dir)
        if dlg.open() == OK:
            p = dlg.path
            if p:
                p = add_extension(p, ext='.py')
                self.debug('saving script to path {}'.format(p))
                with open(p, 'w') as fp:
                    fp.write(self.script_text)

    def _add_sleep_button_fired(self):
        if self.duration:
            self.actions.append(SleepAction(value=self.duration))
        else:
            self.information_dialog('Please set a duration to add a sleep')

    def _add_info_button_fired(self):
        if self.info_str:
            self.actions.append(InfoAction(value=self.info_str))
        else:
            self.information_dialog('Please set a message to add an info')

    def _canvas_default(self):
        elc = ExtractionLineCanvas2D(manager=self,
                                     confirm_open=False)
        elc.load_canvas_file('canvas_config.xml')
        return elc

    def _network_default(self):
        network = ExtractionLineGraph(inherit_state=True)
        p = os.path.join(paths.canvas2D_dir, 'canvas.xml')
        network.load(p)
        return network


# from traitsui.tabular_adapter import TabularAdapter
# from traitsui.api import Controller, View, UItem, Group, HGroup, VGroup, Item, TabularEditor
# from enable.component_editor import ComponentEditor
# from traitsui.menu import Action
# from pychron.core.ui.code_editor import PyScriptCodeEditor
# class ActionsAdapter(TabularAdapter):
#     columns = [('Name', 'name'),
#                ('Value', 'value')]
#
#     def get_bg_color(self, *args, **kw):
#         color = 'white'
#         if self.item.name == 'open':
#             color = 'lightgreen'
#         elif self.item.name == 'close':
#             color = 'lightcoral'
#         return color
#
#
# class ExtractionLineScriptWriterView(Controller):
#     model = ExtractionLineScriptWriter
#
#     def save(self, info):
#         self.model.save()
#
#     def traits_view(self):
#         action_grp = VGroup(HGroup(UItem('add_sleep_button', width=-40),
#                                    UItem('duration')),
#                             HGroup(UItem('add_info_button', width=-40),
#                                    UItem('info_str')),
#                             HGroup(Item('record_valve_actions', label='Record Actions')),
#                             UItem('actions', editor=TabularEditor(adapter=ActionsAdapter(),
#                                                                   operations=['move', 'delete'],
#                                                                   selected='selected',
#                                                                   refresh='refresh_needed',
#                                                                   multi_select=True)))
#
#         canvas_group = HGroup(
#             UItem('canvas', style='custom',
#                   editor=ComponentEditor()),
#             label='Canvas')
#
#         script_group = VGroup(UItem('script_text',
#                                     editor=PyScriptCodeEditor(),
#                                     style='custom'),
#                               label='script')
#
#         tgrp = Group(canvas_group, script_group, layout='tabbed')
#
#         v = View(
#             # tgrp,
#             HGroup(action_grp, tgrp),
#             buttons=['OK', Action(action='save', name='Save')],
#             resizable=True,
#             width=900, height=700)
#         return v
#
#
# if __name__ == '__main__':
#     ew = ExtractionLineScriptWriter()
#     p=os.path.join(paths.extraction_dir, 'foo.py')
#     ew.open_file(p)
#     e = ExtractionLineScriptWriterView(model=ew)
#     e.configure_traits()
#============= EOF =============================================

