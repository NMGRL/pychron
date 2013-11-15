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



##=============enthought library imports=======================
#
##=============standard library imports ========================
# from pylab import *
##=============local library imports  ==========================
# from pychron.helpers.logger_setup import setup
# from ctypes_opencv import cvCreateImage, cvGetSize, cvAcc, cvRunningAvg, \
#    cvLoadImage, cvCreateCameraCapture, cvQueryFrame, cvSaveImage
# from managers.video_manager import VideoManager
#
#
# if __name__ == '__main__':
#    setup('video')
#    vm = VideoManager()
# #    frame=cvLoadImage('/Users/Ross/Desktop/calibration_chamber.png',0)
#    #p='/Users/Ross/Pychrondata/data/video/obamadata/frame950_0.jpg'
#
#    #p='/Users/Ross/Pychrondata/data/video/obamadata/test/frame950_4.jpg'
#    #p='/Users/Ross/Pychrondata/data/video/testframe_red.jpg'
#    #p='/Users/Ross/Pychrondata/data/video/testframe_gradient.jpg'
#    p = '/Users/Ross/Pychrondata/data/video/obamadata/test/'
#
#    result = vm.process_image_dir(p)
#    #print result
#
#
#    setpoints = []
#    mean_rvalues = []
#    mean_bvalues = []
#    mean_gvalues = []
#    #for f, re in result:
#    i = 0
#    while i < len(result):
#        f, re = result[i]
#        r = []
#        g = []
#        b = []
#        setpoints.append(float(f[5:8]))
#        for j in range(5):
#
#            r.append(result[i + j][1].val[0])
#            g.append(result[i + j][1].val[1])
#            b.append(result[i + j][1].val[2])
#        i += 5
#        mean_rvalues.append(sum(r) / 5.0)
#        mean_gvalues.append(sum(g) / 5.0)
#        mean_bvalues.append(sum(b) / 5.0)
#
#
#    r = array(mean_rvalues)
#    g = array(mean_gvalues)
#    b = array(mean_bvalues)
#    x = array(setpoints)
#    print x, r
#    plot(x, r, 'r')
#    plot(x, g, 'g')
#    plot(x, b)
#    show()
#    #print vm.process_path(p)
#    #vm.load_image(path=p)
#   # vm.threshold=20
#    #for i in range(360):
#    #    vm.angle=i
#
#
#    #vm.threshold=161
#    #vm.angle=60
#    #vm.configure_traits(view='image_view')
