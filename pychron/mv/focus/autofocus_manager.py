# ===============================================================================
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
# ===============================================================================

# =============enthought library imports=======================
import cPickle as pickle

from traits.api import Bool, Any, Instance, Button, Property, Event, on_trait_change
from traitsui.api import View, Item, Handler, HGroup

# ============= standard library imports ========================
# from threading import Thread
from threading import Event as TEvent
from numpy import linspace, argmin, argmax, random, asarray
import time
import os
# ============= local library imports  ==========================
from pychron.core.time_series.time_series import smooth
from pychron.image.cv_wrapper import grayspace, crop, get_focus_measure
# from pychron.image.cvwrapper import grayspace, get_focus_measure, crop, resize
from scipy.ndimage.measurements import variance
from scipy.ndimage.filters import generic_gradient_magnitude, sobel
from scipy.ndimage import sum as ndsum
from pychron.paths import paths
from pychron.managers.manager import Manager
from pychron.image.image import Image
# from pychron.machine_vision.focus_parameters import FocusParameters
# from pychron.image.image_editor import ImageEditor
from pychron.graph.graph import Graph
from pychron.mv.focus.focus_parameters import FocusParameters
from pychron.core.ui.image_editor import ImageEditor
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.thread import Thread


class ConfigureHandler(Handler):
    def closed(self, info, isok):
        if isok:
            info.object.dump_parameters()


class AutoFocusManager(Manager):
    '''
        currently uses passive focus techniques
        see

        http://en.wikipedia.org/wiki/Autofocus

    '''

    video = Any
    laser_manager = Any
    stage_controller = Any
    canvas = Any
    parameters = Instance(FocusParameters)
    configure_button = Button('configure')

    autofocus_button = Event
    autofocus_label = Property(depends_on='autofocusing')
    autofocusing = Bool

    # threading event for cancel signal
    _evt_autofocusing = None

    image = Instance(Image, ())

    graph = None

    def dump_parameters(self):
        p = os.path.join(paths.hidden_dir, 'autofocus_configure')
        self.info('dumping parameters to {}'.format(p))
        with open(p, 'wb') as f:
            pickle.dump(self.parameters, f)

    def load_parameter(self):
        p = os.path.join(paths.hidden_dir, 'autofocus_configure')
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                try:
                    params = pickle.load(f)
                    self.info('loading parameters from {}'.format(p))

                    if not isinstance(params, FocusParameters):
                        self.info('out of date parameters file. using default')
                        params = FocusParameters()
                    return params

                except Exception, e:
                    print 'autofocus load parameter', e
                    return FocusParameters()
        else:
            return FocusParameters()

    def passive_focus(self, block=False, **kw):

        self._evt_autofocusing = TEvent()
        self._evt_autofocusing.clear()
#        manager = self.laser_manager
        oper = self.parameters.operator
        self.info('passive focus. operator = {}'.format(oper))

        g = self.graph
        if not g:
            g = Graph(plotcontainer_dict=dict(padding=10),
                      window_x=0.70,
                      window_y=20,
                      window_width=325,
                      window_height=325,
                      window_title='Autofocus'
                      )
            self.graph = g

        g.clear()

        g.new_plot(padding=[40, 10, 10, 40],
                   xtitle='Z (mm)',
                   ytitle='Focus Measure ({})'.format(oper)
                   )
        g.new_series()
        g.new_series()

        invoke_in_main_thread(self._open_graph)

        target = self._passive_focus
        self._passive_focus_thread = Thread(name='autofocus', target=target,
                                            args=(self._evt_autofocusing,

                                                  ),
                                            kwargs=kw
                                            )
        self._passive_focus_thread.start()
        if block:
#             while 1:
#                 if not self._passive_focus_thread.isRunning():
#                     break
#                 time.sleep(0.25)
            self._passive_focus_thread.join()

    def _open_graph(self):
        ui = self.graph.edit_traits()
        self.add_window(ui)

    def stop_focus(self):

        if self.stage_controller:
            self.stage_controller.stop()

        self.info('autofocusing stopped by user')

    def _passive_focus(self, stop_signal, set_zoom=True):
        '''
            sweep z looking for max focus measure
            FMgrad= roberts or sobel (sobel removes noise)
            FMvar = intensity variance
        '''

        self.autofocusing = True

        manager = self.laser_manager
        fstart = self.parameters.fstart
        fend = self.parameters.fend
        step_scalar = self.parameters.step_scalar
        zoom = self.parameters.zoom
        operator = self.parameters.operator

        steps = step_scalar * (max(fend, fstart) - min(fend, fstart)) + 1

        prev_zoom = None
        if set_zoom and \
                manager is not None and \
                     zoom:
            motor = manager.get_motor('zoom')
            if motor:
                prev_zoom = motor.data_position
                self.info('setting zoom: {}'.format(zoom))
                manager.set_motor('zoom', zoom, block=True)
                time.sleep(1.5)

        args = self._do_focusing(fstart, fend, steps, operator)

        if manager is not None:
            if prev_zoom is not None:
                self.info('returning to previous zoom: {}'.format(prev_zoom))
                manager.set_motor('zoom', prev_zoom, block=True)

        if args:
            mi, fmi, ma, fma = args

            self.info('''passive focus results:Operator={}
ImageGradmin={} (z={})
ImageGradmax={}, (z={})'''.format(operator, mi, fmi, ma, fma))

            focus_pos = fma
            self.graph.add_vertical_rule(focus_pos)
            self.graph.redraw()
