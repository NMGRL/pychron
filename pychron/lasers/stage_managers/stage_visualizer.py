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
import cPickle as pickle

from traits.api import Instance, Str, on_trait_change, \
    Bool, Tuple, Float
from traitsui.api import View, Item
from enable.component_editor import ComponentEditor


# ============= standard library imports ========================
import os
import random

from threading import Thread
# ============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.canvas.canvas2D.stage_visualization_canvas import StageVisualizationCanvas, \
    SampleHole
from pychron.stage.maps.laser_stage_map import LaserStageMap
from pychron.paths import paths
from pychron.core.helpers.filetools import unique_path


class StageVisualizer(Manager):
    canvas = Instance(StageVisualizationCanvas)
    stage_map = Instance(LaserStageMap)
    status_text = Str

    use_calibration = Bool(True)
    flag = True
    center = Tuple(Float, Float)
    rotation = Float(23)
    path = None

    def __init__(self, *args, **kw):
        super(StageVisualizer, self).__init__(*args, **kw)
        #        p = os.path.join(data_dir, 'stage_visualizer')
        self.path, _ = unique_path(paths.stage_visualizer_dir, 'vis',
                                   extension='')

    def update_calibration(self, obj, name, new):
        self.clear()
        if name == 'calibration_item':
            self.center = new.center
            self.rotation = new.rotation
        else:
            setattr(self, name, new)

        self.canvas.build_map(self.stage_map, calibration=[self.center,
                                                           self.rotation])

    def set_calibration(self, ca):
        pass

    #        self.clear()
    #        self.center = ca.get_center_position()
    #        self.rotation = ca.get_rotation()
    #
    #        self.canvas.build_map(self.stage_map, calibration=[self.center,
    #                                                           self.rotation])

    def clear(self):
        self.info('clearing visualizer')
        #        sm = self.stage_map
        #
        #        sm.clear_correction_file()
        #        sm.clear_interpolations()

        self.canvas.clear()

    def dump(self):
        with open(self.path, 'wb') as f:
            d = dict(center=self.center,
                     rotation=self.rotation,
                     markup=self.canvas.markupcontainer)

            pickle.dump(d, f)

    def load_visualization(self):
        p = self.open_file_dialog()

        if p is not None:
            with open(p, 'rb') as f:
                #                try:
                d = pickle.load(f)

                self.center = d['center']
                self.rotation = d['rotation']

                for k, v in d['markup'].iteritems():
                    v.set_canvas(self.canvas)

                self.canvas.markupcontainer = d['markup']
                #                except Exception, e:
            # print 'exception', e

                #        self.canvas.invalidate_and_redraw()

    def set_current_hole(self, h):
        self.canvas.set_current_hole(h)
        self.canvas.request_redraw()

    def record_uncorrected(self, h, dump=True, *args):
        self.canvas.record_uncorrected(h)
        if dump:
            self.dump()

    def record_correction(self, h, x, y, dump=True):
        self.canvas.record_correction(h, x, y)
        if dump:
            self.dump()

    def record_interpolation(self, hole, x, y, color=(1, 1, 0), dump=True):
        if isinstance(hole, (str, int)):
            hole = self.stage_map.get_hole(str(hole))

        self.canvas.record_interpolation(hole, x, y, color)
        if dump:
            self.dump()

    @on_trait_change('canvas:selected')
    def update_status_bar(self, parent, name, obj):
        if isinstance(obj, SampleHole):
            correction = ''
            if obj.hole.corrected:
                correction = 'cor.= ({:0.2f},{:0.2f})'.format(obj.hole.x_cor,
                                                              obj.hole.y_cor
                                                              )
            # interpolation = ''
            #            if obj.hole.interpolated:
            #                h = ', '.join(sorted(set([iph.id for iph in obj.hole.interpolation_holes])))
            #                interpolation = 'interpolation holes= {}'.format(h)

            self.status_text = 'hole = {} nom.= ({:0.2f},{:0.2f}) cal.=({:0.2f},{:0.2f}) {}'.format(obj.name,
                                                                                                    obj.hole.x,
                                                                                                    obj.hole.y,
                                                                                                    obj.x,
                                                                                                    obj.y,
                                                                                                    correction)

    def _use_calibration_changed(self):
        ca = self.canvas
        ca.build_map(self.stage_map,
                     calibration=[self.center,
                                  self.rotation] if self.use_calibration else None
                     )

    def traits_view(self):
        v = View(
            #                 Item('test'),
            #                 HGroup(Item('center', style='readonly'), Item('rotation', style='readonly')),
            Item('canvas', editor=ComponentEditor(width=550,
                                                  height=550),
                 show_label=False),

            statusbar='status_text',
            title='Stage Visualizer',
            resizable=True
        )
        return v

    def _stage_map_default(self):
        p = os.path.join(paths.map_dir, '61-hole.txt')
        sm = LaserStageMap(file_path=p)
        sm.load_correction_file()
        return sm

    def _canvas_default(self):
        c = StageVisualizationCanvas()
        c.build_map(self.stage_map, calibration=(self.center,
                                                 self.rotation))

        return c

    # ===============================================================================
    # testing
    # ===============================================================================
    def test_view(self):
        v = View(Item('test'),
                 Item('use_calibration'),
                 Item('center'),
                 Item('rotation'),
                 Item('canvas', editor=ComponentEditor(width=700,
                                                       height=700),
                      show_label=False),

                 statusbar='status_text'
                 )
        return v

    def _test_fired(self):
        t = Thread(target=self._execute_)
        t.start()

    def _apply_calibration(self, hole):
        cpos = (0, 0)
        rot = 0
        if self.use_calibration:
            cpos = self.center
            rot = self.rotation

        return self.stage_map.map_to_calibration(hole.nominal_position,
                                                 cpos, rot)

    def _execute_(self):

        ca = self.canvas

        self.clear()
        sm = self.stage_map
        sm.clear_correction_file()
        sm.clear_interpolations()

        ca.build_map(sm, calibration=[self.center,
                                      self.rotation] if self.use_calibration else None
                     )
        ca.invalidate_and_redraw()

        # set some correction values
        vs = range(61)
        #        vs.remove(17)
        #        vs.remove(26)
        #        vs.remove(25)
        #        vs.remove(34)
        #        vs.remove(35)
        #        vs.remove(0)
        #        vs.remove(1)
        #        vs.remove(2)
        #
        #        vs.remove(58)
        #        vs.remove(59)
        #        vs.remove(60)
        #        vs.remove(3)
        #        vs.remove(6)
        vs.remove(30)
        #        vs = range(50, 60)
        for i in vs:
            #        for i in [21, 29, 30]:

            h = sm.get_hole(str(i + 1))
            x, y = self._apply_calibration(h)

            x = self._add_error(x)
            y = self._add_error(y)

            #            ca.record_correction(h, x, y)
            #            sm.set_hole_correction(h.id, x, y)
            r = random.randint(0, 10)
            #            r = 7
            if r > 6:
                self.record_correction(h, x, y, dump=False)
                sm.set_hole_correction(h.id, x, y)

                #        self._test_interpolate_one()
        self._test_interpolate_all()

    def _add_error(self, a):
        #        return a
        return a + (0.5 - random.random()) / 2.

    def _test_interpolate_one(self):
        sm = self.stage_map
        ca = self.canvas
        h = sm.get_hole('7')
        args = sm.get_interpolated_position('7')
        #        print args
        color = (1, 1, 0)
        if args:
            nx = args[0]
            ny = args[1]
            self.record_interpolation(h, nx, ny, color, dump=False)
        ca.invalidate_and_redraw()

    def _test_interpolate_all(self):
        sm = self.stage_map
        ca = self.canvas
        colors = [(1, 1, 0), (0, 1, 1), (0, 0.75, 1), (0, 0.5, 1),
                  (0, 0.75, 0.75), (0, 0.5, 0.75)
                  ]
        for j, color in enumerate(colors[:1]):
            self.info('iteration {}'.format(j + 1))
            s = 0
            for i in range(60, -1, -1):
                h = sm.get_hole(str(i + 1))
                self.set_current_hole(h)
                r = random.randint(0, 10)
                r = 0
                if r > 5:
                    nx, ny = self._apply_calibration(h)
                    nx = self._add_error(nx)
                    ny = self._add_error(ny)
                    self.record_correction(h, nx, ny, dump=False)
                    sm.set_hole_correction(h.id, nx, ny)
                else:
                    kw = dict(cpos=self.center,
                              rotation=self.rotation)
                    if not self.use_calibration:
                        kw['cpos'] = (0, 0)
                        kw['rotation'] = 0

                    args = sm.get_interpolated_position(h.id,
                                                        **kw
                                                        )
                    if args:
                        s += 1
                        nx = args[0]
                        ny = args[1]
                        self.record_interpolation(h, nx, ny, color, dump=False)
                    else:
                        if not h.has_correction():
                            self.record_uncorrected(h)
                            #                time.sleep(0.5)
                            #                do_later(ca.invalidate_and_redraw)

            n = 61 - sum([1 for si in sm.sample_holes if si.has_correction()])
            self.info('interpolated holes {} - noncorrected {}'.format(s, n))

            if not n or not s:
                break

        ca.invalidate_and_redraw()

        self.dump()
        self.info('noncorrected holes = {}'.format(n))


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('sv')
    sv = StageVisualizer()
    #    sv.load_visualization()
    sv.configure_traits(view='test_view')
# ============= EOF =============================================
