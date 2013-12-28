#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Either, Int, Float, Str, List, Event, \
    Bool
from traitsui.api import View
from traitsui.api import Handler

#============= standard library imports ========================
#============= local library imports  ==========================
# from pychron.utils import IsQt
from pychron.loggable import Loggable
from pychron.core.ui.gui import invoke_in_main_thread


# class ViewableHandler(Controller):
class ViewableHandler(Handler):
    def init(self, info):
#        info.object.ui = info.ui
        info.object.initialized = True
#        try:
        info.object.opened(info.ui)
#        except AttributeError:
#            pass

    def object_activated_changed(self, info):
        if info.initialized:
            if info.ui:
                info.object.set_active(info.ui.control.IsActive())

    def object_disposed_changed(self, info):
        if info.initialized:
            if info.ui:
                info.ui.dispose()

    def object_raised_changed(self, info):
        if info.initialized:
            if info.ui:
                # if IsQt():
                info.ui.control.show()
                # else:
                #     info.ui.control.Raise()

    def close(self, info, is_ok):
        return info.object.close(is_ok)

    def closed(self, info, is_ok):
        info.object.closed(is_ok)
        info.object.close_event = True
        info.object.initialized = False
        return True
#        info.object.ui = None

class Viewable(Loggable):
#    ui = Any
    id = ''
    handler_klass = ViewableHandler

    window_x = Either(Int, Float)
    window_y = Either(Int, Float)

    window_width = Either(Int, Float)
    window_height = Either(Int, Float)

    title = Str
    associated_windows = List

    close_event = Event
    disposed = Event
    raised = Event
    activated = Event

    _is_active = Bool
    initialized = Bool

    def set_active(self, flag):
        self._is_active = flag

    def IsActive(self):
        self.activated = True
        return self._is_active

    def opened(self, ui):
        pass

    def close(self, ok):

        for ai in self.associated_windows:
            ai.close_ui()

        return True
#        return True
#
    def closed(self, ok):
        pass

    def close_ui(self):
        self.debug('disposed')
        invoke_in_main_thread(self.trait_set, disposed=True)

    def show(self, **kw):
        args = tuple()
        if not self.initialized:
            func = self.edit_traits
        else:
            func = self.trait_set
            kw['raised'] = True

        func(*args, **kw)


#     def add_window(self, ui):
#
#         try:
#             if self.application is not None:
#                 self.application.uis.append(ui)
#         except AttributeError:
#             pass
#
#     def open_view(self, obj, **kw):
#         def _open_():
#             ui = obj.edit_traits(**kw)
#             self.add_window(ui)
#
#         invoke_in_main_thread(_open_)
#        _open_()
#        do_after(1, _open_)

    def view_factory(self, *args, **kw):
        if self.window_x:
            kw['x'] = self.window_x
        if self.window_y:
            kw['y'] = self.window_y
        if self.window_width:
            kw['width'] = self.window_width
        if self.window_y:
            kw['height'] = self.window_height

        if not 'resizable' in kw:
            kw['resizable'] = True

        if not 'title' in kw:
            kw['title'] = self.title

        if not 'id' in kw and self.id:
            kw['id'] = self.id

        return View(
                    handler=self.handler_klass,
#                    x=self.window_x,
#                    y=self.window_y,
#                    width=self.window_width,
#                    height=self.window_height,
#                    title=self.title,
#                    resizable=True,
                    *args,
                    **kw
                    )

    def _window_width_default(self):
        return 500

    def _window_height_default(self):
        return 500
    def _window_x_default(self):
        return 0.5

    def _window_y_default(self):
        return 0.5


#============= EOF =============================================
