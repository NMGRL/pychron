# ===============================================================================
# Copyright 2022 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
import os
import time
from math import ceil

import joblib
from numpy import hstack, column_stack, savetxt, savez, save, load, asarray
from skimage.exposure import adjust_gamma
from sklearn import metrics, svm
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from traits.api import Any, Instance, HasTraits, Dict, Enum, Event, Button
from traitsui.api import View, UItem, Item, VGroup, HGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path2
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.image_editor import ImageEditor
from pychron.core.ui.thread import Thread
from pychron.image.cv_wrapper import grayspace, get_size, crop
from pychron.image.standalone_image import FrameImage
from pychron.loggable import Loggable
from pychron.mv.grain_locator import GrainLocator
from pychron.mv.machine_vision_manager import MachineVisionManager
from pychron.paths import paths

from skimage.io import imread, imsave


class TrainView(HasTraits):
    blank_image = Instance(FrameImage, ())
    loaded_image = Instance(FrameImage, ())
    blank_state = Enum('Empty', 'Loaded', 'MultiGrain', 'Dirty')
    loaded_state = Enum('Empty', 'Loaded', 'MultiGrain', 'Dirty')

    def __init__(self, blankframe, loaded_frame, *args, **kw):
        super(TrainView, self).__init__(*args, **kw)

        self.blank_image.set_frame(blankframe)
        self.loaded_image.set_frame(loaded_frame)
        self.blank_state = 'Empty'
        self.loaded_state = 'Loaded'

    def traits_view(self):
        a = VGroup(UItem('blank_state'),
                   UItem('object.blank_image.source_frame',
                         editor=ImageEditor()))
        b = VGroup(UItem('loaded_state'),
                   UItem('object.loaded_image.source_frame',
                         editor=ImageEditor()))
        v = okcancel_view(HGroup(a, b))
        return v


