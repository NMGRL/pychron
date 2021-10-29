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

    @property
    def center_guess_path(self):
        head, tail = os.path.splitext(self.file_path)
        path = "{}.center.txt".format(head)
        return path

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

    @on_trait_change("clear_corrections")
    def clear_correction_file(self):
        p = self.correction_path
        if os.path.isfile(p):
            os.remove(p)
            self.info("removed correction file {}".format(p))

        for h in self.sample_holes:
            h.x_cor = 0
            h.y_cor = 0
            h.corrected = False
            h.interpolated = False

        return p

    def clear_interpolations(self):
        for h in self.sample_holes:
            h.interpolated = False
            h.interpolation_holes = None

    def dump_correction_file(self):
        p = self.correction_path
        with open(p, "wb") as f:
            pickle.dump([(h.id, h.x_cor, h.y_cor) for h in self.sample_holes], f)

        self.info("saved correction file {}".format(p))

    def set_hole_correction(self, hole, x_cor, y_cor):
        self.debug("set hole correction {}, x={}, y={}".format(hole, x_cor, y_cor))
        if not isinstance(hole, SampleHole):
            hole = next((h for h in self.sample_holes if h.id == hole), None)

        if hole is not None:
            self.debug("setting correction {}".format(hole.id))
            hole.x_cor = x_cor
            hole.y_cor = y_cor
            hole.corrected = True

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
