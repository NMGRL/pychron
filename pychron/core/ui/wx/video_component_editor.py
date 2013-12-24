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



#============= enthought library imports =======================
from traits.api import Any
#============= standard library imports ========================
# from wx import EVT_IDLE, EVT_PAINT
import wx
#============= local library imports  ==========================
from pychron.lasers.stage_managers.stage_component_editor import LaserComponentEditor, \
    _LaserComponentEditor


class _VideoComponentEditor(_LaserComponentEditor):
    '''
    '''
    playTimer = Any
    def init(self, parent):
        '''
        Finishes initializing the editor by creating the underlying toolkit
        widget.
   
        '''
        super(_VideoComponentEditor, self).init(parent)
#        self.control.Bind(wx.EVT_IDLE, self.onIdle)
#        self.control.Bind(EVT_PAINT, self.onPaint)

        self.playTimer = wx.Timer(self.control)
        self.control.Bind(wx.EVT_TIMER, self.onNextFrame, self.playTimer)
#
        self.playTimer.Start(1000 / self.value.fps)
        self.value.on_trait_change(self.onClose, 'closed_event')

    def onClose(self):
        self.playTimer.Stop()

    def onNextFrame(self, evt):
        if self.control:
            self.control.Refresh()
            evt.Skip()

#    def onIdle(self, event):
# #        '''
# #
# #        '''
#        if self.control is not None:
#            self.control.Refresh()
#            time.sleep(1 / float(self.value.fps))
#            event.Skip()
#            event.RequestMore()

class VideoComponentEditor(LaserComponentEditor):
    '''
    '''
    klass = _VideoComponentEditor

#============= EOF ====================================
