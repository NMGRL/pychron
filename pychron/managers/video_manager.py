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
from traits.api import Instance, Float, Button, Int, Property, Event, Bool
from traitsui.api import View, Item, HGroup

#=============standard library imports ========================
from threading import Thread
#=============local library imports  ==========================
from pychron.core.ui.stage_component_editor import VideoComponentEditor
from pychron.image.video import Video
from pychron.image.image import Image
from manager import Manager
from pychron.canvas.canvas2D.video_canvas import VideoCanvas
from pychron.core.helpers.filetools import unique_path
from pychron.paths import paths


class VideoManager(Manager):
    """
    """
    video = Instance(Video, ())
    image = Instance(Image, ())

    process = Button
#    pause = Button

    record = Event
    record_label = Property(depends_on='is_recording')
    is_recording = Bool
#    record_button = Button('Record')

    threshold = Float(99, auto_set=False, enter_set=True)
    angle = Float(0, auto_set=False, enter_set=True)
    erosion = Int(0, auto_set=False, enter_set=True)
    dilation = Int(0, auto_set=False, enter_set=True)
    x = Int(0, auto_set=False, enter_set=True)
    y = Int(0, auto_set=False, enter_set=True)

    canvas = Instance(VideoCanvas)
    width = Int(640)
    height = Int(480)
    def open_video(self, **kw):
        self.video.open(**kw)

    def close_video(self, **kw):
        self.video.close(**kw)

    def shutdown(self):
        self.video.shutdown()

    def _get_record_label(self):
        return 'Record' if not self.is_recording else 'Stop'

#    def _pause_fired(self):
#        self.canvas.pause = not self.canvas.pause

    def _record_fired(self):
        def _rec_():
            self.start_recording()
#            time.sleep(4)
#            self.stop_recording()
        if self.is_recording:
            self.is_recording = False
            self.stop_recording()
        else:
            self.is_recording = True
            t = Thread(target=_rec_)
            t.start()


    def start_recording(self, path=None, use_dialog=False):
        '''
        '''
        self.info('start video recording ')
        if path is None:
            if use_dialog:
                path = self.save_file_dialog()
            else:
                path, _ = unique_path(paths.video_dir,
                                      'vm_recording',
                                      extension='avi')

        self.info('saving recording to path {}'.format(path))

        # self.start()
        self.video.start_recording(path)
#        time.sleep(5)
#        self.stop_recording()

    def stop_recording(self):
        '''
        '''
        self.info('stop video recording')
#        self.stop()
        self.video.stop_recording()
        self.is_recording = False

    def start(self, user=None):
        '''
     
        '''
        self.info('opening video connection')
        self.video.open(user=user)

    def stop(self, user=None):
        '''
   
        '''
        self.info('closing video connection')
        self.video.close(user=user)

#    def snapshot(self, identifier=None, path=None, root=None, crop=None):
#        if path is None:
#            if root is None:
#                root = snapshot_dir
#
#            base = 'frame'
#            if identifier is not None:
#                base = 'frame_{}_'.format(identifier)
#
#
#            path, _cnt = unique_path(root=root, base=base, filetype='jpg')
#
#        self.info('saving snapshot {}'.format(path))
#        pychron = self.video.record_frame(path, crop=crop)
#        return pychron, os.path.basename(path)

#        if kind is not None:
#            self.image = globals()['{}Image'.format(kind.capitalize())]()
#            self.image.source_frame = pychron

#    def find_polygons(self, path = None, crop = None):
#        if path:
#            frame = load_image(path, swap = True)
#            if crop:
#                icrop(*((frame,) + crop))
#
#            self.image = CalibrationImage()
#            self.image.source_frame = frame
#
#        return self.image.find_polygons(thresh = self.threshold,
#                           erode_value = self.erosion,
#                           dilate_value = self.dilation)

