#===============================================================================
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
#===============================================================================



#=============enthought library imports=======================
from traits.api import Any, List
from traitsui.basic_editor_factory import BasicEditorFactory

#=============standard library imports ========================
from wx import EVT_IDLE
#=============local library imports  ==========================
from image_editor import _ImageEditor

class _VideoEditor(_ImageEditor):
    '''
    '''

    # storage = Any
    timer = Any
    lines = List
    contours = List



    def get_frames(self, tweak=True):
        '''

        '''
        frame = self.value.get_frame()
        return frame
#        print frame
#        if frame is not None:
#            if tweak:

#            out = cvCreateImage(cvGetSize(frame), 8, 3)


#            return out
    def _set_bindings(self, panel):
        super(VideoEditor, self)._set_bindings(panel)
        panel.Bind(EVT_IDLE, self.onIdle)

    def onIdle(self, event):
        self._draw_(event)
        event.RequestMore()

    def _draw(self, src):
        '''
            @type src: C{str}
            @param src:
        '''
#        dc = ClientDC(self.control)
        self._display_image(src)
        # if self.mouse_x and self.mouse_y:
        #    self._display_crosshair(dc,self.mouse_x,self.mouse_y)


#        size = dc.GetSize()
#        w = size.width / 2.0
#        h = size.height / 2.0

#        self._display_crosshair(dc, w, h, BLACK_PEN)
#        self._display_points(dc, self.points)

class VideoEditor(BasicEditorFactory):
    '''
        G{classtree}
    '''
    klass = _VideoEditor
