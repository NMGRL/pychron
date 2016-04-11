# ===============================================================================
# Copyright 2011 Jake Ross
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
from enable.component_editor import ComponentEditor
from traits.api import Instance, DelegatesTo
from traitsui.api import View, Item

# ============= standard library imports ========================
import os

# ============= local library imports  ==========================
from pychron.canvas.canvas2D.designer_canvas import DesignerCanvas
from pychron.paths import paths
from pychron.envisage.core.envisage_editable import EnvisageEditable
class CanvasDesigner(EnvisageEditable):
    '''
    '''
    canvas = Instance(DesignerCanvas)

    _selected_item = DelegatesTo('canvas')
    file_extension = '.elc'

    def _canvas_default(self):
        '''
        '''
        d = DesignerCanvas()
#        d.items = self._load_fired(d)
        return d
#
    def save(self, path=None):
        oldname, path = self._pre_save(path)
        self._dump_items(path, self.canvas.items)
        return oldname

    def bootstrap(self, path=None):
        '''
        '''

        # self.load_items_from_file()
        self.file_path = path
        self.canvas.bootstrap(path)

    def load_items_from_file(self):
        '''
        '''
        # valves = []
        p = os.path.join(paths.canvas2D_dir, 'canvas.cad')
        f = open(p, 'r')
        lines = f.read().split('\n')
        lines = [l.split(',') for l in lines if l]
        lines = [(l[0], l[1], tuple(l[2:])) for l in lines if len(l) == 4]
        for klass, name, pos in lines:
            self.canvas.add_item(klass, args=dict(name=name, pos=pos), use_editor=False)

        f.close()

# ============= views ===================================

    def traits_view(self):
        '''
        '''
        v = View(
                 Item(
                      'canvas', show_label=False,
                       style='custom',
                       editor=ComponentEditor()
                      ),
             resizable=True,
             width=800,
             height=800
             )
        return v
if __name__ == '__main__':
    c = CanvasDesigner()
    c.configure_traits()
# ============= EOF ====================================
