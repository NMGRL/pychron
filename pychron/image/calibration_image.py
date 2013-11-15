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
#============= standard library imports ========================

# from numpy import array
#============= local library imports  ==========================
# from image_helper import erode, dilate, draw_squares, draw_rectangle, \
#    new_dst, new_size, new_point, new_mask, new_rect, grayspace, colorspace, threshold, contour, draw_contour_list, \
#    clone, new_seq, avg, rotate, get_polygons, draw_polygons, subsample, \
#    avg_std, get_min_max_location, draw_point, convert_seq, equalize, lines, \
#    crop


from image import Image
from pychron.image.image_helper import grayspace, erode, dilate, \
    threshold, colorspace, contour, clone, get_polygons, draw_polygons, lines

class CalibrationImage(Image):
    '''
    '''
    def find_polygons(self, thresh=0, erode_value=0, dilate_value=0, angle=0):
        self.frames = []
        frame = self.source_frame
        # crop(frame, 150, 150, 300, 300)
        # display original
        # timg = rotate(clone(self.source_frame), angle)
        # self.frames.append(timg)
        self.frames.append(frame)
        gsrc = grayspace(frame)
        gsrc = erode(gsrc, erode_value)
        gsrc = dilate(gsrc, dilate_value)
        gsrc = threshold(gsrc, thresh)

        self.frames.append(colorspace(gsrc))
        # contour the threshold source
        _nc, contours = contour(gsrc)
        if contours:
            # display the contours
            csrc = clone(colorspace(gsrc))
#            draw_contour_list(csrc, contours)

            # approximate and draw polygons from contours
            polygons, br = get_polygons(contours)

            # draw_rectangles(csrc, polygons)
            draw_polygons(csrc, polygons)
            self.frames.append(csrc)
            return br, polygons
        # lsrc, ls = lines(gsrc, thresh = thresh)
        # self.frames.append(lsrc)

    def process(self, thresh=0, erode_value=0, dilate_value=0, angle=0):
        '''
   
        '''

        self.frames = []
        frame = self.source_frame
        # crop(frame, 150, 150, 300, 300)
        # display original
        # timg = rotate(clone(self.source_frame), angle)
        # self.frames.append(timg)
        self.frames.append(frame)
        gsrc = grayspace(frame)
        gsrc = erode(gsrc, erode_value)
        gsrc = dilate(gsrc, dilate_value)
        gsrc = threshold(gsrc, thresh)

        self.frames.append(colorspace(gsrc))
        lsrc, ls = lines(gsrc, thresh=thresh)
        self.frames.append(lsrc)

        vert = []
        horz = []
        for li in ls:
            # find vert
            tol = 5
            if abs(li[0].x - li[1].x) < tol:
#                print 'vert', ((li[0].x + li[1].x) ** 2 + (li[0].y + li[1].y) ** 2) ** 0.5
                vert.append(li)
            elif abs(li[0].y - li[1].y) < tol:
#                print 'hor', ((li[0].x + li[1].x) ** 2 + (li[0].y + li[1].y) ** 2) ** 0.5
                horz.append(li)

        hdist = []
        for hi in horz:
            for hj in horz:
                hdist.append(max([abs(hi[0].y - hj[0].y),
                  abs(hi[0].y - hj[1].y),
                  abs(hi[1].y - hj[1].y),
                  abs(hi[1].y - hj[0].y)]))
        vdist = []
        for vi in vert:
            for vj in vert:
                vdist.append(max([abs(vi[0].x - vj[0].x),
                  abs(vi[0].x - vj[1].x),
                  abs(vi[1].x - vj[1].x),
                  abs(vi[1].x - vj[0].x)]))

        return hdist, vdist

#    def preprocess(self, pychron, erode_value, dilate_value, thresh):
#        '''
#        '''
#        #display original gray scaled
#        gsrc = grayspace(pychron)
#        cgsrc = colorspace(gsrc)
#        gsrc = equalize(gsrc)
#
#        self.frames.append(cgsrc)
#
#        if erode_value:
#            #display an eroded gray scale
#            edst = erode(gsrc, erode_value)
#            #edst=clone(gsrc)
#            #cvErode(edst,edst,0,erode)
#            self.frames.append(colorspace(edst))
#            gsrc = edst
#
#        if dilate_value:
#            #display a dilated gray scale
#            #ddst=clone(gsrc)
#            ddst = dilate(gsrc, dilate_value)
#            self.frames.append(colorspace(ddst))
#            gsrc = ddst
#
#        #threshold and display the gray scale
#        tsrc = threshold(gsrc, thresh)
#
#        self.frames.append(colorspace(tsrc))
#
#        return tsrc






#============= EOF ====================================
