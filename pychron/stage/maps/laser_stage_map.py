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
import os
import pickle

import yaml
from traits.api import Button, on_trait_change

from pychron.paths import paths
from pychron.stage.maps.base_stage_map import BaseStageMap, SampleHole


class LaserStageMap(BaseStageMap):
    clear_corrections = Button

    cpos = None
    rotation = None

    @property
    def correction_path(self):
        p = ''
        if paths.hidden_dir:
            p = os.path.join(paths.hidden_dir,
                             '{}_correction_file'.format(self.name))
        return p

    def load_correction_file(self):
        self.debug('load correction file')
        p = self.correction_path
        if os.path.isfile(p):
            cors = None
            with open(p, 'rb') as f:
                try:
                    cors = pickle.load(f)
                except pickle.PickleError, e:
                    print 'exception', e

            if cors:
                self.info('loaded correction file {}'.format(p))
                for i, x, y in cors:

                    h = self.get_hole(i)
                    if h is not None:
                        if x is not None and y is not None:
                            h.x_cor = x
                            h.y_cor = y
                            h.corrected = True

    def _get_interpolation_holes(self, h, row):
        idx = row.index(h)
        n = len(row)
        eidx = n - 1
        midx = eidx / 2
        if idx < midx:
            a, b = row[0], row[midx]
            p = idx / float(midx)
            if not a.has_correction():
                a = row[midx]
                b = row[-1]
                p = (idx - midx) / float(eidx - midx)
                if not a.has_correction() or not b.has_correction():
                    return
            elif not b.has_correction():
                b = row[-1]
                p = idx / float(eidx)
                if not b.has_correction():
                    return
        else:
            a, b = row[midx], row[-1]
            p = (idx - midx) / float((eidx - midx))
            if not a.has_correction():
                a = row[0]
                p = idx / float(eidx)
                if not a.has_correction():
                    return
            elif not b.has_correction():
                a = row[0]
                b = row[midx]
                p = idx / float(midx)
                if not a.has_correction() or not b.has_correction():
                    return

        return a, b, p

    def generate_row_interpolated_corrections(self, dump_corrections=True):
        self.debug('generate row interpolated corrections')
        rowdict = self.row_dict()
        for i, h in enumerate(self.sample_holes):

            self.debug('{:03n} {} has correction ={}'.format(i, h.id, h.has_correction()))
            if not h.has_correction():

                row = rowdict[h.y]
                args = self._get_interpolation_holes(h, row)
                if args:
                    a, b, p = args
                    self.debug('interpolation holes a={}, b={}, p={}'.format(a.id, b.id, p))

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

    @on_trait_change('clear_corrections')
    def clear_correction_file(self):
        p = self.correction_path
        if os.path.isfile(p):
            os.remove(p)
            self.info('removed correction file {}'.format(p))

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
        with open(p, 'wb') as f:
            pickle.dump([(h.id, h.x_cor, h.y_cor)
                         for h in self.sample_holes], f)

        self.info('saved correction file {}'.format(p))

    def set_hole_correction(self, hole, x_cor, y_cor):
        self.debug('set hole correction {}, x={}, y={}'.format(hole, x_cor, y_cor))
        if not isinstance(hole, SampleHole):
            hole = next((h for h in self.sample_holes if h.id == hole), None)

        if hole is not None:
            self.debug('setting correction {}'.format(hole.id))
            hole.x_cor = x_cor
            hole.y_cor = y_cor
            hole.corrected = True

    def _get_hole_by_position(self, x, y, tol=None):
        return self._get_hole_by_pos(x, y, 'x', 'y', tol)

    def _get_hole_by_corrected_position(self, x, y, tol=None):
        return self._get_hole_by_pos(x, y, 'x_cor', 'y_cor', tol)

    def _get_hole_by_pos(self, x, y, xkey, ykey, tol):
        if tol is None:
            tol = self.g_dimension  # * 0.75

        pythag = lambda hi, xi, yi: ((hi.x - xi) ** 2 + (hi.y - yi) ** 2) ** 0.5
        holes = [(hole, pythag(hole, x, y)) for hole in self.sample_holes
                 if abs(getattr(hole, xkey) - x) < tol and abs(
                    getattr(hole, ykey) - y) < tol]
        if holes:
            #            #sort holes by deviation
            holes = sorted(holes, lambda a, b: cmp(a[1], b[1]))
            return holes[0][0]

    def traits_view(self):
        from stage_map_view import StageMapView
        return StageMapView(model=self).traits_view()


