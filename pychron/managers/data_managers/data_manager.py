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



# ============= enthought library imports =======================
from traits.api import Dict

# ============= standard library imports ========================
import os

# ============= local library imports  ==========================
from pychron.paths import paths
from pychron.core.helpers.filetools import unique_path
from pychron.managers.manager import Manager
from pychron.core.helpers.datetime_tools import generate_datetimestamp, time_generator


class DataManager(Manager):
    '''
    '''
    _extension = 'txt'
    frames = Dict
    _current_frame = ''
    time_gen = None
    def get_current_path(self):
        pass

    def close_file(self):
        pass

    def new_frame(self, *args, **kw):
        """
        """
        p = self._new_frame_path(*args, **kw)

        name, _ext = os.path.splitext(os.path.basename(p))
        self.frames[name] = p

        self._current_frame = name
        return name

    def _new_frame_path(self, path=None, directory='scans',
                        offset=0,
                        base_frame_name=None, verbose=True):
        """

        """
        if base_frame_name is None:
            base_frame_name = 'scan'

        '''
            if directory is an absolute path paths.data_dir is not joined
        '''

        base = os.path.join(paths.data_dir, directory)
        if not os.path.isdir(base):
            os.mkdir(base)

        if path is None:
            path, _cnt = unique_path(base, base_frame_name,
                                     extension=self._extension)
        if verbose:
            self.info('New frame {}'.format(path))
        return path

    def add_time_stamped_value(self, value, frame_key=None, rawtime=False):
        '''

        '''
        if frame_key is None:
            frame_key = self._current_frame

        frame = self._get_frame(frame_key)
        if frame is not None:
            if rawtime:
                if self.time_gen is None:
                    self.time_gen = time_generator()
                    t = 0
                else:
                    t = self.time_gen.next()
            else:
                t = generate_datetimestamp()
            datum = (t, value)
            self.new_writer(frame, datum)

    def _get_frame(self, key):
        if key in self.frames:
            return self.frames[key]
# ============= EOF ====================================