#    def find_lines(self, path = None, crop = None):
#        if path:
#            frame = load_image(path, swap = True)
#            if crop:
#                icrop(*((frame,) + crop))
#
#            self.image = CalibrationImage()
#            self.image.source_frame = frame
#
#        return self.image.process(thresh = self.threshold,
#                           erode_value = self.erosion,
#                           dilate_value = self.dilation)
#
#    def process_image(self, path = None, angle = None, thresh = None, crop = None, **kw):
#        '''
#        '''
#        if path is None:
#            if self.image is None:
#                frame = self.video.get_frame(clone = True)
#            else:
#                frame = self.image.source_frame
#        else:
#            frame = load_image(path)
#
#        if thresh is None:
#            thresh = self.threshold
#        if angle is None:
#            angle = self.angle
#
#        if self.image is None:
#            self.image = TargetImage()
#
#        if crop:
#            icrop(*((frame,) + crop))
#
#        self.image.source_frame = frame
#
#        #self.load_image(path = path)
#        target = self.image.process(thresh, angle, **kw)
#
#        return target

    def _canvas_default(self):
        return VideoCanvas(video=self.video)

#    def _video_default(self):
#        '''
#        '''
#
#        return Video()

#    def _image_default(self):
#        '''
#        '''
#        return TargetImage()



#    @on_trait_change('threshold,erosion,angle,dilation,x,y')
#    def update(self):
#        '''
#        '''
#        self.find_lines()
# #        p = '/Users/fargo2/Desktop/laser_tray_75.tiff'
#        av = self.process_image(#crop = (self.x, self.y, 250, 250),
#                               # erode = self.erosion,
#                                #dilate = self.dilation
#                                )


    def traits_view(self):
        v = View(
                 HGroup(
                        self._button_factory('record', 'record_label', align='right'),
#                        Item('pause')
                        ),
                 Item('canvas', show_label=False,
                      resizable=False,
                      editor=VideoComponentEditor(width=self.width,
                                                    height=self.height)))
        return v
#
#    def image_view(self):
#        '''
#        '''
#        control_grp = VGroup(Item('threshold', editor=RangeEditor(mode='slider',
#                                                        low=0,
#                                                        high=255)),
# #                                Item('angle', editor = RangeEditor(mode = 'slider',
# #                                                                    low = 0,
# #                                                                    high = 360)),
#                                Item('erosion', editor=RangeEditor(mode='spinner',
#                                                                    low=0,
#                                                                    high=4)),
#                                Item('dilation', editor=RangeEditor(mode='spinner',
#                                                                    low=0,
#                                                                    high=4)))
# #                                Item('x', editor = RangeEditor(mode = 'spinner',
# #                                                                    low = 0,
# #                                                                    high = 500)),
# #                                Item('y', editor = RangeEditor(mode = 'spinner',
# #                                                                    low = 0,
# #                                                                    high = 500)),)
#        return View(
#                    VGroup(control_grp,
#                           Item('image', show_label=False,
#                             editor=ImageEditor())
#                           ),
#                         x=0.05,
#                         y=0.1,
#                         #386365
#                         width=1000,
#                         height=700,
#                         resizable=True,
#                         title=self.title
#                         )

if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('video')
    vm = VideoManager()

    # p = '/Users/fargo2/Desktop/laser_tray_50.tiff'

    # vm.process_image(p, crop=(0, 0, 250, 250))
    vm.start()
    vm.configure_traits()  # view='image_view')



