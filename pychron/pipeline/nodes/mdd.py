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
import logging
import os
import subprocess
import time

from pyface.constant import OK
from pyface.directory_dialog import DirectoryDialog
from pyface.message_dialog import warning
from traits.api import Str, Enum, Bool, Int, Float, HasTraits, List, Instance, Button
from traitsui.api import UItem, Item, View, TableEditor, VGroup, InstanceEditor, ListStrEditor
from traitsui.table_column import ObjectColumn

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.options.options_manager import MDDFigureOptionsManager
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.figure import FigureNode

# class FortranProcess:
#     def __init__(self, path, queue):
#         self.path = path
#
#     def start(self, name):
#         # os.chdir(os.path.join(os.path.dirname(self.path), name))
#         p = subprocess.Popen([self.path],
#                              shell=False,
#                              bufsize=1024,
#                              stdout=subprocess.PIPE
#                              )
#         return p
#
#         # while p.poll() is None:
#         #     self.queue.put(p.stdout.readline(), timeout=0.1)
#         #     time.sleep(1e-6)


# files
# arrme
# autoarr

# --- generate thermal histories
# autoagemon
# autoagefree

EOF = 1


class MDDWorkspace(HasTraits):
    roots = List
    add_root_button = Button

    def _add_root_button_fired(self):
        dlg = DirectoryDialog(default_path=paths.mdd_data_dir)
        if dlg.open() == OK and dlg.path:
            name = os.path.basename(dlg.path)
            if os.path.isfile(os.path.join(dlg.path, '{}.in'.format(name))):
                self.roots.append(dlg.path)
            else:
                warning(None, 'Invalid MDD directory. {}. Directory must contain file '
                              'named {}.in'.format(dlg.path, name))

    def traits_view(self):
        v = View(VGroup(icon_button_editor('add_root_button', 'add'),
                        UItem('roots', editor=ListStrEditor())))
        return v

    # def _roots_default(self):
    #     return ['/Users/ross/Desktop/12H',
    #             '/Users/ross/Desktop/13H']


class MDDWorkspaceNode(BaseNode):
    name = 'MDD Workspace'
    workspace = Instance(MDDWorkspace, ())

    def run(self, state):
        state.mdd_workspace = self.workspace

    def traits_view(self):
        g = VGroup(UItem('workspace', style='custom', editor=InstanceEditor()))
        return okcancel_view(g)


fortranlogger = logging.getLogger('FortranProcess')


class MDDNode(BaseNode):
    executable_name = ''
    configuration_name = ''
    _dumpables = None

    root_dir = Str

    def run(self, state):
        if state.mdd_workspace:
            for root in state.mdd_workspace.roots:
                self.root_dir = root

                self._write_configuration_file()
                os.chdir(root)
                fortranlogger.info('changing to workspace {}'.format(root))
                self.run_fortan()

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
        path = self.executable_path
        name = self.executable_name

        fortranlogger.info('------ started {}'.format(name))
        p = subprocess.Popen([path],
                             shell=False,
                             bufsize=1024,
                             stdout=subprocess.PIPE)

        while p.poll() is None:
            fortranlogger.info(p.stdout.readline().decode('utf8').strip())
            time.sleep(1e-6)
        fortranlogger.info('------ complete {}'.format(name))
        self.post_fortran()

    def post_fortran(self):
        pass

    @property
    def configuration_path(self):
        if not self.configuration_name:
            raise NotImplementedError
        return self.get_path('{}.cl'.format(self.configuration_name))

    @property
    def executable_path(self):
        if not self.executable_name:
            raise NotImplementedError
        return os.path.join(paths.clovera_root, self.executable_name)

    @property
    def rootname(self):
        return os.path.basename(self.root_dir)

    def get_path(self, name):
        return os.path.join(self.root_dir, name)


class MDDLabTable(MDDNode):
    def run(self, state):
        # from the list of unknowns in the current state
        # assemble the <sample>.in file
        # for use with files_py
        pass


