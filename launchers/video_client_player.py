import wx
from threading import Thread, Lock
from numpy import fromstring
import time
from Queue import Queue
from scipy.misc.pilutil import toimage
# Demonstrates how to use wxPython and OpenCV to create a video player
#
# Written by lassytouton
#
# Works with OpenCV 2.3.1
#
# Borrows from "Playing a movie" (http://opencv.willowgarage.com/wiki/wxpython)
#
# Icons film.png, control_stop.png, and control_play.png were sourced from
# Mark James' Silk icon set 1.3 at http://www.famfamfam.com/lab/icons/silk/

# WIDTH = 1280
# HEIGHT = 720
class Client(Thread):
    data = None
    queue = None
    host = '129.138.12.141'
    port = 5556
    use_color = True
    width = 100
    height = 100
    def run(self):
        import zmq
        context = zmq.Context()
        self._sock = context.socket(zmq.SUB)
        self._sock.connect('tcp://{}:{}'.format(self.host,
                                                  self.port))
        self._sock.setsockopt(zmq.SUBSCRIBE, '')

#        wxBmap = wx.EmptyBitmap(1, 1)     # Create a bitmap container object. The size values are dummies.
#        filename = '/Users/ross/Sandbox/snapshot001.jpg'
#        wxBmap.LoadFile(filename, wx.BITMAP_TYPE_ANY)
#        self.data = wxBmap
        fp = 1 / 10.
        while 1:
            t = time.time()
            resp = self._sock.recv()
            header = fromstring(resp)
            w, h, fp, depth = header
            depth = int(depth)
            self.width = w
            self.height = h

            resp = self._sock.recv()
            data = fromstring(resp, dtype='uint8')

            if depth == 3:
                shape = (WIDTH, HEIGHT, 3)
                self.use_color = True
            else:
                self.use_color = False
                shape = (HEIGHT, WIDTH)
                data = data.reshape(*shape)
#
            self.data = data
            time.sleep(max(0.001, fp - (time.time() - t)))

    def get_frame(self):
        return self.data

class VideoClientPlayer(wx.Frame):
    DEFAULT_TOTAL_FRAMES = 300

    ID_OPEN = 1
    ID_SLIDER = 2
    ID_STOP = 3
    ID_PLAY = 4

    ID_TIMER_PLAY = 5
    bmp = None

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, title="pyCan Video Player - Version 1.0.0",
#                          size=dim2,
                          size=(500, 300),
                          style=wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN
                          )

        self.SetDoubleBuffered(True)

        self.client = Client()
        self.client.start()

        self.playing = False

        self.displayPanel = wx.Panel(self, -1)

#        self.displayPanel.SetBackgroundColour('red')
#        self.ToolBar = self.CreateToolBar(style=wx.TB_BOTTOM | wx.TB_FLAT)
#        openFile = self.ToolBar.AddLabelTool(self.ID_OPEN, '', wx.Bitmap('film.png'))
#        self.ToolBar.AddSeparator()
#        self.slider = wx.Slider(self.ToolBar, self.ID_SLIDER, 0, 0, self.DEFAULT_TOTAL_FRAMES - 1, None, (self.DEFAULT_FRAME_WIDTH - 100, 50), wx.SL_HORIZONTAL)
#        self.ToolBar.AddControl(self.slider)
#        self.ToolBar.AddSeparator()

#        stop = self.ToolBar.AddLabelTool(self.ID_STOP, '', wx.Bitmap('control_stop.png'))
#        play = self.ToolBar.AddLabelTool(self.ID_PLAY, '', wx.Bitmap('control_play.png'))

#        self.Bind(wx.EVT_TOOL, self.onOpenFile, openFile)
#        self.Bind(wx.EVT_SLIDER, self.onSlider, self.slider)
#        self.Bind(wx.EVT_TOOL, self.onStop, stop)
#        self.Bind(wx.EVT_TOOL, self.onPlay, play)

        self.playTimer = wx.Timer(self, self.ID_TIMER_PLAY)
        self.Bind(wx.EVT_TIMER, self.onNextFrame, self.playTimer)
