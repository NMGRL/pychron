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
import base64
import io
# ============= enthought library imports =======================
import os
import time
from math import ceil

import joblib
import requests
from PIL import Image
from numpy import hstack, column_stack, savetxt, savez, save, load, asarray, concatenate
from sklearn import metrics, svm
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from traits.api import Any, Instance, HasTraits, Dict, Enum, Event, Button
from traitsui.api import View, UItem, Item, VGroup, HGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.image_editor import ImageEditor
from pychron.core.ui.thread import Thread
from pychron.image.cv_wrapper import get_size, crop
from pychron.image.standalone_image import FrameImage
from pychron.loading.traydb import LABEL_MAP
from pychron.loggable import Loggable
from pychron.mv.machine_vision_manager import MachineVisionManager
from pychron.paths import paths


# from skimage.io import imread, imsave


#
# class TrainView(HasTraits):
#     blank_image = Instance(FrameImage, ())
#     loaded_image = Instance(FrameImage, ())
#     blank_state = Enum('Empty', 'Loaded', 'MultiGrain', 'Dirty')
#     loaded_state = Enum('Empty', 'Loaded', 'MultiGrain', 'Dirty')
#
#     def __init__(self, blankframe, loaded_frame, *args, **kw):
#         super(TrainView, self).__init__(*args, **kw)
#
#         self.blank_image.set_frame(blankframe)
#         self.loaded_image.set_frame(loaded_frame)
#         self.blank_state = 'Empty'
#         self.loaded_state = 'Loaded'
#
#     def traits_view(self):
#         a = VGroup(UItem('blank_state'),
#                    UItem('object.blank_image.source_frame',
#                          editor=ImageEditor()))
#         b = VGroup(UItem('loaded_state'),
#                    UItem('object.loaded_image.source_frame',
#                          editor=ImageEditor()))
#         v = okcancel_view(HGroup(a, b))
#         return v