class FilesNode(MDDNode):
    name = 'Files'
    configuration_name = 'files'
    executable_name = 'files_py3'

    configurable = False
    _dumpables = ['rootname']


GEOMETRIES = ('Slab', 'Sphere', 'Cylinder')


class GeometryMixin(HasTraits):
    geometry = Enum(*GEOMETRIES)

    @property
    def _geometry(self):
        return GEOMETRIES.index(self.geometry) + 1


class ArrMeNode(MDDNode, GeometryMixin):
    name = 'Arrme'
    configuration_name = 'arrme'
    executable_name = 'arrme_py3'

    _dumpables = ('_geometry',)

    def traits_view(self):
        v = okcancel_view(Item('geometry'))
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


class CoolingStep(HasTraits):
    ctime = Float
    ctemp = Float

    def __init__(self, time, temp):
        self.ctime = float(time)
        self.ctemp = float(temp)


class CoolingHistory(HasTraits):
    steps = List

    def load(self):
        steps = []
        if os.path.isfile(self.path):
            with open(self.path, 'r') as rfile:
                for line in rfile:
                    try:
                        a, b = line.split(',')
                        step = CoolingStep(a, b)
                        steps.append(step)
                    except ValueError:
                        continue
        else:
            for i in range(10):
                step = CoolingStep(10 - 0.5 * i, 500 - i * 50)
                steps.append(step)

        self.steps = steps

    def dump(self):
        with open(self.path, 'w') as wfile:
            for c in self.steps:
                wfile.write('{},{}\n'.format(c.ctime, c.ctemp))

    @property
    def path(self):
        return os.path.join(paths.appdata_dir, 'cooling_history.txt')

    def traits_view(self):
        cols = [ObjectColumn(name='ctime'),
                ObjectColumn(name='ctemp')]
        v = View(UItem('steps', editor=TableEditor(columns=cols, sortable=False)))
        return v


class AgesMeNode(MDDNode, GeometryMixin):
    name = 'AgesMe'
    configuration_name = 'agesme'
    executable_name = 'agesme_py3'
    cooling_history = Instance(CoolingHistory, ())

    _dumpables = ('_geometry',)

    def _pre_run_hook(self, state):
        self.cooling_history.load()

    def _finish_configure(self):
        super(AgesMeNode, self)._finish_configure()

        # write the agesme.in file from specified cooling history
        p = self.get_path('agesme.in')
        with open(p, 'w') as wfile:
            steps = self.cooling_history.steps
            wfile.write('{}\n'.format(len(steps)))
            for ci in steps:
                line = '{}\t{}\n'.format(ci.ctime, ci.ctemp)
                wfile.write(line)

            # include contents of arr-me file
            pp = self.get_path('arr-me.in')
            with open(pp, 'r') as rfile:
                wfile.write(rfile.read())

        self.cooling_history.dump()

    def traits_view(self):
        a = UItem('cooling_history', style='custom')
        g = Item('geometry')
        return okcancel_view(g, a, resizable=True, width=300, height=400)


class AutoAgeFreeNode(MDDNode):
    name = 'AutoAge Free'
    configuration_name = 'autoagefree'
    executable_name = 'autoagefree_py3'


class AutoAgeMonNode(MDDNode):
    name = 'AutoAge Monotonic'
    configuration_name = 'autoagemon'
    executable_name = 'autoage-mon_py3'

    nruns = Int(10)
    max_age = Float(600)

    _dumpables = ['nruns', 'max_age']

    def traits_view(self):
        g = VGroup(Item('nruns'),
                   Item('max_age'))
        return okcancel_view(g)


class MDDFigureNode(FigureNode):
    name = 'MDD Figure'
    editor_klass = 'pychron.pipeline.plot.editors.mdd_figure_editor,MDDFigureEditor'
    plotter_options_manager_klass = MDDFigureOptionsManager

# ============= EOF =============================================
