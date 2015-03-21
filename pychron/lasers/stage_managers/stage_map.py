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
from traits.api import HasTraits, Str, Property, CFloat, Float, List, Enum, Button, on_trait_change
from traitsui.api import View, Item, TabularEditor, HGroup
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
import os
from numpy import array
import pickle
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import parse_file
from pychron.paths import paths
from pychron.loggable import Loggable
from pychron.core.geometry.affine import AffineTransform


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

    nominal_position = Property(depends_on='x,y')
    corrected_position = Property(depends_on='x_cor,y_cor')

    associated_hole = Str

    def _get_corrected_position(self):
        return self.x_cor, self.y_cor

    def _get_nominal_position(self):
        return self.x, self.y

    def has_correction(self):
        return self.corrected


#        print self.id, self.x_cor, self.y_cor
#        return True if (abs(self.x_cor) > 1e-6
#                and abs(self.y_cor) > 1e-6) else False


class SampleHoleAdapter(TabularAdapter):
    columns = [('ID', 'id'),
               ('X', 'x'), ('Y', 'y'),
               ('XCor', 'x_cor'), ('YCor', 'y_cor'),
               ('Render', 'render')]

    def set_text(self, obj, trait, row, column, txt):
        if column in [3, 4]:
            try:
                txt = float(txt)
            except:
                txt = '0'

        setattr(getattr(obj, trait)[row], self.columns[column][1], txt)


