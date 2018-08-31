# ===============================================================================
# Copyright 2018 ross
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
import os
import subprocess
import time
from multiprocessing import Queue

from traits.api import Str, Enum, Bool, Int
from traitsui.api import UItem, Item

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.figure import FigureNode


class FortranProcess:
    def __init__(self, path, queue):
        self.path = path
        self.queue = queue

    def start(self, name):
        os.chdir(os.path.join(os.path.dirname(self.path), name))
        p = subprocess.Popen([self.path],
                             shell=False,
                             bufsize=1024,
                             stdout=subprocess.PIPE
                             )

        while p.poll() is None:
            self.queue.put(p.stdout.readline(), timeout=0.1)
            time.sleep(1e-6)


# files
# arrme
# change age.sd.samp to age.in
# autoarr

# --- generate thermal histories
# autoagemon
# autoagefree


class MDDInFilesNode(BaseNode):
    def run(self, state):
        # create necessary input file
        # columns
        # nstp,t,dtim,a39,sig39,f,age ,sig,terrage,clage,errclage
        pass


class MDDNode(BaseNode):
    executable_name = ''
    configuration_name = ''
    _dumpables = None

    root_dir = Str('12H')

    def run(self, state):
        self.run_fortan()

    def _finish_configure(self):
        self._write_configuration_file()

    def _write_configuration_file(self):
        with open(self.configuration_path, 'w') as wfile:
            for d in self._dumpables:
                if d.startswith('!'):
                    v = d[1:]
                else:
                    v = getattr(self, d)

                if isinstance(v, bool):
                    v = int(v)
                line = '{}\n'.format(v)
                wfile.write(line)

    def run_fortan(self):
        queue = Queue()
        process = FortranProcess(self.executable_path, queue)
        process.start(self.root_dir)
        self.post_fortran()

    def post_fortran(self):
        pass

    @property
    def configuration_path(self):
        if not self.configuration_name:
            raise NotImplementedError
        return os.path.join(paths.clovera_root, self.root_dir, '{}.cl'.format(self.configuration_name))

    @property
    def executable_path(self):
        if not self.executable_name:
            raise NotImplementedError
        return os.path.join(paths.clovera_root, self.executable_name)


class FilesNode(MDDNode):
    name = 'Files'
    configuration_name = 'files'
    executable_name = 'files_py3'

    _dumpables = ['root_dir']

    def post_fortran(self):
        pass

    def traits_view(self):
        v = okcancel_view(UItem('root_dir'))
        return v


GEOMETRIES = ('Slab', 'Sphere', 'Cylinder')


class ArrMeNode(MDDNode):
    name = 'Arrme'
    configuration_name = 'arrme'
    executable_name = 'arrme_py3'
    geometry = Enum(*GEOMETRIES)

    _dumpables = ('_geometry', )
    @property
    def _geometry(self):
        return GEOMETRIES.index(self.geometry) + 1

    def traits_view(self):
        v = okcancel_view(UItem('root_dir'),
                          Item('geometry'))
        return v


class AutoArrNode(MDDNode):
    name = 'AutoArr'
    configuration_name = 'autoarr'
    executable_name = 'autoarr_py3'

    use_defaults = Bool
    n_max_domains = Int(8)
    n_min_domains = Int(3)
    use_do_fix = Bool
    _dumpables = ('use_defaults', 'n_max_domains', 'n_min_domains', 'use_do_fix')

    def traits_view(self):
        v = okcancel_view(UItem('root_dir'),
                          Item('use_defaults'),
                          Item('n_max_domains'),
                          Item('n_min_domains'),
                          Item('use_do_fix'))
        return v


class CompositeFigureNode(FigureNode):
    pass


class LogRNode(MDDNode):
    pass


class ArrheniusNode(MDDNode):
    pass
# ============= EOF =============================================
