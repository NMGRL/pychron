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
import os

from traits.api import HasTraits, Str, CFloat, Float, Property, List, Enum

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.geometry.affine import transform_point, \
    itransform_point
# from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.loggable import Loggable


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

    nominal_position = Property(depends_on='x,y')
    corrected_position = Property(depends_on='x_cor,y_cor')

    associated_hole = Str

    def _get_corrected_position(self):
        return self.x_cor, self.y_cor

    def _get_nominal_position(self):
        return self.x, self.y

    def has_correction(self):
        return self.corrected


class BaseStageMap(Loggable):
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

    # should always be N,E,S,W,center
    calibration_holes = None

    def __init__(self, *args, **kw):
        super(BaseStageMap, self).__init__(*args, **kw)
        self.load()

    def load(self):

        with open(self.file_path, 'r') as rfile:

            line = rfile.readline()
            # line 0 shape, dimension
            shape, dimension = line.split(',')
            self.g_shape = shape
            self.g_dimension = dimension = float(dimension)

            # line 1 list of holes to default draw
            line = rfile.readline()
            valid_holes = line.split(',')

            # line 2 list of calibration holes
            # should always be N,E,S,W,center
            line = rfile.readline()
            self.calibration_holes = line.split(',')

            # for hi, line in enumerate(lines[3:]):
            hi = 0
            sms = []
            for line in rfile:
                if not line.startswith('#'):

                    # try:
                    #     hole, x, y = line.split(',')
                    # except ValueError:
                    #     try:
                    #         x, y = line.split(',')
                    #         hole = str(hi + 1)
                    #     except ValueError:
                    #         break
                    h = self._hole_factory(hi, line, shape, dimension,
                                           valid_holes)
                    if h is None:
                        break

                    sms.append(h)
                    hi += 1
            else:
                self.sample_holes = sms

            self._load_hook()

    def get_calibration_hole(self, h):
        d = 'north', 'east', 'south', 'west'
        try:
            idx = d.index(h)
        except IndexError, e:
            self.debug('^^^^^^^^^^^^^^^^^^^ index error: {}, {}, {}'.format(d, h, e))
            return

        try:
            key = self.calibration_holes[idx]
            return self.get_hole(key.strip())
        except ValueError, e:
            self.debug('^^^^^^^^^^^^^^^^^^^ value error: {}, {}, {}'.format(idx, key, e))

    def map_to_uncalibration(self, pos, cpos=None, rot=None, scale=None):
        cpos, rot, scale = self._get_calibration_params(cpos, rot, scale)
        return itransform_point(pos, cpos, rot, scale)
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

        return transform_point(pos, cpos, rot, scale)

    def get_hole(self, key):
        return next((h for h in self.sample_holes if h.id == str(key)), None)

    def get_hole_pos(self, key):
        """
            hole ids are str so convert key to str
        """
        return next(((h.x, h.y)
                     for h in self.sample_holes if h.id == str(key)), None)

    def check_valid_hole(self, key):
        if self.sample_holes:
            hole = self.get_hole(key)
            if hole is None:
                msg = '''{} is not a valid hole for tray '{}'. '''.format(key,
                                                                          self.name)
            else:
                return True
        else:
            msg = '''There a no holes in tray "{}". This is most likely because the file "{}" was not
properly parsed. \n\n
Check that the file is UTF-8 and Unix (LF) linefeed'''.format(self.name,
                                                              self.file_path)

        invoke_in_main_thread(self.warning_dialog, msg)

    def get_corrected_hole_pos(self, key):
        return next(((h.x_cor, h.y_cor)
                     for h in self.sample_holes if h.id == key), None)

    def clear_correction_file(self):
        pass

    # private
    def _load_hook(self):
        pass

    def _hole_factory(self, hi, line, shape, dimension, valid_holes):
        ah = ''
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
            self.warning('invalid stage map file. {}. '
                         'Problem with line {}: {}'.format(self.file_path,
                                                           hi + 3, line))
            return
        return SampleHole(id=hole,
                          x=float(x),
                          y=float(y),
                          associated_hole=ah,
                          render='x' if hole in valid_holes else '',
                          shape=shape,
                          dimension=dimension)

    def _get_bitmap_path(self):

        name, _ext = os.path.splitext(self.name)
        root, _path = os.path.split(self.file_path)
        name = '.'.join([name, 'png'])
        return os.path.join(root, name)

    def _get_name(self):
        name = os.path.basename(self.file_path)
        name, _ext = os.path.splitext(name)
        return name

    def _get_calibration_params(self, cpos, rot, scale):
        if cpos is None:
            cpos = self.cpos if self.cpos else (0, 0)
        if rot is None:
            rot = self.rotation if self.rotation else 0
        if scale is None:
            scale = 1
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
        with open(self.file_path, 'r') as f:
            lines = [line for line in f]

        lines[0] = '{},{}\n'.format(self.g_shape, self.g_dimension)
        with open(self.file_path, 'w') as f:
            f.writelines(lines)

# ============= EOF =============================================
