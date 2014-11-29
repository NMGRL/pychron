# ===============================================================================
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
# ===============================================================================
from pychron.core.ui import set_qt

set_qt()

# ============= enthought library imports =======================
from traitsui.menu import ToolBar, Action
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Instance, Dict, List
from traitsui.api import View, UItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D


def diff_states(s1, s2):
    """
        return list of new states
    """
    diffs = {}
    for k, v in s1:
        if s1[k] != s2[k]:
            diffs[k] = s1[k]
    return diffs


class ValveState(HasTraits):
    __valves = Dict

    def set_state(self, k, v):
        self.__valves[k] = v

    def diff(self, s1):
        return diff_states(self, s1)

    def __iter__(self):
        return self.__valves.iteritems()

    def __getitem__(self, item):
        return self.__valves[item]

    def get_states(self):
        return self.__valves.copy()

    def set_states(self, v):
        self.__valves = v

    def __repr__(self):
        return ','.join(['{}={}'.format(k, 'open' if v else 'close')
                         for k, v in self.__valves.iteritems()])


class ValveProgrammer(Loggable):
    canvas = Instance(ExtractionLineCanvas2D)
    previous_state = Instance(ValveState)
    current_state = Instance(ValveState)
    states = List

    def assemble(self):
        for si in self.states:
            print si

    def save_state(self):
        self.debug('save state')
        self.states.append(self.previous_state)

        vd = self.current_state.get_states()
        self.previous_state.set_states(vd)

    def clear_state(self):
        self.debug('clear state')

    #extraction_line_canvas protocol
    def set_selected_explanation_item(self, v):
        pass

    def open_valve(self, v, *args, **kw):
        self.current_state.set_state(v, True)
        print self.current_state.diff(self.previous_state)
        return True, True

    def close_valve(self, v, *args, **kw):
        self.current_state.set_state(v, False)
        print self.current_state.diff(self.previous_state)
        return True, True

    def setup(self):
        self.canvas.load_canvas_file('canvas.xml')
        self.previous_state = ValveState()
        self.current_state = ValveState()
        # self.save_state()
        for vi in self.canvas.iter_valves():
            self.previous_state.set_state(vi.name, False)
            self.current_state.set_state(vi.name, False)

    def traits_view(self):
        v = View(UItem('canvas', editor=ComponentEditor()),
                 resizable=True,
                 toolbar=ToolBar(Action(name='Save State',
                                        action='save_state'),
                                 Action(name='Assemble',
                                        action='assemble'),
                 ),
                 width=500)
        return v

    def _canvas_default(self):
        return ExtractionLineCanvas2D(manager=self)


if __name__ == '__main__':
    v = ValveProgrammer()
    v.setup()
    v.configure_traits()

# ============= EOF =============================================