#        self.Bind(wx.EVT_IDLE, self.onIdle)
        self.Bind(wx.EVT_PAINT, self.onPaint)

#        self.ToolBar.Realize()
        self.Show(True)
        self.playTimer.Start(1000 / 15.)

    def _get_best_size(self):
        (window_width, _) = self.GetSizeTuple()

        w, h = WIDTH, float(HEIGHT)
        w, h = self.client.width, self.client.height
        new_height = window_width / (w / h)
        new_size = (window_width, new_height)
        return new_size

    def _set_bitmap_size(self, img):
#        if bmp:
        if img:
#            img = wx.ImageFromBitmap(bmp)
            w, h = self._get_best_size()
            img = img.Scale(w, h)
            return img.ConvertToBitmap()

    def updateVideo(self):
        frame = self.client.get_frame()

        if frame is not None:
            if self.client.use_color:
                if self.obmp is None:
                    self.obmp = wx.BitmapFromBuffer(self.client.width,
                                                  self.client.height,
                                                  frame
                                                  )
                else:
                    self.obmp.CopyFromBuffer(frame)
                wimg = self.obmp.ConvertToImage()
            else:
#            print frame.dtype, frame.shape
                img = toimage(frame)
                wimg = wx.EmptyImage(img.size[0], img.size[1])

                wimg.SetData(img.convert('RGB').tostring())
            self.bmp = self._set_bitmap_size(wimg)

        self.Refresh()

    def onNextFrame(self, evt):
        self.updateVideo()
        evt.Skip()

    def onStop(self, evt):
        self.playTimer.Stop()
        self.playing = False

#    def onPlay(self, evt):
# #        fps = cv.GetCaptureProperty(self.capture, cv.CV_CAP_PROP_FPS)
# #        if fps != 0:
# #            self.playTimer.Start(1000 / fps)#every X ms
# #        else:
# #        frame = self.capture.get_frame()
#
#
# #        self.bmp = wx.BitmapFromBuffer(w, h, frame)
# #        self.SetSize((w, h))
#        self.playTimer.Start(1000 / 15)#assuming 15 fps
#        self.playing = True

#    def onIdle(self, evt):
#        pass
#        if (self.capture):
#            if (self.ToolBar.GetToolEnabled(self.ID_OPEN) != (not self.playing)):
#                self.ToolBar.EnableTool(self.ID_OPEN, not self.playing)
#            if (self.slider.Enabled != (not self.playing)):
#                self.slider.Enabled = not self.playing
#            if (self.ToolBar.GetToolEnabled(self.ID_STOP) != self.playing):
#                self.ToolBar.EnableTool(self.ID_STOP, self.playing)
#            if (self.ToolBar.GetToolEnabled(self.ID_PLAY) != (not self.playing)):
#                self.ToolBar.EnableTool(self.ID_PLAY, not self.playing)
#        else:
#            if (not self.ToolBar.GetToolEnabled(self.ID_OPEN)):
#                self.ToolBar.EnableTool(self.ID_OPEN, True)
#            if (self.slider.Enabled):
#                self.slider.Enabled = False
#            if (self.ToolBar.GetToolEnabled(self.ID_STOP)):
#                self.ToolBar.EnableTool(self.ID_STOP, False)
#            if (self.ToolBar.GetToolEnabled(self.ID_PLAY)):
#                self.ToolBar.EnableTool(self.ID_PLAY, False)

    def onPaint(self, evt):
        if self.bmp:
            dc = wx.PaintDC(self)
            dc.DrawBitmap(self.bmp, 0, 0, True)
        else:
            evt.Skip()

if __name__ == "__main__":
    app = wx.App()
    app.RestoreStdio()

    VideoClientPlayer(None)
    app.MainLoop()

    import os
    os._exit(0)
