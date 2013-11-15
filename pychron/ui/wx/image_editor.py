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
from traits.api import List, Any
from traitsui.wx.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory

#=============standard library imports ========================
from wx import Panel, PaintDC, \
    CLIP_CHILDREN, \
    RED_PEN, BitmapFromBuffer
import wx

# import math
# import wx
# from wx._core import EVT_PAINT
#=============local library imports  ==========================
# from ctypes_opencv import  cvCreateImage, CvSize, cvAddS, CvScalar, \
# CvRect, cvSetImageROI, cvResize, cvResetImageROI
# from ctypes_opencv.cxcore import cvZero


class _ImageEditor(Editor):
    '''
    '''

    points = List
    fps = 20
    playTimer = Any
    def init(self, parent):
        '''
        '''
        self.control = self._create_control(parent)
        self.set_tooltip()

    def update_editor(self):
        '''
        '''
        self.control.Refresh()

#    def get_frames(self):
#        '''
#        '''
#
#        obj = self.value
#        try:
#            if obj.frames:
#                return obj.frames
#        except AttributeError:
#            pass

    def _create_control(self, parent, track_mouse=False):
        '''
        '''
        panel = Panel(parent, -1, style=CLIP_CHILDREN)

        self._set_bindings(panel)
        return panel

    def _set_bindings(self, panel):
        self.playTimer = wx.Timer(panel, 5)
        panel.Bind(wx.EVT_TIMER, self.onNextFrame, self.playTimer)
        self.playTimer.Start(1000 / self.fps)

#        panel.Bind(EVT_PAINT, self.onPaint)
#        if track_mouse:
#            panel.Bind(EVT_MOTION, self.onMotion)

#        panel.Bind(EVT_IDLE, self.onIdle)
#        panel.Bind(EVT_LEFT_DOWN, self.onLeftDown)

#    def onLeftDown(self, event):
#        '''
#        '''
#        self.value.mouse_x = x = event.GetX()
#        self.value.mouse_y = y = event.GetY()
#
#        if not self.points:
#            self.points.append((x, y))
#        else:
#            self.points[0] = (x, y)
#
#        self.control.Refresh()
#
#    def onPaint(self, event):
#        '''
#
#        '''
#        self._draw_(event)

#    def onIdle(self, event):
#        self._draw_(event)
#        event.RequestMore()

    def onNextFrame(self, event):
#        pychron = self.get_frames()
#        frames = self.value.frames
#        if frames is not None:
        try:
            frame = self.value.render()
        except AttributeError:
            return

        if not frame:
            return
        try:
            bitmap = frame.to_wx_bitmap()
#            for d in dir(pychron):
#                print d
        except AttributeError, e:
            print e

            bitmap = BitmapFromBuffer(frame.width, frame.height,
                                           frame.data
                                            )
        dc = PaintDC(self.control)
        dc.DrawBitmap(bitmap, 0, 0, False)
#    def onMotion(self, event):
#        '''
#
#        '''
#        #self.value.mouse_x=event.GetX()
#        #self.value.mouse_y=event.GetY()
#        pass

#    def _draw(self, pychron):
#        '''
#        '''
#        if pychron:
#            self._display_images(pychron)
#
# #        if self.points:
# #            self._display_points(dc,self.points)
#
#    def _display_image(self, pychron):
#        '''
#        '''
#
#        if pychron is not None:
#            try:
#                bitmap = pychron.to_wx_bitmap()
#    #            for d in dir(pychron):
#    #                print d
#            except AttributeError, e:
#                print e
#
#                bitmap = BitmapFromBuffer(pychron.width, pychron.height,
#                                               pychron.data
#                                                )
#            dc = PaintDC(self.control)
#            dc.DrawBitmap(bitmap, 0, 0, False)


#    def _display_images(self, pychron):
#        '''
#        '''
#        display = self.value.render_images(pychron)
#        self._display_image(display)

    def _display_crosshair(self, dc, x, y, pen=None):
        '''
        '''
        if not pen:
            pen = RED_PEN
        dc.SetPen(pen)
        dc.CrossHair(x, y)

    def _display_points(self, dc, ptlist, radius=5):
        '''
        '''
        for pt in ptlist:
            params = pt + (radius,)

            dc.DrawCircle(*params)


class ImageEditor(BasicEditorFactory):
    '''
    '''
    klass = _ImageEditor