class StageMap(Loggable):
    file_path = Str
    # holes = Dict
    name = Property(depends_on='file_path')
    bitmap_path = Property(depends_on='file_path')
    #    valid_holes = None
    #    use_valid_holes = True
    # holes = Property
    sample_holes = List(SampleHole)

    g_dimension = Float(enter_set=True, auto_set=False)
    g_shape = Enum('circle', 'square')

    clear_corrections = Button

    # should always be N,E,S,W,center
    calibration_holes = None
    cpos = None
    rotation = None

    def interpolate_noncorrected(self):
        self.info('iteratively fill in non corrected holes')
        n = len(self.sample_holes)
        for i in range(2):
            self._interpolate_noncorrected()

            g = len([h for h in self.sample_holes
                     if h.has_correction()])

            if g == n:
                break
            self.info('iteration {}, total={}'.format(i + 1, g))
        if g < n:
            self.info('{} holes remain noncorrected'.format(n - g))
        else:
            self.info('all holes now corrected')

    def get_interpolated_position(self, holenum, cpos=None, rotation=None):
        self.cpos = cpos
        self.rotation = rotation

        h = self.get_hole(holenum)
        if h is not None:
            nxs = []
            nys = []
            iholes = []
            n = 3
            for sd in range(n):
                xi, yi, hi = self._calculated_interpolated_position(h, sd + 1)
                # do simple weighting by distance
                w = (n - sd)
                nxs += xi * w
                nys += yi * w
                iholes += hi

            if nxs and nys:
                nx, ny = (sum(nxs) / max(1, len(nxs)),
                          sum(nys) / max(1, len(nys)))

                # verify within tolerance
                tol = h.dimension * 0.85

                hx, hy = self.map_to_calibration(h.nominal_position)
                if abs(nx - hx) < tol and abs(ny - hy) < tol:
                    h.interpolated = True
                    h.corrected = True
                    h.interpolation_holes = set(iholes)

                    h.x_cor = nx
                    h.y_cor = ny

                    return nx, ny

    def _interpolate_noncorrected(self):
        self.sample_holes.reverse()
        for h in self.sample_holes:
            self._calculated_interpolated_position(h)

    def _calculated_interpolated_position(self, h, search_distance):
        """
            search distance is a scalar in hole units. it defines how many
            holes away to
        """

        spacing = search_distance * abs(self.sample_holes[0].x - self.sample_holes[1].x)
        #         debug_hole = '18'
        nxs = []
        nys = []
        iholes = []

        if not h.has_correction():
            # this hole does not have a correction value
            found = []
            # get the cardinal holes and corner holes
            for rx, ry in [(0, 1),
                           (-1, 0), (1, 0),
                           (0, -1),

                           (-1, 1), (1, 1),
                           (-1, -1), (1, -1)]:

                x = h.x + rx * spacing
                y = h.y + ry * spacing

                ihole = self._get_hole_by_position(x, y)

                if ihole == h:
                    ihole = None

                fo = None
                if ihole is not None:
                    if ihole.has_correction():
                        fo = ihole
                found.append(fo)

            self._interpolate_midpoint(h, found, nxs, nys, iholes)
            self._interpolate_triangulation(h, found, nxs, nys, iholes)
            self._interpolated_normals(h, found, nxs, nys, iholes, spacing)

        return nxs, nys, iholes

    def _interpolate_midpoint(self, hole, found, nxs, nys, iholes):
        """
            try interpolating using midpoint
        """

        def _midpoint(a, b):
            mx = None
            my = None
            if a and b:
                a = a.corrected_position
                b = b.corrected_position
                dx = abs(a[0] - b[0])
                dy = abs(a[1] - b[1])
                mx = min(a[0], b[0]) + dx / 2.0
                my = min(a[1], b[1]) + dy / 2.0
            return mx, my

        rad = hole.dimension
        for i, j in [(0, 3), (1, 2)]:

            mx, my = _midpoint(found[i], found[j])
            if mx is not None and my is not None:
                # make sure the corrected value makes sense
                # ie less than 1 radius from nominal hole

                hx, hy = self.map_to_calibration(hole.nominal_position)
                if (abs(mx - hx) < rad
                    and abs(my - hy) < rad):
                    nxs.append(mx)
                    nys.append(my)
                    iholes.append(found[i])
                    iholes.append(found[j])

    def _interpolate_triangulation(self, hole, found, nxs, nys, iholes):
        """
            try interpolating using "triangulation"
        """
        rad = hole.dimension
        for i, j in [(0, 1), (0, 2), (3, 2), (3, 1)]:
            if found[i] and found[j]:
                ux, _ = self.map_to_uncalibration(found[i].corrected_position)
                _, uy = self.map_to_uncalibration(found[j].corrected_position)
                if (abs(ux - hole.x) < rad
                    and abs(uy - hole.y) < rad):
                    x, y = self.map_to_calibration((ux, uy))
                    nxs.append(x)
                    nys.append(y)
                    iholes.append(found[i])
                    iholes.append(found[j])

    def _interpolated_normals(self, hole, found, nxs, nys, iholes, spacing):
        # try interpolation using legs of a triangle
        for i, j, s in [
            # vertical
            (4, 1, 1), (6, 1, -1),
            (5, 2, -1), (7, 2, 1),

            # horizontal
            (4, 0, -1), (5, 0, 1),
            (7, 3, -1), (6, 3, 1)]:

            p1 = found[i]
            p2 = found[j]

            if p1 and p2:
                p1 = p1.corrected_position
                p2 = p2.corrected_position

                p1 = self.map_to_uncalibration(p1)
                p2 = self.map_to_uncalibration(p2)
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]

                n = (dx ** 2 + dy ** 2) ** 0.5
                norm = array([-dy, dx]) / n

                npos = array([p2[0], p2[1]]) + (s * spacing * norm)
                nx, ny = self.map_to_calibration(npos)
                nxs.append(nx)
                nys.append(ny)

                iholes.append(found[i])
                iholes.append(found[j])

    def _get_calibration_params(self, cpos, rot, scale):
        if cpos is None:
            cpos = self.cpos if self.cpos else (0, 0)
        if rot is None:
            rot = self.rotation if self.rotation else 0
        if scale is None:
            scale = 1
        return cpos, rot, scale

    def map_to_uncalibration(self, pos, cpos=None, rot=None, scale=None):
        cpos, rot, scale = self._get_calibration_params(cpos, rot, scale)
        a = AffineTransform()
        a.scale(1 / scale, 1 / scale)
        a.rotate(-rot)
        a.translate(cpos[0], cpos[1])
        #        a.translate(-cpos[0], -cpos[1])
        #        a.translate(*cpos)
        #        a.rotate(-rot)
        #        a.translate(-cpos[0], -cpos[1])

        pos = a.transform(*pos)
        return pos

    def map_to_calibration(self, pos, cpos=None, rot=None,
                           use_modified=False,
                           scale=None,
                           translate=None):
        cpos, rot, scale = self._get_calibration_params(cpos, rot, scale)

        a = AffineTransform()
        #         if translate:
        #             a.translate(*translate)

        #        if scale:
        a.scale(scale, scale)
        if use_modified:
            a.translate(*cpos)

        #         print cpos, rot, scale
        a.rotate(rot)
        a.translate(-cpos[0], -cpos[1])
        if use_modified:
            a.translate(*cpos)
        pos = a.transform(*pos)
        return pos

    def get_hole(self, key):
        return next((h for h in self.sample_holes if h.id == str(key)), None)

    def get_hole_pos(self, key):
        """
            hole ids are str so convert key to str
        """
        return next(((h.x, h.y)
                     for h in self.sample_holes if h.id == str(key)), None)

    def get_corrected_hole_pos(self, key):
        return next(((h.x_cor, h.y_cor)
                     for h in self.sample_holes if h.id == key), None)

    def load_correction_file(self):
        p = os.path.join(paths.hidden_dir, '{}_correction_file'.format(self.name))
        if os.path.isfile(p):
            cors = None
            with open(p, 'rb') as f:
                try:
                    cors = pickle.load(f)
                except pickle.PickleError, e:
                    print e

            if cors:
                self.info('loaded correction file {}'.format(p))
                for i, x, y in cors:

                    h = self.get_hole(i)
                    if h is not None:
                        if x is not None and y is not None:
                            h.x_cor = x
                            h.y_cor = y

    @on_trait_change('clear_corrections')
    def clear_correction_file(self):
        p = os.path.join(paths.hidden_dir, '{}_correction_file'.format(self.name))
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

        p = os.path.join(paths.hidden_dir, '{}_correction_file'.format(self.name))
        with open(p, 'wb') as f:
            pickle.dump([(h.id, h.x_cor, h.y_cor)
                         for h in self.sample_holes], f)

        self.info('saved correction file {}'.format(p))

    def set_hole_correction(self, hn, x_cor, y_cor):
        hole = next((h for h in self.sample_holes if h.id == hn), None)
        if hole is not None:
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
                 if abs(getattr(hole, xkey) - x) < tol and abs(getattr(hole, ykey) - y) < tol]
        if holes:
            #            #sort holes by deviation
            holes = sorted(holes, lambda a, b: cmp(a[1], b[1]))
            return holes[0][0]

    def _get_bitmap_path(self):

        name, _ext = os.path.splitext(self.name)
        root, _path = os.path.split(self.file_path)
        name = '.'.join([name, 'png'])
        return os.path.join(root, name)

    def _get_name(self):
        name = os.path.basename(self.file_path)
        name, _ext = os.path.splitext(name)
        return name

    def __init__(self, *args, **kw):
        super(StageMap, self).__init__(*args, **kw)
        self.load()

    def _g_dimension_changed(self):
        for h in self.sample_holes:
            h.dimension = self.g_dimension
        self._save_()

    def _g_shape_changed(self):
        for h in self.sample_holes:
            h.shape = self.g_shape
        self._save_()

    def _save_(self):
        pass

    #        with open(self.file_path, 'r') as f:
    #            lines = [line for line in f]
    #
    #        lines[0] = '{},{}\n'.format(self.g_shape, self.g_dimension)
    #        with open(self.file_path, 'w') as f:
    #            f.writelines(lines)

    def load(self):
        lines = parse_file(self.file_path)
        if not lines:
            return

        # line 0 shape, dimension
        shape, dimension = lines[0].split(',')
        self.g_shape = shape
        self.g_dimension = float(dimension)

        # line 1 list of holes to default draw
        valid_holes = lines[1].split(',')

        # line 2 list of calibration holes
        # should always be N,E,S,W,center
        self.calibration_holes = lines[2].split(',')

        # for hi, line in enumerate(lines[3:]):
        hi = 0
        for line in lines[3:]:
            if not line.startswith('#'):
                ah=''
                args = line.split(',')
                if len(args) == 2:
                    x, y = args
                    hole = str(hi + 1)
                elif len(args) == 3:
                    hole, x, y = args
                    if '(' in y:
                        hole = str(hi + 1)
                        x, y, ah = args
                        ah = ah.strip()
                        ah = ah[1:-1]

                elif len(args) == 4:
                    hole, x, y, ah = args
                    if '(' in ah:
                        ah = ah.strip()
                        ah = ah[1:-1]
                else:
                    self.warning(
                        'invalid stage map file. {}. Problem with line {}: {}'.format(self.file_path, hi + 3, line))
                    break
                # try:
                #     hole, x, y = line.split(',')
                # except ValueError:
                #     try:
                #         x, y = line.split(',')
                #         hole = str(hi + 1)
                #     except ValueError:
                #         break

                self.sample_holes.append(SampleHole(id=hole,
                                                    x=float(x),
                                                    y=float(y),
                                                    associated_hole=ah,
                                                    render='x' if hole in valid_holes else '',
                                                    shape=shape,
                                                    dimension=float(dimension)))
                hi += 1
                # ============= views ===========================================

    def traits_view(self):
        #        cols = [ObjectColumn(name = 'id'),
        #              ObjectColumn(name = 'x'),
        #              ObjectColumn(name = 'y'),
        #              CheckboxColumn(name = 'render')
        #              ]
        #        editor = TableEditor(columns = cols)


        editor = TabularEditor(adapter=SampleHoleAdapter())
        v = View(
            HGroup(Item('clear_corrections', show_label=False)),
            HGroup(Item('g_shape'),
                   Item('g_dimension'), show_labels=False),

            Item('sample_holes',
                 show_label=False, editor=editor),
            height=500, width=250,
            resizable=True,
            title=self.name)
        return v