#            self.graph.add_vertical_rule(fma)

            self.info('calculated focus z= {}'.format(focus_pos))

#            if set_z:
            controller = self.stage_controller
            if controller is not None:
                if not stop_signal.isSet():
                    controller.single_axis_move('z', focus_pos, block=True)
                    controller._z_position = focus_pos
                    controller.z_progress = focus_pos

        self.autofocusing = False

    def _cancel_sweep(self, vo):
        if self._evt_autofocusing.isSet():
            # return to original velocity
            self.autofocusing = False
            self._reset_velocity(vo)
            return True

    def _reset_velocity(self, vo):
        if self.stage_controller:
            pdict = dict(velocity=vo, key='z')
            self.stage_controller.set_single_axis_motion_parameters(pdict=pdict)

    def _do_focusing(self, start, end, steps, operator):
        screen_roi = self._get_roi()
        self._add_focus_area_rect(*screen_roi)

        src = self._load_source()
        src = asarray(src)
        h, w, _d = src.shape

        cx = w / 2.
        cy = h / 2.

        cw = self.parameters.crop_width
        ch = self.parameters.crop_height

        roi = cx, cy, cw, ch

        '''
            start the z in motion and take pictures as you go
            query stage_controller to get current z
        '''

        self.info('focus sweep start={} end={}'.format(start, end))
        # move to start position
        controller = self.stage_controller
        if controller:
            vo = controller.axes['z'].velocity
            if self._cancel_sweep(vo):
                return
            self.graph.set_x_limits(min(start, end), max(start, end), pad=2)
            # sweep 1 and velocity 1
            self._do_sweep(start, end, velocity=self.parameters.velocity_scalar1)
            fms, focussteps = self._collect_focus_measures(operator, roi)
            if not (fms and focussteps):
                return

            # reached end of sweep
            # calculate a nominal focal point
            args = self._calculate_nominal_focal_point(fms, focussteps)
            if not args:
                return
            nfocal = args[3]

            nwin = self.parameters.negative_window
            pwin = self.parameters.positive_window

            if self._cancel_sweep(vo):
                return
            nstart, nend = max(0, nfocal - nwin), nfocal + pwin
#            mi = min(min(nstart, nend), min(start, end))
#            ma = max(max(nstart, nend), max(start, end))
#            self.graph.set_x_limits(mi, ma, pad=2)
            time.sleep(1)
            # do a slow tight sweep around the nominal focal point
            self._do_sweep(nstart, nend, velocity=self.parameters.velocity_scalar2)
            fms, focussteps = self._collect_focus_measures(operator, roi, series=1)

            self._reset_velocity(vo)

        else:
            focussteps = linspace(0, 10, 11)
            fms = -(focussteps - 5) ** 2 + 10 + random.random(11)

        self.info('frames analyzed {}'.format(len(fms)))

#        self.canvas.markupcontainer.pop('croprect')
        return self._calculate_nominal_focal_point(fms, focussteps)

    def _do_sweep(self, start, end, velocity=None):
        controller = self.stage_controller
        controller.single_axis_move('z', start, block=True)
#         time.sleep(0.1)
        # explicitly check for motion