class TrayChecker(MachineVisionManager):
    positions = Dict
    display_image = Instance(FrameImage, ())
    refresh_image = Event
    stop_button = Button('Stop')
    good_button = Button('Good')
    empty_button = Button('Empty')
    multigrain_button = Button('MultiGrain')
    contaminant_button = Button('Contaminant')

    post_move_delay = 0.250
    post_check_delay = 0.0

    # traydb = Instance(TrayDB)

    _alive = False
    _active_frame = None
    _samples = None
    _labels = None
    _active_positions = None
    _active_position = None
    _thread = None

    def __init__(self, loading_manager, dbpath='', *args, **kw):
        super(TrayChecker, self).__init__(*args, **kw)
        if loading_manager:
            self._loading_manager = loading_manager
            self.video = loading_manager.stage_manager.video

        # self.traydb = TrayDB(path=dbpath)
        # self.traydb.build_database()

    def stop(self):
        self.debug('stop fired')
        self._alive = False

    def check_frame(self):
        #     frame = self._loading_manager.stage_manager.autocenter_manager.new_image_frame(force=True)
        return True

    # def check(self):
    #     self._iter()

    # def map(self):
    #     self._iter(func=self._map_positions)

    def scan(self, classify_now=False):
        if classify_now:
            self._samples = []
            self._labels = []
            self._active_positions = self._loading_manager.stage_manager.stage_map.all_holes()

            buttons = HGroup(UItem('stop_button'),
                             UItem('good_button'),
                             UItem('empty_button'),
                             UItem('multigrain_button'),
                             UItem('contaminant_button')
                             )
            v = okcancel_view(buttons,
                              UItem('object.display_image.source_frame',
                                    width=640 * 1.25,
                                    height=480 * 1.25,
                                    editor=ImageEditor(refresh='object.display_image.refresh_needed')),
                              )

            # go to first hole
            self._visit_next_position()

            info = self.edit_traits(v)
            # if info.result:
            #     self.dump_klasses()
        else:
            pipe = None
            info = self.edit_traits(view=View(HGroup(UItem('stop_button')),
                                              UItem('object.display_image.source_frame',
                                                    width=640,
                                                    height=480,
                                                    editor=ImageEditor(refresh='object.display_image.refresh_needed')),
                                              ))

            self._alive = True
            self._thread = Thread(target=self._scan, args=(pipe, info,))
            self._thread.start()

    def _visit_next_position(self):
        try:
            hole = next(self._active_positions)
        except StopIteration:
            self.information_dialog('Classification Complete')
            return

        trayname = self._loading_manager.stage_manager.stage_map.name
        traypath = os.path.join(paths.snapshot_dir, trayname)
        if not os.path.isdir(traypath):
            os.mkdir(traypath)

        pos = hole.id
        self._loading_manager.goto(pos, block=True)
        time.sleep(self.post_move_delay)
        frame = self.new_image_frame(pos)

        self._loading_manager.stage_manager.snapshot(name=os.path.join(traypath, '{}.tc'.format(pos)),
                                                     render_canvas=False, inform=False)
        # guess the label for this image
        possible_label = self._classify(frame)
        self.debug(f'possible label={possible_label}')

        self.display_image.clear()
        self.display_image.source_frame = frame
        # self.display_image.tile(frame)
        # self.display_image.tilify()
        self.display_image.refresh_needed = True

    # def dump_klasses(self):
    #     tray_name = self._loading_manager.stage_manager.stage_map.name
    #     # loadname = self._loading_manager.load_instance.name
    #     sp = os.path.join(paths.loading_dir, f'{tray_name}.samples.npy')
    #     #sp, cnt = unique_path2(paths.loading_dir, 'samples', extension='.npy')
    #     # sp = os.path.join(paths.loading_dir, '{}.samples.npy'.format(loadname))
    #     # samples = self._samples
    #     # labels = self._labels
    #
    #     if os.path.isfile(sp):
    #         samples = load(sp)
    #         samples = concatenate((samples, self._samples))
    #     else:
    #         samples = self._samples
    #     save(sp, samples)
    #
    #     lp = os.path.join(paths.loading_dir, f'{tray_name}.samples.npy')
    #     #lp, cnt = unique_path2(paths.loading_dir, 'labels', extension='.npy')
    #     # lp = os.path.join(paths.loading_dir, '{}.labels.npy'.format(loadname))
    #
    #     if os.path.isfile(lp):
    #         labels = load(lp)
    #         self.debug(f'loaded labels {labels}')
    #         self.debug(f'new labels {self._labels}')
    #         labels = concatenate((labels, self._labels))
    #     else:
    #         # labels = column_stack(labels)
    #         labels = self._labels
    #     save(lp, labels)

    # def _iter(self, func=None):
    #     use_ml = False
    #     pipe = None
    #     if use_ml:
    #         pipe = self._get_classifier()
    #
    #     info = self.edit_traits(view=View(HGroup(UItem('stop_button')),
    #                                       UItem('object.display_image.source_frame',
    #                                             width=640,
    #                                             height=480,
    #                                             editor=ImageEditor(refresh='object.display_image.refresh_needed')),
    #                                       # width=900,
    #                                       # height=900,
    #                                       ))
    #
    #     if func is None:
    #         func = self._check
    #
    #     self._alive = True
    #     self._thread = Thread(target=func, args=(pipe, info))
    #     self._thread.start()

    # def _map_positions(self, pipe, info):
    #     results = []
    #     for hole in self._loading_manager.stage_manager.stage_map.sample_holes[:11]:
    #         if not self._alive:
    #             self.debug('exiting check loop')
    #             break
    #
    #         pos = hole.id
    #         # for pos in self._loading_manager.positions:
    #         self._loading_manager.goto(pos, block=True, capture=".filled")
    #         # time.sleep(self.post_move_delay)
    #         # if pipe is not None:
    #         #     self._check_position_ml(pipe, pos)
    #         # else:
    #         #     self._check_position(pos)
    #         x = self._loading_manager.stage_manager.stage_controller.x
    #         y = self._loading_manager.stage_manager.stage_controller.y
    #         results.append((pos, (x, y)))
    #         self.debug('map position result {}'.format(results[-1]))
    #         # time.sleep(self.post_check_delay)
    #
    #     name = self._loading_manager.stage_manager.stage_map.name
    #     p, cnt = unique_path2(paths.csv_data_dir, '{}.corrected_positions.txt'.format(name))
    #     with open(p, 'w') as wfile:
    #         for r in results:
    #             print(r)
    #             line = ','.join([str(ri) for ri in r])
    #             line = '{}\n'.format(line)
    #             wfile.write(line)

    def _scan(self, pipe, info):
        trayname = self._loading_manager.stage_manager.stage_map.name
        # traypath = os.path.join(paths.snapshot_dir, trayname)
        # if not os.path.isdir(traypath):
        #     os.mkdir(traypath)

        for hole in self._loading_manager.stage_manager.stage_map.all_holes():
            if not self._alive:
                self.debug('exiting check loop')
                break

            pos = hole.id
            # for pos in self._loading_manager.positions:
            self._loading_manager.goto(pos, block=True)
            time.sleep(self.post_move_delay)
            frame = self.new_image_frame(pos)

            # self._loading_manager.stage_manager.snapshot(name=os.path.join(traypath, '{}.tc'.format(pos)),
            #                                              render_canvas=False, inform=False)

            # name = f'{trayname}:{pos}'
            # if self._loading_manager.load_instance:
            #     name = f'{name}:{self._loading_manager.load_instance.name}'

            self._add_unlabeled_image(pos, frame)

            self.display_image.clear()
            self.display_image.set_frame(frame)
            # self.display_image.tile(frame)
            # self.display_image.tilify()
            self.display_image.refresh_needed = True
            time.sleep(self.post_check_delay)

        info.dispose()
        self.information_dialog(f'Scan of {trayname} complete')

    def _check(self, info):
        for hole in self._loading_manager.stage_manager.stage_map.all_holes():
            if not self._alive:
                self.debug('exiting check loop')
                break

            pos = hole.id
            self._loading_manager.goto(pos, block=True)
            time.sleep(self.post_move_delay)

            self._check_position(pos)

            time.sleep(self.post_check_delay)

        info.dispose()

    # def train(self):
    #     xs = []
    #     labels = []
    #     for pos in self._loading_manager.positions:
    #         self._loading_manager.goto(pos, block=True)
    #         args = self._train_position(pos.position)
    #         if not args:
    #             ss, bv, lv = args
    #             labels.extend(ss)
    #             xs.extend((bv, lv))
    #
    #             loadname = self._loading_manager.load_instance.name
    #             sp = os.path.join(paths.loading_dir, '{}.samples.npy'.format(loadname))
    #             save(sp, column_stack(xs))
    #             lp = os.path.join(paths.loading_dir, '{}.labels.npy'.format(loadname))
    #             save(lp, labels)
    #
    #     self.train_ml()
    #
    # def train_ml(self):
    #     loadname = self._loading_manager.load_instance.name
    #     sp = os.path.join(paths.loading_dir, '{}.samples.npy'.format(loadname))
    #     lp = os.path.join(paths.loading_dir, '{}.labels.npy'.format(loadname))
    #     samples = load(sp)
    #     labels = load(lp)
    #     use_nn = False
    #     if use_nn:
    #         clf = MLPClassifier(hidden_layer_sizes=(5, 2),
    #                             random_state=1)
    #     else:
    #         clf = svm.SVC(gamma=0.001)
    #
    #     X_train, X_test, y_train, y_test = train_test_split(samples, labels, random_state=42)
    #     pipe = make_pipeline(StandardScaler(), clf)
    #     pipe.fit(X_train, y_train)  # apply scaling on training data
    #
    #     tp = os.path.join(paths.loading_dir, '{}.clf.joblib'.format(loadname))
    #     joblib.dump(pipe, tp)
    #
    #     score = pipe.score(X_test, y_test)
    #
    #     predicted = pipe.predict(X_test)
    #     print(
    #         f"Classification report for classifier {clf}:\n"
    #         f"{metrics.classification_report(y_test, predicted)}\n"
    #     )
    #     self.info('training score={}'.format(score))
    #     disp = metrics.ConfusionMatrixDisplay.from_predictions(y_test, predicted)
    #     disp.figure_.suptitle("Confusion Matrix")
    #     print(f"Confusion matrix:\n{disp.confusion_matrix}")
    #
    # def _train_position(self, pos):
    #     blankframe = self._get_blankframe(pos)
    #     frame = self.new_image_frame(pos)
    #     self._save_image(pos, frame)
    #
    #     t = TrainView(blankframe, frame)
    #     info = t.edit_traits()
    #     if info.result:
    #         blank_vector = blankframe.flatten()
    #         loaded_vector = frame.flatten()
    #         # blank_vector = self._make_vector(pos, blankframe)
    #         # loaded_vector = self._make_vector(pos, frame)
    #         return [t.blank_state, t.loaded_state], blank_vector, loaded_vector
    def test_ml(self):
        clf = self._get_classifier()
        names, samples, labels = self._get_sample_labels()

        idx = 50
        print(names[idx])
        print(clf.predict(samples[idx].reshape(1, -1)))

    def train_ml(self):
        names, samples, labels = self._get_sample_labels()
        print(samples.shape, labels.shape)
        # labels = randint(0,4, size=labels.size)
        use_nn = False
        if use_nn:
            clf = MLPClassifier(hidden_layer_sizes=(5, 2),
                                random_state=1)
        else:
            clf = svm.SVC(gamma=0.001)

        x_train, x_test, y_train, y_test = train_test_split(samples, labels, random_state=42)
        pipe = make_pipeline(StandardScaler(), clf)
        pipe.fit(x_train, y_train)  # apply scaling on training data

        tp = os.path.join(paths.loading_dir, 'tray.clf.joblib')
        joblib.dump(pipe, tp)

        score = pipe.score(x_test, y_test)

        predicted = pipe.predict(x_test)
        self.debug(
            f"Classification report for classifier {clf}:\n"
            f"{metrics.classification_report(y_test, predicted)}\n"
        )
        self.info('training score={}'.format(score))
        # disp = metrics.ConfusionMatrixDisplay.from_predictions(y_test, predicted)
        # disp.figure_.suptitle("Confusion Matrix")
        # self.debug(f"Confusion matrix:\n{disp.confusion_matrix}")

    def new_image_frame(self, pos):
        frame = super(TrayChecker, self).new_image_frame(force=True)
        frame = self._preprocess(frame)
        frame = self._crop(frame, pos=pos)
        self._active_frame = frame
        self._active_position = pos

        return frame

    # def _get_sample_labels(self):
    #     args = self.traydb.get_sample_labels()
    #     if args is not None:
    #         names, samples, labels = args
    #
    #     return names, samples, labels

    def _preprocess(self, frame, gamma=2):
        # frame = grayspace(frame)
        # if gamma:
        #     frame = adjust_gamma(frame, gamma)
        return frame

    # def _save_image(self, pos, frame):
    #     loadname = self._loading_manager.load_instance.name
    #     p = os.path.join(paths.loading_dir, loadname, '{}.loaded.jpg'.format(pos))
    #     imsave(p, frame)

    def _get_classifier(self):
        tp = os.path.join(paths.loading_dir, 'tray.clf.joblib')
        if os.path.isfile(tp):
            return joblib.load(tp)

    # def _get_blankframe(self, pos):
    #     p = self._image_path(pos)
    #     if os.path.isfile(p):
    #         blankframe = imread(p)
    #         blankframe = self._preprocess(blankframe)
    #         blankframe = self._crop(blankframe, pos=pos)
    #         return blankframe

    def _image_path(self, pos):
        loadname = self._loading_manager.load_instance.name
        dirname = os.path.join(paths.loading_dir, loadname)
        p = os.path.join(dirname, '{}.empty.tif'.format(pos))
        return p

    def _crop(self, frame, dim=None, pos=1):
        if dim is None:
            hole = self._loading_manager.stage_manager.stage_map.get_hole(pos)
            dim = hole.dimension

        cw = ch = dim * 2.75
        # new = 3
        # with open(os.path.join(paths.appdata_dir, 'zoom_level.csv')) as rfile:
        #     for line in rfile:
        #         zoom, pxpermm = line.split(',')
        #         if float(zoom) == float(new):
        #             pxpermm = float(pxpermm)
        #             break
        #     else:
        #         pxpermm = 55
        #         self.debug(f'no zoom found for {new}. defaulting to {pxpermm}')

        pxpermm = self._loading_manager.stage_manager.autocenter_manager.pxpermm
        cw_px = int(cw * pxpermm)
        ch_px = int(ch * pxpermm)
        w, h = get_size(frame)
        x = int((w - cw_px) / 2.0)
        y = int((h - ch_px) / 2.0)
        return asarray(crop(frame, x, y, cw_px, ch_px))

    def _check_position(self, hole):
        pass

    # def _check_position(self, hole):
    #     pos = hole.id
    #
    #     self.debug('check position {}'.format(pos))
    #     frame = self.new_image_frame(pos)
    #     self._loading_manager.stage_manager.snapshot(name='{}.tc'.format(pos),
    #                                                  render_canvas=False, inform=False)
    #     blankframe = self._get_blankframe(pos)
    #
    #     self.display_image.clear()
    #     self.display_image.tile(frame)
    #     if blankframe is not None:
    #         diff = frame - blankframe
    #         self.display_image.tile(blankframe)
    #         self.display_image.tile(diff)
    #         # self.display_image.tile(diff)
    #     self.display_image.tilify()
    #     # invoke_in_main_thread(self.trait_set, refresh_image=True)
    #     # self.refresh_image = True
    #     self.display_image.refresh_needed = True
    #
    # def _check_position_ml(self, pipe, pos):
    #     self.debug('check position nn {}'.format(pos))
    #
    #     frame = self.new_image_frame(pos)
    #     if pipe is not None:
    #         result = pipe.predict(frame.flatten())
    #         self.info('check_position result={}'.format(result))
    #
    #     else:
    #         self.debug('dumb position check')
    #         self._check_position(pos)
    #
    #     # blankframe = self._get_blankframe(pos)
    #     # if not self.locator.find_grain(im, blankframe, frame, dim):
    #     #     self.debug('no grain found {}'.format(pos))

    def _classify(self, frame):
        pipe = self._get_classifier()
        if pipe:
            result = pipe.predict(frame.flatten())
            self.debug(f'classify={result}')

    def _advance(self, label):
        self._labels.append(LABEL_MAP.get(label, -1))
        self._samples.append(self._active_frame)

        trayname = self._loading_manager.stage_manager.stage_map.name
        name = f'{trayname}-{self._active_position}'
        # self.traydb.add_labeled_sample(name, self._active_frame, label)
        self._add_labeled_sample(name, self._active_frame, label)
        self._visit_next_position()

    def _add_unlabeled_image(self, pos, frame):
        host = '129.138.12.35:8000'
        url = f'http://{host}/add_unclassified_image'

        buf = io.BytesIO()
        im = Image.fromarray(frame)
        im.save(buf, 'tiff')


        trayname = self._loading_manager.stage_manager.stage_map.name
        zm = self._loading_manager.zoom_level

        data = {
                    'trayname': trayname,
                    'hole_id': pos,
                    'zoom_level': zm,
                    'image': base64.b64encode(buf.getvalue()).decode()
                }

        load_pos = self._loading_manager.get_load_position_by_position(pos)
        if load_pos:
            data['identifier'] = load_pos.identifier
            data['sample'] = load_pos.sample
            data['material'] = load_pos.material
            data['project'] = load_pos.project
            data['note'] = load_pos.note
            data['nxtals'] = load_pos.nxtals
            data['weight'] = load_pos.weight

        if self._loading_manager.load_instance:
            data['loadname'] = self._loading_manager.load_instance.name
        try:
            resp = requests.post(url, json=data)
        except requests.exceptions.ConnectionError:
            self.warning('failed posting to central database')

    def _add_labeled_sample(self, name, frame, label):
        pass

    def _stop_button_fired(self):
        self.stop()

    def _good_button_fired(self):
        self._advance('good')

    def _empty_button_fired(self):
        self._advance('empty')

    def _multigrain_button_fired(self):
        self._advance('multigrain')

    def _contaminant_button_fired(self):
        self._advance('contaminant')


def main():
    tc = TrayChecker(None,
                     dbpath='/Users/ross/Sandbox/loadimages/db.sqlite')
    # tc.train_ml()
    tc.test_ml()


if __name__ == '__main__':
    paths.build('~/PychronDev')
    logging_setup('traydb')
    main()

# ============= EOF =============================================