class TrayChecker(MachineVisionManager):
    positions = Dict
    display_image = Instance(FrameImage, ())
    refresh_image = Event
    stop_button = Button('Stop')
    post_move_delay = 0.125
    post_check_delay = 1

    def __init__(self, loading_manager, *args, **kw):
        super(TrayChecker, self).__init__(*args, **kw)
        self._loading_manager = loading_manager
        self.video = loading_manager.stage_manager.video

    def stop(self):
        self.debug('stop fired')
        self._alive = False

    def check_frame(self):
        frame = self._loading_manager.stage_manager.autocenter_manager.new_image_frame(force=True)
        return True

    def check(self):
        self._iter()

    def map(self):
        self._iter(map_positions=True)

    def _iter(self, map_positions=False):
        use_ml = True
        pipe = None
        if use_ml:
            pipe = self._get_classifier()
        self.edit_traits(view=View(UItem('stop_button'),
                                   UItem('object.display_image.source_frame',
                                         width=640,
                                         height=480,
                                         editor=ImageEditor(refresh='object.display_image.refresh_needed')),
                                   # width=900,
                                   # height=900,
                                   ))

        if map_positions:
            func = self._map_positions
        else:
            func = self._check

        self._thread = Thread(target=func, args=(pipe,))
        self._thread.start()

    def _map_positions(self, pipe):
        self._alive = True
        results = []
        for hole in self._loading_manager.stage_manager.stage_map.sample_holes[:11]:
            if not self._alive:
                self.debug('exiting check loop')
                break

            pos = hole.id
            # for pos in self._loading_manager.positions:
            self._loading_manager.goto(pos, block=True, capture=".filled")
            # time.sleep(self.post_move_delay)
            # if pipe is not None:
            #     self._check_position_ml(pipe, pos)
            # else:
            #     self._check_position(pos)
            x = self._loading_manager.stage_manager.stage_controller.x
            y = self._loading_manager.stage_manager.stage_controller.y
            results.append((pos, (x, y)))
            self.debug('map position result {}'.format(results[-1]))
            # time.sleep(self.post_check_delay)

        name = self._loading_manager.stage_manager.stage_map.name
        p, cnt = unique_path2(paths.csv_data_dir, '{}.corrected_positions.txt'.format(name))
        with open(p, 'w') as wfile:
            for r in results:
                print(r)
                line = ','.join([str(ri) for ri in r])
                line = '{}\n'.format(line)
                wfile.write(line)

    def _check(self, pipe):
        self._alive = True
        for hole in self._loading_manager.stage_manager.stage_map.sample_holes:
            if not self._alive:
                self.debug('exiting check loop')
                break

            pos = hole.id
            # for pos in self._loading_manager.positions:
            self._loading_manager.goto(pos, block=True)
            time.sleep(self.post_move_delay)
            if pipe is not None:
                self._check_position_ml(pipe, pos)
            else:
                self._check_position(pos)
            time.sleep(self.post_check_delay)

    def train(self):
        xs = []
        labels = []
        for pos in self._loading_manager.positions:
            self._loading_manager.goto(pos, block=True)
            args = self._train_position(pos.position)
            if not args:
                ss, bv, lv = args
                labels.extend(ss)
                xs.extend((bv, lv))

                loadname = self._loading_manager.load_instance.name
                sp = os.path.join(paths.loading_dir, '{}.samples.npy'.format(loadname))
                save(sp, column_stack(xs))
                lp = os.path.join(paths.loading_dir, '{}.labels.npy'.format(loadname))
                save(lp, labels)

        self.train_ml()

    def train_ml(self):
        loadname = self._loading_manager.load_instance.name
        sp = os.path.join(paths.loading_dir, '{}.samples.npy'.format(loadname))
        lp = os.path.join(paths.loading_dir, '{}.labels.npy'.format(loadname))
        samples = load(sp)
        labels = load(lp)
        use_nn = False
        if use_nn:
            clf = MLPClassifier(hidden_layer_sizes=(5, 2),
                                random_state=1)
        else:
            clf = svm.SVC(gamma=0.001)

        X_train, X_test, y_train, y_test = train_test_split(samples, labels, random_state=42)
        pipe = make_pipeline(StandardScaler(), clf)
        pipe.fit(X_train, y_train)  # apply scaling on training data

        tp = os.path.join(paths.loading_dir, '{}.clf.joblib'.format(loadname))
        joblib.dump(pipe, tp)

        score = pipe.score(X_test, y_test)

        predicted = pipe.predict(X_test)
        print(
            f"Classification report for classifier {clf}:\n"
            f"{metrics.classification_report(y_test, predicted)}\n"
        )
        self.info('training score={}'.format(score))
        disp = metrics.ConfusionMatrixDisplay.from_predictions(y_test, predicted)
        disp.figure_.suptitle("Confusion Matrix")
        print(f"Confusion matrix:\n{disp.confusion_matrix}")

    def _train_position(self, pos):
        blankframe = self._get_blankframe(pos)
        frame = self.new_image_frame(pos)
        self._save_image(pos, frame)

        t = TrainView(blankframe, frame)
        info = t.edit_traits()
        if info.result:
            blank_vector = blankframe.flatten()
            loaded_vector = frame.flatten()
            # blank_vector = self._make_vector(pos, blankframe)
            # loaded_vector = self._make_vector(pos, frame)
            return [t.blank_state, t.loaded_state], blank_vector, loaded_vector

    def new_image_frame(self, pos):
        frame = super(TrayChecker, self).new_image_frame(force=True)
        frame = self._preprocess(frame)
        return self._crop(frame, pos=pos)

    def _preprocess(self, frame, gamma=2):
        # frame = grayspace(frame)
        # if gamma:
        #     frame = adjust_gamma(frame, gamma)
        return frame

    def _save_image(self, pos, frame):
        loadname = self._loading_manager.load_instance.name
        p = os.path.join(paths.loading_dir, loadname, '{}.loaded.jpg'.format(pos))
        imsave(p, frame)

    def _get_classifier(self):
        loadname = self._loading_manager.load_instance.name
        tp = os.path.join(paths.loading_dir, '{}.clf.joblib'.format(loadname))
        if os.path.isfile(tp):
            return joblib.load(tp)

    def _get_blankframe(self, pos):
        p = self._image_path(pos)
        if os.path.isfile(p):
            blankframe = imread(p)
            blankframe = self._preprocess(blankframe)
            blankframe = self._crop(blankframe, pos=pos)
            return blankframe

    def _image_path(self, pos):
        loadname = self._loading_manager.load_instance.name
        dirname = os.path.join(paths.loading_dir, loadname)
        p = os.path.join(dirname, '{}.empty.tif'.format(pos))
        return p

    def _crop(self, frame, dim=None, pos=1):
        if dim is None:
            hole = self._loading_manager.stage_manager.stage_map.get_hole(pos)
            dim = hole.dimension

        cw = ch = ceil(dim * 2.55)
        pxpermm = self._loading_manager.stage_manager.autocenter_manager.pxpermm
        cw_px = int(cw * pxpermm)
        ch_px = int(ch * pxpermm)
        w, h = get_size(frame)
        x = int((w - cw_px) / 2.0)
        y = int((h - ch_px) / 2.0)
        return asarray(crop(frame, x, y, cw_px, ch_px))

    def _check_position(self, pos):
        self.debug('check position {}'.format(pos))
        frame = self.new_image_frame(pos)
        self._loading_manager.stage_manager.snapshot(name='{}.tc'.format(pos),
                                                     render_canvas=False, inform=False)
        blankframe = self._get_blankframe(pos)

        self.display_image.clear()
        self.display_image.tile(frame)
        if blankframe is not None:
            diff = frame - blankframe
            self.display_image.tile(blankframe)
            self.display_image.tile(diff)
            # self.display_image.tile(diff)
        self.display_image.tilify()
        # invoke_in_main_thread(self.trait_set, refresh_image=True)
        # self.refresh_image = True
        self.display_image.refresh_needed = True

    def _check_position_ml(self, pipe, pos):
        self.debug('check position nn {}'.format(pos))

        frame = self.new_image_frame(pos)
        if pipe is not None:
            result = pipe.predict(frame.flatten())
            self.info('check_position result={}'.format(result))

        else:
            self.debug('dumb position check')
            self._check_position(pos)

        # blankframe = self._get_blankframe(pos)
        # if not self.locator.find_grain(im, blankframe, frame, dim):
        #     self.debug('no grain found {}'.format(pos))

    def _stop_button_fired(self):
        self.stop()
# ============= EOF =============================================
