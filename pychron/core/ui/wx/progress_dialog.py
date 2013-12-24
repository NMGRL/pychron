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
from pyface.api import ProgressDialog
#============= standard library imports ========================
from wx import DEFAULT_FRAME_STYLE, FRAME_NO_WINDOW_MENU, \
    CLIP_CHILDREN, VERTICAL, Frame, BoxSizer, NullColor, Size, DisplaySize
#============= local library imports  ==========================

class myProgressDialog(ProgressDialog):

    def get_value(self):
        return self.progress_bar.control.GetValue()

    def increment(self, step=1):
        v = self.get_value()
        self.update(v + step)

    def increase_max(self, step=1):
        self.max += step

    def center(self):
        '''
            center window on screen
        '''

        (w, h) = DisplaySize()
        (ww, _hh) = self.control.GetSize()
        self.control.MoveXY(w / 2 - ww + 275, h / 2 + 150)

    def set_size(self, w, h):
        self.size = (w, h)

    def _create_control(self, parent):
        '''
        '''

        style = DEFAULT_FRAME_STYLE | FRAME_NO_WINDOW_MENU \
            | CLIP_CHILDREN

        dialog = Frame(parent, -1, self.title, style=style)

        sizer = BoxSizer(VERTICAL)
        dialog.SetSizer(sizer)
        dialog.SetAutoLayout(True)
        dialog.SetBackgroundColour(NullColor)

        self.dialog_size = Size(*self.size)

        # The 'guts' of the dialog.

        self._create_message(dialog, sizer)
        self._create_gauge(dialog, sizer)
        self._create_percent(dialog, sizer)
        self._create_timer(dialog, sizer)
        self._create_buttons(dialog, sizer)

        dialog.SetClientSize(self.dialog_size)

        # dialog.CentreOnParent()

        return dialog
#============= EOF =============================================
