# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Either, Int, Float, Str, List, Event, \
    Bool
from traitsui.api import Handler
from traitsui.api import View

# ============= standard library imports ========================
# ============= local library imports  ==========================
# from pychron.utils import IsQt
from pychron.loggable import Loggable


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


class Viewable(Loggable):
    id = ''
    handler_klass = ViewableHandler
    handler = None

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
    resizable = Bool(False)

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
        from pychron.core.ui.gui import invoke_in_main_thread

        self.debug('close ui')
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
        if self.window_height:
            kw['height'] = self.window_height

        if 'resizable' not in kw:
            kw['resizable'] = self.resizable

        if 'title' not in kw:
            kw['title'] = self.title

        if 'id' not in kw and self.id:
            kw['id'] = self.id

        if self.handler:
            kw['handler'] = self.handler
        else:
            kw['handler'] = self.handler_klass()

        return View(*args, **kw)

    def _window_width_default(self):
        return 500

    def _window_height_default(self):
        return 500

    def _window_x_default(self):
        return 0.5

    def _window_y_default(self):
        return 0.5

# ============= EOF =============================================
