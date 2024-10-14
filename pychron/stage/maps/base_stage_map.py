# ===============================================================================
# Copyright 2015 Jake Ross
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

import math
import os
import random
from operator import attrgetter

from traits.api import HasTraits, Str, CFloat, Float, Property, List, Enum

from pychron.core.codetools.inspection import caller
from pychron.core.geometry.affine import transform_point, itransform_point
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.loggable import Loggable
from pychron.mv.zoom.zoom import calc_rotation


class SampleHole(HasTraits):
    id = Str
    x = Float
    y = Float
    x_cor = CFloat(0)
    y_cor = CFloat(0)
    render = Str
    shape = Str
    dimension = Float
    interpolated = False
    corrected = False
    interpolation_holes = None
    analyzed = False
    deviation = None
    nominal_position = Property(depends_on="x,y")
    corrected_position = Property(depends_on="x_cor,y_cor")

    associated_hole = Str

    def _get_corrected_position(self):
        return self.x_cor, self.y_cor

    def _get_nominal_position(self):
        return self.x, self.y

    def has_correction(self):
        return self.corrected

    def distance(self, h):
        return ((self.x_cor - h.x_cor) ** 2 + (self.y_cor - h.y_cor) ** 2) ** 0.5

    def vector_distance(self, h):
        return self.x_cor - h.x_cor, self.y_cor - h.y_cor


