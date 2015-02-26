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
from traits.api import HasTraits, List, Any, Property
from traitsui.api import View, UItem, ListEditor, InstanceEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.wait.wait_control import WaitControl

class WaitGroup(HasTraits):
    controls = List
    active_control = Any
    single = Property(depends_on='controls[]')
    def _get_single(self):
        return len(self.controls) == 1

    def traits_view(self):
        v = View(
                 UItem('active_control',
                       style='custom',
                       visible_when='single',
                       editor=InstanceEditor()
                       ),

                 UItem(
                       'controls',
                        editor=ListEditor(
                                         use_notebook=True,
                                         selected='active_control',
                                         page_name='.page_name'
                                         ),
                       style='custom',
                       visible_when='not single'
                       )
                 )
        return v

    def _controls_default(self):
        return [WaitControl()]

    def _active_control_default(self):
        return self.controls[0]

    def pop(self, control=None):
        if len(self.controls) > 1:
            if control:
                if control in self.controls:
                    self.controls.remove(control)
            else:
                self.controls.pop()

            self.active_control = self.controls[-1]

    def stop(self):
        for ci in self.controls:
            ci.stop()

    def add_control(self, **kw):
        if 'page_name' not in kw:
            kw['page_name'] = 'Wait {:02d}'.format(len(self.controls))
        w = WaitControl(**kw)

        self.controls.append(w)
        self.active_control = w

        return w
# ============= EOF =============================================
