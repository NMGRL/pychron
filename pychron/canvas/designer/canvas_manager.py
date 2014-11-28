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



#============= enthought library imports =======================
from traits.api import Instance, Property, DelegatesTo, Event, Bool
from traitsui.api import View, Item, InstanceEditor, ButtonEditor
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from canvas_designer import CanvasDesigner
from pychron.envisage.core.envisage_editor import EnvisageEditor
from pychron.envisage.core.envisage_manager import EnvisageManager
from pychron.paths import paths
class CEditor(EnvisageEditor):
    '''
       
    '''
    id_name = 'Canvas'

class CanvasManager(EnvisageManager):
    '''
       
    '''
    canvas_designer = Instance(CanvasDesigner)
    _selected_item = DelegatesTo('canvas_designer')

    show_hide = Event
    show_hide_label = Property(depends_on='_show_hide')
    _show_hide = Bool

    editor_klass = CEditor
    wildcard = '*.elc'
    default_directory = paths.canvas2D_dir


    def _show_hide_fired(self):
        '''
        '''

        self._show_hide = not self._show_hide
        for item in self.canvas_designer.canvas.items:
            item.identify = self._show_hide

    def _get_show_hide_label(self):
        '''
        '''
        return 'Show all' if not self._show_hide else 'Hide All'

    def _canvas_designer_default(self):
        '''
        '''
        d = CanvasDesigner()
        self.selected = d
        return d

    def new(self):
        '''
        '''
        self.window.workbench.edit(self.canvas_designer,
                         kind=self.editor_klass)

    def open(self, path=None):
        path = self._file_dialog('open')
        if path is not None:
            self.canvas_designer.bootstrap(path)
            self.new()

    def open_default(self):
        '''
        '''

        path = os.path.join(paths.canvas2D_dir, 'canvas.elc')
        if os.path.isfile(path):
            self.canvas_designer.bootstrap(path)

        self.new()

#    def save(self, path = None):
#        '''
#        '''
#        if path is None:
#            path = self.canvas_designer.canvas.file_path
#            print path
#
#        items = self.canvas_designer.canvas.items
#        dlg = FileDialog(action = 'save as', default_directory = canvas2D_dir)
#        if dlg.open() == OK:
#            f = open(dlg.path, 'w')
#            pickle.dump(items, f)
#            f.close()

    def active_canvas_view(self):
        '''
        '''
        v = View(Item('_selected_item', editor=InstanceEditor(), style='custom', show_label=False),
                 Item('show_hide', editor=ButtonEditor(label_value='show_hide_label'),
                      show_label=False)
                 )
        return v