#        controller.block(axis='z')

        if velocity:
            vo = controller.axes['z'].velocity

            controller.set_single_axis_motion_parameters(pdict=dict(velocity=vo * velocity,
                                                    key='z'))

        self.info('starting sweep from {}'.format(controller.z_progress))
        # pause before moving to end
        time.sleep(0.25)
        controller.single_axis_move('z', end, update=100, immediate=True)

    def _collect_focus_measures(self, operator, roi, series=0):
        controller = self.stage_controller
        focussteps = []
        fms = []
        if controller.timer:
            p = controller.timer.get_interval()
            self.debug('controller timer period {}'.format(p))
            pz = controller.z_progress

            while 1:
                src = self._load_source()
                x = controller.z_progress
                if x != pz:
                    y = self._calculate_focus_measure(src, operator, roi)
                    self.graph.add_datum((x, y), series=series)

                    focussteps.append(x)
                    fms.append(y)

                    pz = x

                if not (controller.timer.isActive() and \
                        not self._evt_autofocusing.isSet()):
                    break
                time.sleep(p)

            self.debug('sweep finished')


        return fms, focussteps

    def _calculate_nominal_focal_point(self, fms, focussteps):
        if fms:
            sfms = smooth(fms)
            if sfms is not None:

                self.graph.new_series(focussteps, sfms)
                self.graph.redraw()

                fmi = focussteps[argmin(sfms)]
                fma = focussteps[argmax(sfms)]

                mi = min(sfms)
                ma = max(sfms)

                return mi, fmi, ma, fma

    def _calculate_focus_measure(self, src, operator, roi):
        '''
            see
            IMPLEMENTATION OF A PASSIVE AUTOMATIC FOCUSING ALGORITHM
            FOR DIGITAL STILL CAMERA
            DOI 10.1109/30.468047
            and
            http://cybertron.cg.tu-berlin.de/pdci10/frankencam/#autofocus
        '''

        # need to resize to 640,480. this is the space the roi is in
#        s = resize(grayspace(pychron), 640, 480)
        src = grayspace(src)
        v = crop(src, *roi)

        di = dict(var=lambda x:variance(x),
                  laplace=lambda x: get_focus_measure(x, 'laplace'),
                  sobel=lambda x: ndsum(generic_gradient_magnitude(x, sobel, mode='nearest'))
                  )

        func = di[operator]
        return func(v)

    def image_view(self):
        v = View(Item('image', show_label=False, editor=ImageEditor(),
                      width=640,
                      height=480,
                       style='custom'))
        return v

    def traits_view(self):
        v = View(
               HGroup(self._button_factory('autofocus_button', 'autofocus_label'),
                      Item('configure_button', show_label=False),
                      show_border=True,
                      label='Autofocus'
                      )
               )
        return v

    def configure_view(self):
        v = View(Item('parameters', style='custom', show_label=False),
               handler=ConfigureHandler,
               buttons=['OK', 'Cancel'],
               kind='livemodal',
               title='Configure Autofocus',
               x=0.80,
               y=0.05
               )
        return v

    def _load_source(self):
        src = self.video.get_frame()
        return src
#        if pychron:
#            return Image.new_frame(pychron)
#            self.image.load(pychron)

#        return self.image.source_frame

    def _get_roi(self):
        w = self.parameters.crop_width
        h = self.parameters.crop_height

        cx, cy = self.canvas.get_center_rect_position(w, h)


#         cw, ch = self.canvas.outer_bounds
#         print w, h, cw, ch
#         cx = cw / 2. - w / 2.
#         cy = ch / 2. - h / 2.
#         cx = (cw - w) / 2.
#         cy = (ch - h) / 2.
#         cx = (640 * self.canvas.scaling - w) / 2
#         cy = (480 * self.canvas.scaling - h) / 2
        roi = cx, cy, w, h

        return roi

    def _add_focus_area_rect(self, cx, cy, w, h):
#         pl = self.canvas.padding_left
#         pb = self.canvas.padding_bottom

        self.canvas.remove_item('croprect')
        self.canvas.add_markup_rect(cx, cy, w, h, identifier='croprect')

    def _autofocus_button_fired(self):
        if not self.autofocusing:
            self.autofocusing = True

            self.passive_focus()
        else:
            self.autofocusing = False
            self._evt_autofocusing.set()
            self.stop_focus()

    def _configure_button_fired(self):
        self._crop_rect_update()
        self.edit_traits(view='configure_view', kind='livemodal')

        self.canvas.remove_item('croprect')
#        try:
#            self.canvas.markupcontainer.pop('croprect')
#        except KeyError:
#            pass

    @on_trait_change('parameters:[_crop_width,_crop_height]')
    def _crop_rect_update(self):
        roi = self._get_roi()
        self._add_focus_area_rect(*roi)

    def _get_autofocus_label(self):
        return 'Autofocus' if not self.autofocusing else 'Stop'


    def _parameters_default(self):
        return self.load_parameter()

    def _autofocusing_changed(self, new):
        if not new:
            self.canvas.remove_item('croprect')
# ===============================================================================
# Deprecated
# ===============================================================================
# ============= EOF =====================================

