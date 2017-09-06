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
from traits.api import HasTraits, Any
from traitsui.api import View, Item


# ============= standard library imports ========================
# ============= local library imports  ==========================
# from canvas.canvas3D.extraction_line_canvas3D import ExtractionLineCanvas3D
# from pychron.canvas.canvas3D.canvas3D_editor import Canvas3DEditor


class ExtractionLineCanvas(HasTraits):
    """
    """
    canvas2D = Any
    manager = Any

    def toggle_item_identify(self, name):
        """
        """
        self._canvas_function('toggle_item_identify', name)

    def refresh(self):
        """
        """
        self._canvas_function('invalidate_and_redraw')

    def get_object(self, name):
        if self.canvas2D:
            obj = self.canvas2D._get_object_by_name(name)
            return obj

    def load_canvas_file(self, *args, **kw):
        """
        """
        self._canvas_function('load_canvas_file', *args, **kw)

    def update_switch_state(self, name, state, *args, **kw):
        """
            do the specific canvas action
        """
        self._canvas_function('update_switch_state', name, state, *args, **kw)

    def update_switch_lock_state(self, name, state, *args, **kw):
        """
            do the specific canvas action
        """
        self._canvas_function('update_switch_lock_state', name, state)

    def update_switch_owned_state(self, name, state, *args, **kw):
        """
            do the specific canvas action
        """
        self._canvas_function('update_switch_owned_state', name, state)

    def _canvas_function(self, func, *args, **kw):
        c = self.canvas2D
        if c:
            getattr(c, func)(*args, **kw)
        else:
            print 'canvas2D not available'

    def _canvas_factory(self):
        from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D

        e = ExtractionLineCanvas2D(
            manager=self.manager)
        return e

    def _canvas2D_default(self):
        return self._canvas_factory()

    def _canvas2D_group(self):
        """
        """

        g = Item('canvas2D',
                 style='custom',
                 show_label=False,
                 editor=ComponentEditor(),
                 label='2D')
        return g

    def traits_view(self):
        """
        """
        c = self._canvas2D_group()
        v = View(c)
        return v

# ============= EOF ====================================
