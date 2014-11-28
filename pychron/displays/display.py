# ===============================================================================
# Copyright 2013 Jake Ross
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

# ============= enthought library imports =======================
from PySide.QtGui import QColor
from traits.api import HasTraits, Int, Color, Str, Event, Bool
# from traitsui.api import View, UItem
# from pychron.lasers.scanner import ApplicationController
from traitsui.item import UItem
from traitsui.view import View
from pychron.application_controller import ApplicationController
from pychron.core.ui.display_editor import DisplayEditor
# ============= standard library imports ========================
from threading import Lock
from Queue import Queue
# ============= local library imports  ==========================
# from pychron.viewable import Viewable


class DisplayModel(HasTraits):
    # messages = List
    #     max_messages = Int(300)
    #    message = Tuple
    clear_event = Event
    refresh = Event

    # font_size = Int(12)
    # bgcolor = Color('white')
    text_width = Int(10)

    #    message = Queue
    def __init__(self, *args, **kw):
        super(DisplayModel, self).__init__(*args, **kw)

        self.qmessage = Queue()

    def add_text(self, txt, color, force=False, is_marker=False, **kw):
        self.qmessage.put((txt, color, force, is_marker))
        self.refresh = True
        # invoke_in_main_thread(self.trait_set, refresh=True)


class DisplayController(ApplicationController):
    x = Int
    y = Int
    width = Int
    height = Int(500)
    title = Str

    default_color = Color('black')
    # default_size = Int
    bgcolor = Color
    font_name = Str
    font_size = Int(12)
    max_blocks = Int(0)

    editor_klass = DisplayEditor
    _lock = None
    visible = Bool

    opened = Bool(False)
    was_closed = Bool(False)
    text_added = Event

    def __init__(self, *args, **kw):
        super(DisplayController, self).__init__(model=DisplayModel(),
                                                *args, **kw)
        self._lock = Lock()
        self.model.font_size = self.font_size
        self.model.bgcolor = self.bgcolor

    def init(self, info):
        self.opened = True
        super(DisplayController, self).init(info)

    #        print 'rrrrr', info
    #        info.object.ui = info.ui

    def clear(self, **kw):
        #        self.clear_event = True
        self.model.clear_event = True

    #        self.model.clear_event = True
    #         self.model.message=('%%clear%%',)
    #         self.model.messages = []

    # @deprecated
    def freeze(self):
        pass

    # @deprecated
    def thaw(self):
        pass

    def add_marker(self, txt, **kw):
        self.add_text(txt, is_marker=True, **kw)

    def add_text(self, txt, **kw):
        if 'color' not in kw or kw['color'] is None:
            kw['color'] = self.default_color

        tol = 5
        if isinstance(kw['color'], str):
            q = QColor(kw['color'])
            kw['color'] = q

        rgba = kw['color'].toTuple()
        b_rgba = self.bgcolor.toTuple()
        for a, b in zip(rgba, b_rgba):
            if abs(a - b) > tol:
                break
        else:
            r, b, g, a = b_rgba
            kw['color'].setRgb(255 - r, 255 - b, 255 - g, a)

        with self._lock:
            self.model.add_text(txt, **kw)

        self.text_added = True

    def traits_view(self):
        self.visible = True
        editor = self.editor_klass(
            clear='clear_event',
            refresh='refresh',
            font_size='font_size',
            bgcolor='bgcolor',
            text_width='text_width',
            max_blocks=self.max_blocks)

        v = View(UItem('qmessage', editor=editor),
                 x=self.x, y=self.y, width=self.width,
                 height=self.height,
                 title=self.title)
        return v

    def close_ui(self):
        if self.info:
            if self.info.ui:
                self.info.ui.dispose()

    def closed(self, info, result):
        self.opened = False
        self.was_closed = True

    def _bgcolor_changed(self, new):
        if self.model:
            self.model.bgcolor = new

    def _font_size_changed(self, new):
        if self.model:
            self.model.font_size = new


# def show(self):
#        if not self.visible:
#            invoke_in_main_thread(self.edit_traits)
#        elif self.info:
#            self.info.ui.control.raise_()


class ErrorDisplay(DisplayController):
    pass


# ============= EOF =============================================