#================== EOF ========================
# def process_image_dir(self, root):
#        '''
#            @type root: C{str}
#            @param root:
#        '''
#        A = 60
#        t = 99
#        results = []
#        if os.path.isdir(root):
#            files = os.listdir(root)
#
#            for f in files:
#                if not f.startswith('.'):
#                    path = os.path.join(root, f)
#                    self.title = f
#
#                    target = self.process_image(path, angle = A, thresh = t)
#
#                    results.append((f, target))
#
#        return results
#
#
# #    def load_image(self, path = None):
# #        '''
# #            @type path: C{str}
# #            @param path:
# #        '''
# #        if path is None:
# #            frame = load_image(path)
# #            self.image.source_frame = frame
#
#
#    def save_frame(self, name = None, frame = None, path = None, root = None):
#        '''
#            @type name: C{str}
#            @param name:
#
#            @type frame: C{str}
#            @param frame:
#
#            @type path: C{str}
#            @param path:
#
#            @type root: C{str}
#            @param root:
#        '''
#        if path is None:
#            pass
#        if root is None:
#            root = os.path.join(paths.data_dir, 'video')
#        if frame is None:
#            frame = self.video.get_frame()
#
#
#        if name is not None:
#            path = os.path.join(root, '%.jpg' % name)
#
#        sp = save_image(frame, root, path = path)
#        self.info('=====image located at %s======' % sp)
#        return sp
#
#    def accumulate_frames(self, setpoint, n, interval):
#        '''
#            @type setpoint: C{str}
#            @param setpoint:
#
#            @type n: C{str}
#            @param n:
#
#            @type interval: C{str}
#            @param interval:
#        '''
#        for i in range(n):
#            self.info('accumulating frame %i' % (i))
#            frame = self.video.get_frame()
#            self.save_frame(frame = frame, name = 'frame%i_%i' % (setpoint, i))
#            time.sleep(interval)
# #        #fi=self.video.get_frame()
# #
# #        #dst=new_dst(fi)
# #        for i in range(n-1):
# #            self.info('accumulating frame %i'%(i))
# #            f=self.video.get_frame()#gray=True)
# #            #cvAcc(f,dst)
# #            time.sleep(interval)
# #
# #        return fi
#
#    def _process_fired(self):
#        '''
#        '''
#        f = self.accumulate_frames(5, 1)
#        self.save_frame(frame = f, name = 'test')

#    def process_frame(self,frame=None,path=None,type='temperature',**kw):
#        self.logger.info('========= processing frame for %s =========='%type)
#
#        if path is not None:
#            #frame=cvLoadImage(path)
#            frame=load_image(path)
#
#        elif frame is None:
#            frame=self.video.get_frame(clone=True,
#                                       flag=CV_CVTIMG_SWAP_RB
#                                       )
#
#        self.image.frames.append(frame)
#        a=self.image
#
#        #locate the ROI
#        self.logger.info('=========== locating target and selecting ROI =========')
#        #a.locate_target()
#
#        #calculate a temperature
#        self.logger.info('============ calculating temperature from ROI =========')
#        #avg= a.get_target_info()
#
#
#        #self.edit_traits(view='image_view')
#        return 10
#        #return avg.val
#   low_threshold=DelegatesTo('image')
#    high_threshold=DelegatesTo('image')
#
#    low_low=DelegatesTo('image')
#    low_high=DelegatesTo('image')
#
#    high_low=DelegatesTo('image')
#    high_high=DelegatesTo('image')
#    process=Button
#    prev_ui=Any
#
#
#    record_button=Event
#    record_label=Property(depends_on='recording')
#    recording=Bool
#
#    snapshot=DelegatesTo('video')
#    def process_view(self):
#        return View(Item('low_threshold',editor=RangeEditor(low_name='low_low',
#                                                            high_name='low_high')),
#                    Item('high_threshold',editor=RangeEditor(low_name='high_low',
#                                                            high_name='high_high',
#                                                            mode='slider')),
#                    Item('image',show_label=False,
#                         editor=ImageEditor()),
#                         x=0.05,
#                         y=0.1,
#                         width=0.75,
#                         height=0.75,
#                         resizable=True,
#                         title='Snapshot View'
#                         )
# #    def _snapshot_fired(self):
# #        directory='/Users/Ross/Pychrondata/data/video'
# #        self.video.record_frame(directory)
#
#    def _record_button_fired(self):
#        if not self.recording:
#            self.logger.info('starting video record')
#
#            self.video.start_recording()
#        else:
#            self.logger.info('stop video record')
#
#        self.recording =not self.recording
#
#    def _get_record_label(self):
#        return 'RECORD' if not self.recording else 'STOP'
#
#    def _high_threshold_changed(self):
#        self.low_high=self.high_threshold
#

#    def _set_center_fired(self):
#        center=self.video.mouse_x,self.video.mouse_y
#
#        #self.video.set_center()
#        print center
#
#        self.image.center=center