class UVLaserStageMap(LaserStageMap):
    def dump_correction_file(self):
        """
            dont dump a correction file for a uv stage map
        """
        pass

    def load(self):
        with open(self.file_path, 'r') as rfile:
            d = yaml.load(rfile.read())
            for attr in ('points', 'lines', 'polygons', 'transects'):
                if attr in d:
                    setattr(self, attr, d[attr])

    def get_polygon(self, name):
        return self._get_item('polygon', 'r', name)

    def get_line(self, name):
        return self._get_item('lines', 'l', name)

    def _get_item(self, name, key, value):
        pos = None
        value = value.lower()
        if value.startswith(key):
            items = getattr(self, name)
            v = int(value[1:])
            pos = items[v - 1]

        return pos

        # ============= EOF =============================================
        #     def interpolate_noncorrected(self):
        #         self.info('iteratively fill in non corrected holes')
        #         n = len(self.sample_holes)
        #         for i in range(2):
        #             self._interpolate_noncorrected()
        #
        #             g = len([h for h in self.sample_holes
        #                      if h.has_correction()])
        #
        #             if g == n:
        #                 break
        #             self.info('iteration {}, total={}'.format(i + 1, g))
        #         if g < n:
        #             self.info('{} holes remain noncorrected'.format(n - g))
        #         else:
        #             self.info('all holes now corrected')
        #
        #     def get_interpolated_position(self, holenum, cpos=None, rotation=None):
        #         self.cpos = cpos
        #         self.rotation = rotation
        #
        #         h = self.get_hole(holenum)
        #         if h is not None:
        #             nxs = []
        #             nys = []
        #             iholes = []
        #             n = 3
        #             for sd in range(n):
        #                 xi, yi, hi = self._calculated_interpolated_position(h, sd + 1)
        #                 # do simple weighting by distance
        #                 w = (n - sd)
        #                 nxs += xi * w
        #                 nys += yi * w
        #                 iholes += hi
        #
        #             if nxs and nys:
        #                 nx, ny = (sum(nxs) / max(1, len(nxs)),
        #                           sum(nys) / max(1, len(nys)))
        #
        #                 # verify within tolerance
        #                 tol = h.dimension * 0.85
        #
        #                 hx, hy = self.map_to_calibration(h.nominal_position)
        #                 if abs(nx - hx) < tol and abs(ny - hy) < tol:
        #                     h.interpolated = True
        #                     h.corrected = True
        #                     h.interpolation_holes = set(iholes)
        #
        #                     h.x_cor = nx
        #                     h.y_cor = ny
        #
        #                     return nx, ny
        # def _interpolate_noncorrected(self):
        #         self.sample_holes.reverse()
        #         for h in self.sample_holes:
        #             self._calculated_interpolated_position(h)
        #
        #     def _calculated_interpolated_position(self, h, search_distance):
        #         """
        #             search distance is a scalar in hole units. it defines how many
        #             holes away to
        #         """
        #
        #         spacing = search_distance * abs(self.sample_holes[0].x - self.sample_holes[1].x)
        #         #         debug_hole = '18'
        #         nxs = []
        #         nys = []
        #         iholes = []
        #
        #         if  not h.has_correction():
        #             # this hole does not have a correction value
        #             found = []
        #             # get the cardinal holes and corner holes
        #             for rx, ry in [(0, 1),
        #                            (-1, 0), (1, 0),
        #                            (0, -1),
        #
        #                            (-1, 1), (1, 1),
        #                            (-1, -1), (1, -1)]:
        #
        #                 x = h.x + rx * spacing
        #                 y = h.y + ry * spacing
        #
        #                 ihole = self._get_hole_by_position(x, y)
        #
        #                 if ihole == h:
        #                     ihole = None
        #
        #                 fo = None
        #                 if ihole is not None:
        #                     if ihole.has_correction():
        #                         fo = ihole
        #                 found.append(fo)
        #
        #             self._interpolate_midpoint(h, found, nxs, nys, iholes)
        #             self._interpolate_triangulation(h, found, nxs, nys, iholes)
        #             self._interpolated_normals(h, found, nxs, nys, iholes, spacing)
        #
        #         return nxs, nys, iholes
        #
        #     def _interpolate_midpoint(self, hole, found, nxs, nys, iholes):
        #         """
        #             try interpolating using midpoint
        #         """
        #
        #         def _midpoint(a, b):
        #             mx = None
        #             my = None
        #             if a and b:
        #                 a = a.corrected_position
        #                 b = b.corrected_position
        #                 dx = abs(a[0] - b[0])
        #                 dy = abs(a[1] - b[1])
        #                 mx = min(a[0], b[0]) + dx / 2.0
        #                 my = min(a[1], b[1]) + dy / 2.0
        #             return mx, my
        #
        #         rad = hole.dimension
        #         for i, j in [(0, 3), (1, 2)]:
        #
        #             mx, my = _midpoint(found[i], found[j])
        #             if mx is not None and my is not None:
        #                 # make sure the corrected value makes sense
        #                 # ie less than 1 radius from nominal hole
        #
        #                 hx, hy = self.map_to_calibration(hole.nominal_position)
        #                 if abs(mx - hx) < rad and abs(my - hy) < rad:
        #                     nxs.append(mx)
        #                     nys.append(my)
        #                     iholes.append(found[i])
        #                     iholes.append(found[j])
        #
        #     def _interpolate_triangulation(self, hole, found, nxs, nys, iholes):
        #         """
        #             try interpolating using "triangulation"
        #         """
        #         rad = hole.dimension
        #         for i, j in [(0, 1), (0, 2), (3, 2), (3, 1)]:
        #             if found[i] and found[j]:
        #                 ux, _ = self.map_to_uncalibration(found[i].corrected_position)
        #                 _, uy = self.map_to_uncalibration(found[j].corrected_position)
        #                 if abs(ux - hole.x) < rad and abs(uy - hole.y) < rad:
        #                     x, y = self.map_to_calibration((ux, uy))
        #                     nxs.append(x)
        #                     nys.append(y)
        #                     iholes.append(found[i])
        #                     iholes.append(found[j])
        #
        #     def _interpolated_normals(self, hole, found, nxs, nys, iholes, spacing):
        #         # try interpolation using legs of a triangle
        #         for i, j, s in [  # vertical
        #
        #                           (4, 1, 1), (6, 1, -1),
        #                           (5, 2, -1), (7, 2, 1),
        #
        #                           # horizontal
        #                           (4, 0, -1), (5, 0, 1),
        #                           (7, 3, -1), (6, 3, 1)]:
        #
        #             p1 = found[i]
        #             p2 = found[j]
        #
        #             if p1 and p2:
        #                 p1 = p1.corrected_position
        #                 p2 = p2.corrected_position
        #
        #                 p1 = self.map_to_uncalibration(p1)
        #                 p2 = self.map_to_uncalibration(p2)
        #                 dx = p2[0] - p1[0]
        #                 dy = p2[1] - p1[1]
        #
        #                 n = (dx ** 2 + dy ** 2) ** 0.5
        #                 norm = array([-dy, dx]) / n
        #
        #                 npos = array([p2[0], p2[1]]) + (s * spacing * norm)
        #                 nx, ny = self.map_to_calibration(npos)
        #                 nxs.append(nx)
        #                 nys.append(ny)
        #
        #                 iholes.append(found[i])
        #                 iholes.append(found[j])

        #        cspacing = spacing
        #        for i, e in enumerate(self.sample_holes[1:]):
        #            s = self.sample_holes[i - 1]
        #            if s.has_correction() and e.has_correction():
        #                dx = abs(s.x_cor - e.x_cor)
        #                dy = abs(s.y_cor - e.y_cor)
        # #                cspacing = (dx + dy) / 2.0
        #                break

        # if the number of adjacent holes found is only 1
        # do a simple offset using

# nfound = [f for f in found if f is not None]
#                if len(nfound) == 1:
#                    f = nfound[0]
#                    ind = found.index(f)
#                    x = f[0]
#                    y = f[1]
#                    l = cspacing#spacing / scalar
#                    if ind == 0:
#                        nxs.append(x)
#                        nys.append(y - l)
#                    elif ind == 1:
#                        nxs.append(x + l)
#                        nys.append(y)
#                    elif ind == 2:
#                        nxs.append(x - l)
#                        nys.append(y)
#                    else:
#                        nxs.append(x)
#                        nys.append(y + l)