class BaseStageMap(Loggable):
    file_path = Str
    # holes = Dict
    name = Property(depends_on="file_path")
    bitmap_path = Property(depends_on="file_path")
    #    valid_holes = None
    #    use_valid_holes = True
    # holes = Property
    sample_holes = List(SampleHole)

    g_dimension = Float(enter_set=True, auto_set=False)
    g_shape = Enum("circle", "square")

    # should always be N,E,S,W,center
    calibration_holes = None
    secondary_calibration = None

    corrected_affine = None

    # def __init__(self, *args, **kw):
    #     super(BaseStageMap, self).__init__(*args, **kw)
    #     self.load()

    def load(self):
        self.debug("loading stage map file {}".format(self.file_path))
        with open(self.file_path, "r") as rfile:
            cnt = 0
            for line in rfile:
                if line.startswith("#"):
                    continue

                if "#" in line:
                    line = line.split("#")[0]


                if cnt == 0:
                    # line 0 shape, dimension
                    args = line.split(",")
                    shape, dimension = args[:2]
                    self.g_shape = shape
                    self.g_dimension = dimension = float(dimension)
                elif cnt == 1:
                    # line 1 list of holes to default draw
                    valid_holes = line.split(",")
                elif cnt == 2:
                    # # line 2 list of calibration holes
                    # # should always be N,E,S,W,center
                    self.calibration_holes = line.split(",")
                    break

                cnt += 1

            hi = 0
            sms = []
            for line in rfile:
                line = line.strip()
                if line and not line.startswith("#"):
                    h = self._hole_factory(hi, line, shape, dimension, valid_holes)
                    if h is None:
                        self.warning_dialog("Invalid Stage Map {}".format(self.name))
                        return
                    sms.append(h)
                    hi += 1
            else:
                self.sample_holes = sms

            self._load_hook()
            return True

    def random_choice(self, k=10):
        holes = random.choice(self.sample_holes, k=k)
        return sorted(holes, key=attrgetter("id"))

    def row_dict(self):
        return {k: list(v) for k, v in self._grouped_rows()}

    def row_ends(self, include_mid=False, alternate=False):
        for i, (g, ri) in enumerate(self._grouped_rows()):
            ri = list(ri)

            a, b = ri[0], ri[-1]
            if alternate and i % 2:
                a, b = b, a

            yield a
            if include_mid:
                yield ri[len(ri) / 2]
            yield b

    def all_holes(self):
        for i, (g, ri) in enumerate(self._grouped_rows()):
            if i % 2:
                # odd row
                yield from reversed(list(ri))
            else:
                # even row
                yield from ri

    def circumference_holes(self):
        for i, (g, ri) in enumerate(self._grouped_rows()):
            ri = list(ri)
            yield ri[0]

        for i, (g, ri) in enumerate(self._grouped_rows(reverse=False)):
            ri = list(ri)
            yield ri[-1]

    def mid_holes(self):
        for i, (g, ri) in enumerate(self._grouped_rows()):
            ri = list(ri)
            yield ri[len(ri) // 2]

    def get_calibration_hole(self, h):
        d = "north", "east", "south", "west", "center"
        try:
            idx = d.index(h)
        except IndexError as e:
            self.debug("^^^^^^^^^^^^^^^^^^^ index error: {}, {}, {}".format(d, h, e))
            return

        try:
            key = self.calibration_holes[idx]
        except IndexError as e:
            self.debug("^^^^^^^^^^^^^^^^^^^ index error: {}, {}".format(idx, e))
            self.debug("calibration holes={}".format(self.calibration_holes))
            return

        return self.get_hole(key.strip())

    @caller
    def map_to_uncalibration(self, pos, cpos=None, rot=None, scale=None):
        cpos, rot, scale = self._get_calibration_params(cpos, rot, scale)
        npos = itransform_point(pos, cpos, rot, scale)

        self.load_correction_affine_file()
        if self.corrected_affine:
            cpos = self.corrected_affine["translation"]
            rot = self.corrected_affine["rotation"]
            npos = itransform_point(npos, cpos, rot, 1)

        return npos
        # a = AffineTransform()
        # a.scale(1 / scale, 1 / scale)
        # a.rotate(-rot)
        # a.translate(cpos[0], cpos[1])
        # #        a.translate(-cpos[0], -cpos[1])
        # #        a.translate(*cpos)
        # #        a.rotate(-rot)
        # #        a.translate(-cpos[0], -cpos[1])
        #
        # pos = a.transform(*pos)
        # return pos

    def map_to_calibration(self, pos, cpos=None, rot=None, scale=None):
        cpos, rot, scale = self._get_calibration_params(cpos, rot, scale)

        pt = transform_point(pos, cpos, rot, scale)
        self.debug(
            "map to calibration. pos={}, cpos={}, rot={}. new pos={}".format(
                pos, cpos, rot, pt
            )
        )
        # if self.secondary_calibration and include_secondary:
        #     c, r, s = self.secondary_calibration
        #     npt = transform_point(pt, c, r, s)
        #     self.debug('secondary calibration pos={}, cpos={}, rot={}, new pos={}'.format(pt, c, r, npt))
        #     pt = npt

        return pt

    _bufx = None

    # def update_secondary_calibration(self, h):
    #     """
    #     """
    #     return
    #
    #     if h.corrected_position:
    #         # nx, ny = h.nominal_position
    #         nx, ny = h.calibrated_position
    #         cx, cy = h.corrected_position
    #
    #         # nx -= self.cpos[0]
    #         # ny -= self.cpos[1]
    #         # dx = nx - cx
    #         # dy = ny - cy
    #
    #         # if self._bufx is None:
    #         #     self._bufx = []
    #         #     self._bufy = []
    #         # self._bufx.append(dx)
    #         # self._bufy.append(dy)
    #         #
    #         # dx = sum(self._bufx) / len(self._bufx)
    #         # dy = sum(self._bufy) / len(self._bufy)
    #
    #         # r = math.degrees(math.atan2(dy, dx))
    #         nominal_rotation = math.degrees(math.atan2(ny, nx))
    #         corrected_rotation = math.degrees(math.atan2(cy, cx))
    #         r = corrected_rotation - nominal_rotation
    #
    #         self.debug('secondary rotation calibration {}'.format(ny, nx, cy, cx, r))
    #         # self.secondary_calibration = ((0, 0), r, 1)
    #         # self.debug('nx {} {} {} {} dx={} dy={}'.format(nx, cx, ny, cy, dx, dy))
    #         # c, r, s = calculate_transform(h.nominal_position, h.corrected_position)

    def get_hole(self, key):
        r = key
        if not isinstance(key, SampleHole):
            r = next((h for h in self.sample_holes if h.id == str(key)), None)
        return r

    def get_hole_pos(self, key):
        """
        hole ids are str so convert key to str
        """
        return next(((h.x, h.y) for h in self.sample_holes if h.id == str(key)), None)

    def check_valid_hole(self, key, autocenter_only=False, **kw):
        if autocenter_only and not key:
            return True

        msg = None
        if self.sample_holes:
            hole = self.get_hole(key)
            if hole is None:
                msg = '"{}" is not a valid hole for tray "{}".'.format(key, self.name)
        else:
            msg = """There a no holes in tray "{}". This is most likely because
the file "{}" was not properly parsed. \n\n
Check that the file is UTF-8 and Unix (LF) linefeed""".format(
                self.name, self.file_path
            )
        if msg:
            from pychron.core.ui.gui import invoke_in_main_thread

            invoke_in_main_thread(self.warning_dialog, msg)
        else:
            return True

    def get_corrected_hole_pos(self, key):
        pos = next(
            (
                h.corrected_position if h.has_correction else h.nominal_position
                for h in self.sample_holes
                if int(h.id) == int(key)
            ),
            None,
        )
        if pos is not None:
            self.load_correction_affine_file()

            if self.corrected_affine:
                cpos = self.corrected_affine["translation"]
                rot = self.corrected_affine["rotation"]
                scale = 1
                self.debug(
                    f"applying corrected affine pos={pos} cpos={cpos}, rot={rot}"
                )
                pos = transform_point(pos, cpos, rot, scale)
                self.debug(f"new pos {pos}")
        return pos

    def load_correction_affine_file(self):
        pass

    def clear_correction_file(self):
        pass

    def motion_saver_holes(self):
        for i, rs in self._grouped_rows():
            rs = list(rs)
            if i % 2:
                rs = list(reversed(rs))
            yield rs
            # print(rs[0].id, rs[-1].id)

    # private
    def _grouped_rows(self, reverse=True):
        # def func(x):
        #     return x.y

        # holes = sorted(self.sample_holes, key=func, reverse=reverse)
        # return groupby(holes, key=func)
        return groupby_key(self.sample_holes, "y", reverse=reverse)

    def _load_hook(self):
        pass

    def _hole_factory(self, hi, line, shape, dimension, valid_holes):
        ah = ""
        args = line.split(",")
        if len(args) == 2:
            x, y = args
            hole = str(hi + 1)
        elif len(args) == 3:
            hole, x, y = args
            if "(" in y:
                hole = str(hi + 1)
                x, y, ah = args
                ah = ah.strip()
                ah = ah[1:-1]
            elif y.startswith('r'):
                hole = str(hi + 1)
                x, y, d = args
                print(line)
                dimension = float(d[1:].strip())

        elif len(args) == 4:
            hole, x, y, ah = args
            if "(" in ah:
                ah = ah.strip()
                ah = ah[1:-1]
        else:
            self.warning(
                "invalid stage map file. {}. "
                "Problem with line {}: {}".format(self.file_path, hi + 3, line)
            )
            return
        return SampleHole(
            id=hole,
            x=float(x),
            y=float(y),
            associated_hole=ah,
            render="x" if hole in valid_holes else "",
            shape=shape,
            dimension=dimension,
        )

    def _get_bitmap_path(self):
        name, _ext = os.path.splitext(self.name)
        root, _path = os.path.split(self.file_path)
        name = ".".join([name, "png"])
        return os.path.join(root, name)

    def _get_name(self):
        name = os.path.basename(self.file_path)
        name, _ext = os.path.splitext(name)
        return name

    def _get_calibration_params(self, cpos, rot, scale):
        if cpos is None:
            cpos = self.cpos if self.cpos else (0, 0)
            self.cpos = cpos
        if rot is None:
            rot = self.rotation if self.rotation else 0
            self.rotation = rot
        if scale is None:
            scale = 1
            self.scale = scale

        return cpos, rot, scale

    # handlers
    def _g_dimension_changed(self):
        for h in self.sample_holes:
            h.dimension = self.g_dimension
        self._save()

    def _g_shape_changed(self):
        for h in self.sample_holes:
            h.shape = self.g_shape
        self._save()

    def _save(self):
        with open(self.file_path, "r") as f:
            lines = [line for line in f]

        lines[0] = "{},{}\n".format(self.g_shape, self.g_dimension)
        with open(self.file_path, "w") as f:
            f.writelines(lines)

# ============= EOF =============================================