import yaml


class UVStageMap(StageMap):
    def dump_correction_file(self):
        '''
            dont dump a correction file for a uv stage map
        '''
        pass


    def load(self):
        with open(self.file_path, 'r') as fp:
            d = yaml.load(fp.read())
            for attr in ('points', 'lines', 'polygons', 'transects'):
                if d.has_key(attr):
                    setattr(self, attr, d[attr])

    def get_polygon(self, name):
        return self._get_item('polygon', 'r', name)

    #
    #    def get_point(self, name):
    # #        print name, TRANSECT_REGEX.match(name)
    #        if TRANSECT_REGEX.match(name):
    #            t, p = map(int, name[1:].split('-'))
    # #            print t, p, len(self.transects)
    #            if t <= len(self.transects):
    #                tran = self.transects[t-1]
    #                pts = tran['points']
    #
    #                if p <= len(pts)-1:
    #                    return pts[p]
    #        else:
    #            pt = self._get_item('points', 'p', name)
    #            if pt is None:
    #                v = int(name)
    #                pt = self.points[v - 1]
    #
    #            return pt

    #        if name.startswith('p'):
    #            v = int(name[1:])
    #        else:
    #            v = int(name)
    #
    #
    #        return pt

    def get_line(self, name):
        #        pos = None
        #        name = name.lower()
        #        if name.startswith('l'):
        #            v = int(name[1:])
        #            pos = self.lines[v - 1]
        #        return pos
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

#                nfound = [f for f in found if f is not None]
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

