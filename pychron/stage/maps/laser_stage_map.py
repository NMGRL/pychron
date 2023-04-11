# ===============================================================================
# Copyright 2011 Jake Ross
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
from __future__ import absolute_import

import os
import pickle
import shutil

import yaml
from numpy import array, mean, correlate, std, corrcoef
from traits.api import Button, on_trait_change

from pychron.core.yaml import yload
from pychron.paths import paths
from pychron.stage.maps.base_stage_map import BaseStageMap, SampleHole


def get_interpolation_holes(idx, row):
    n = len(row)
    eidx = n - 1
    midx = eidx // 2
    if idx < midx:
        a, b = row[0], row[midx]
        p = idx / float(midx)
        if not a.has_correction():
            a = row[midx]
            b = row[-1]
            p = (idx - midx) / float(eidx - midx)
        elif not b.has_correction():
            b = row[-1]
            p = idx / float(eidx)
    else:
        a, b = row[midx], row[-1]
        p = (idx - midx) / float((eidx - midx))
        if not a.has_correction():
            a = row[0]
            p = idx / float(eidx)
        elif not b.has_correction():
            a = row[0]
            b = row[midx]
            p = idx / float(midx)

    if a.has_correction() and b.has_correction():
        return a, b, p


class LaserStageMap(BaseStageMap):
    clear_corrections = Button

    cpos = None
    rotation = None
    zoom_level = 1

    @property
    def center_guess_path(self):
        head, tail = os.path.splitext(self.file_path)
        path = "{}.center.txt".format(head)
        return path

    @property
    def correction_affine_path(self):
        p = ""
        if paths.hidden_dir:
            p = os.path.join(paths.hidden_dir, "{}_correction_affine_file.yaml".format(self.name))
        return p

    @property
    def correction_path(self):
        p = ""
        if paths.hidden_dir:
            p = os.path.join(paths.hidden_dir, "{}_correction_file".format(self.name))
        return p

    def set_center_guess(self, x, y):
        previous = []
        p = self.center_guess_path
        if os.path.isfile(p):
            with open(p, "rb") as rfile:
                previous = [
                    l if l[0] == "#" else "#{}".format(l) for l in rfile.readlines()
                ]

        previous.append("{},{}\n".format(x, y))
        with open(p, "wb") as wfile:
            for lin in previous:
                wfile.write(lin.encode("utf-8"))

    def finger_print(self, keys, resultarr):
        """

        """
        # get our same holes as those in results
        holes = [self.get_hole(k.hole_id) for k in keys]

        # get our corrected positions as an array
        hs = array([(h.x_cor, h.y_cor) for h in holes]).flat

        # calculate correlation coeffs
        corr = corrcoef(hs.flat, resultarr)
        return corr[0, 1]

        """
        do a normalized cross correlation between our corrected positions and the correct positions for `tholes`

        the larger the value the better the match. 1.0 indicates perfect match i.e. autocorrelation
        """
        # holes = [self.get_hole(k.id) for k in tholes]
        #
        # def crosscorr(k):
        #     hs = array([getattr(h, k) for h in holes])
        #     ts = array([getattr(h, k) for h in tholes])
        #     if hs.any() and ts.any():
        #         hs = (hs - mean(hs)) / (std(hs) * len(hs))
        #         ts = (ts - mean(ts)) / (std(ts))
        #         return correlate(hs, ts)
        #     else:
        #         return 0
        #
        # return ((crosscorr('x_cor') + crosscorr('y_cor')) / 2)[0]

    def has_correction_file(self):
        return os.path.isfile(self.correction_path)

    _corrected_zoom_level = None

    def load_correction_affine_file(self, force=False):
        if not self.corrected_affine or self._corrected_zoom_level != self.zoom_level or force:
            self.debug(f'load correction affine file for zoom_level={self.zoom_level}')
            p = self.correction_affine_path
            correction_table = yload(p)
            self.corrected_affine = correction_table.get(str(self.zoom_level))
            self._corrected_zoom_level = self.zoom_level

            self.debug(f'corrected_affine {self.corrected_affine}')

    def update_correction_affine_file(self, center, rotation):
        self.debug(f'update correction affine file center={center} rotation={rotation}')
        p = self.correction_affine_path
        correction_table = yload(p)
        correction_table[str(self.zoom_level)] = {'translation': list(center), 'rotation': rotation}
        with open(p, 'w') as wfile:
            yaml.dump(correction_table, wfile)

        self.load_correction_affine_file(force=True)

    def load_correction_file(self):
        self.debug("load correction file")
        p = self.correction_path
        if os.path.isfile(p):
            cors = None
            with open(p, "rb") as f:
                try:
                    cors = pickle.load(f)
                except (ValueError, pickle.PickleError, EOFError) as e:
                    self.warning_dialog(
                        "Failed to load the correction file:\n{}\n"
                        "If you are relying on SemiAuto or Auto calibration a "
                        "recalibration is required".format(p)
                    )
                    if self.confirmation_dialog(
                            "Would you like to delete the file:\n {}".format(p)
                    ):
                        os.remove(p)
            if cors:
                self.info("loaded correction file {}".format(p))
                for i, x, y in cors:
                    h = self.get_hole(i)
                    if h is not None:
                        if x is not None and y is not None:
                            h.x_cor = x
                            h.y_cor = y
                            h.corrected = True

    def generate_row_interpolated_corrections(self, dump_corrections=True):
        self.debug("generate row interpolated corrections")
        rowdict = self.row_dict()
        for i, h in enumerate(self.sample_holes):
            self.debug(
                "{:03n} {} has correction ={}".format(i, h.id, h.has_correction())
            )
            if not h.has_correction():
                row = rowdict[h.y]
                args = get_interpolation_holes(row.index(h), row)
                if args:
                    a, b, p = args
                    self.debug(
                        "interpolation holes a={}, b={}, p={}".format(a.id, b.id, p)
                    )

                    dx = b.x_cor - a.x_cor
                    dy = b.y_cor - a.y_cor
                    cx = a.x_cor + dx * p
                    cy = a.y_cor + dy * p

                    self.set_hole_correction(h, cx, cy)

        if dump_corrections:
            self.dump_correction_file()

    # private
    def _load_hook(self):
        self.load_correction_file()
        self.load_correction_affine_file()

    @on_trait_change("clear_corrections")
    def clear_correction_file(self):
        p = self.correction_path
        if os.path.isfile(p):
            # os.remove(p)
            root, name = os.path.split(p)
            bp = os.path.join(root, f'~{name}')
            shutil.move(p, bp)
            self.info(f"backup correction file {p} to {bp}")

        for h in self.sample_holes:
            h.x_cor = 0
            h.y_cor = 0
            h.corrected = False
            h.interpolated = False
            h.calibrated_position = None

        self.secondary_calibration = None
        return p

    def clear_interpolations(self):
        for h in self.sample_holes:
            h.interpolated = False
            h.interpolation_holes = None

    def dump_corrections_affine(self):
        p = self.correction_affine_path
        with open(p, 'w') as wfile:
            yaml.dump(self.corrected_affine, wfile)
        self.info(f'saved correction affine file to {p}')

    def dump_correction_file(self):
        p = self.correction_path
        with open(p, "wb") as f:
            pickle.dump([(h.id, h.x_cor, h.y_cor) for h in self.sample_holes], f)

        self.info("saved correction file {}".format(p))

    def set_hole_correction(self, hole, x_cor, y_cor):
        hole = self.get_hole(hole)
        self.debug("set hole correction {}, x={}, y={}".format(hole, x_cor, y_cor))
        # if not isinstance(hole, SampleHole):
        #     hole = next((h for h in self.sample_holes if int(h.id) == int(hole)), None)

        if hole is not None:
            self.debug("setting correction {}".format(hole.id))
            hole.x_cor = x_cor
            hole.y_cor = y_cor
            hole.corrected = True
            # self.update_secondary_calibration(hole)

    def _get_hole_by_position(self, x, y, tol=None):
        return self._get_hole_by_pos(x, y, "x", "y", tol)

    def _get_hole_by_corrected_position(self, x, y, tol=None):
        return self._get_hole_by_pos(x, y, "x_cor", "y_cor", tol)

    def _get_hole_by_pos(self, x, y, xkey, ykey, tol):
        if tol is None:
            tol = self.g_dimension  # * 0.75

        def pythag(hi, xi, yi):
            return ((hi.x - xi) ** 2 + (hi.y - yi) ** 2) ** 0.5

        holes = [
            (hole, pythag(hole, x, y))
            for hole in self.sample_holes
            if abs(getattr(hole, xkey) - x) < tol and abs(getattr(hole, ykey) - y) < tol
        ]
        if holes:
            # sort holes by deviation
            holes = sorted(holes, lambda a, b: (a[1] > b[1]) - (a[1] < b[1]))
            return holes[0][0]

    def traits_view(self):
        from .stage_map_view import StageMapView

        return StageMapView(model=self).traits_view()


class UVLaserStageMap(LaserStageMap):
    def dump_correction_file(self):
        """
        dont dump a correction file for a uv stage map
        """
        pass

    def load(self):
        d = yload(self.file_path)
        for attr in ("points", "lines", "polygons", "transects"):
            if attr in d:
                setattr(self, attr, d[attr])

    def get_polygon(self, name):
        return self._get_item("polygon", "r", name)

    def get_line(self, name):
        return self._get_item("lines", "l", name)

    def _get_item(self, name, key, value):
        pos = None
        value = value.lower()
        if value.startswith(key):
            items = getattr(self, name)
            v = int(value[1:])
            pos = items[v - 1]

        return pos

# ============= EOF =============================================
