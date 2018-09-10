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
import shutil
import subprocess
import time

from apptools.preferences.preference_binding import bind_preference
from pyface.confirmation_dialog import confirm
from pyface.constant import OK, YES
from pyface.directory_dialog import DirectoryDialog
from pyface.message_dialog import warning
from traits.api import Str, Enum, Bool, Int, Float, HasTraits, List, Instance, Button, CFloat
from traitsui.api import UItem, Item, View, TableEditor, VGroup, InstanceEditor, ListStrEditor, HGroup
from traitsui.table_column import ObjectColumn
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.iterfuncs import groupby_group_id, groupby_key
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_editor import grouped_name
from pychron.globals import globalv
from pychron.mdd import GEOMETRIES
from pychron.options.options_manager import MDDFigureOptionsManager
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.figure import FigureNode
from pychron.processing.analyses.analysis_group import StepHeatAnalysisGroup
from pychron.regex import MDD_PARAM_REGEX

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

    def _roots_default(self):
        r = []
        if globalv.mdd_workspace_debug:
            r = [
                # os.path.join(paths.mdd_data_dir, '66208-01'),
                os.path.join(paths.mdd_data_dir, '12H')
            ]
        return r


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
    executable_root = Str

    def __init__(self, *args, **kw):
        super(MDDNode, self).__init__(*args, **kw)
        bind_preference(self, 'executable_root', 'pychron.mdd.executable_root')

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
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)

        while p.poll() is None:
            msg = p.stdout.readline().decode('utf8').strip()
            if msg == 'PYCHRON_INTERRUPT':
                self.handle_interrupt(p)
            else:
                self.handle_stdout(p, msg)
                fortranlogger.info(msg)
            time.sleep(1e-6)

        fortranlogger.info('------ complete {}'.format(name))
        self.post_fortran()

    def handle_stdout(self, proc, msg):
        pass

    def handle_interrupt(self, proc):
        pass

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

        root = self.executable_root
        if not root:
            root = paths.clovera_root

        return os.path.join(root, self.executable_name)

    @property
    def rootname(self):
        return os.path.basename(self.root_dir)

    def get_path(self, name):
        return os.path.join(self.root_dir, name)


class MDDLabTableNode(MDDNode):
    name = 'MDD Lab Table'

    temp_offset = Float
    time_offset = Float

    def __init__(self, *args, **kw):
        super(MDDLabTableNode, self).__init__(*args, **kw)
        bind_preference(self, 'temp_offset', 'pychron.mdd.default_temp_offset')

    def run(self, state):
        # from the list of unknowns in the current state
        # assemble the <sample>.in file
        # for use with files_py
        roots = []
        state.mdd_workspace = MDDWorkspace()
        for gid, unks in groupby_group_id(state.unknowns):
            unks = list(unks)
            unk = unks[0]
            name = '{}-{:02n}'.format(unk.identifier, unk.aliquot)
            root = os.path.join(paths.mdd_data_dir, name)
            if os.path.isdir(root):
                if confirm(None, '{} already exists. Backup existing?'.format(root)) == YES:
                    head, tail = os.path.split(root)
                    dest = os.path.join(head, '~{}'.format(tail))
                    if os.path.isdir(dest):
                        shutil.rmtree(dest)

                    shutil.move(root, dest)

            if not os.path.isdir(root):
                os.mkdir(root)

            roots.append(root)
            ag = StepHeatAnalysisGroup(analyses=unks)
            with open(os.path.join(root, '{}.in'.format(name)), 'w') as wfile:
                step = 0
                for unk in ag.analyses:
                    if unk.age > 0:
                        cum39 = ag.cumulative_ar39(step)
                        line = self._assemble(step, unk, cum39)
                        wfile.write(line)
                        step += 1

        state.mdd_workspace.roots = roots

    def _assemble(self, step, unk, cum39):
        """
        step, T(C), t(min), 39mol, %error 39, cum ar39, age, age_er, age_er_w_j, cl_age, cl_age_er

        cl_age and cl_age_er are currently ignored. Ar/Ar age is used as a placeholder instead
        :param unk:
        :return:
        """
        temp = unk.extract_value
        time_at_temp = unk.extract_duration / 60.
        molv = unk.moles_k39

        mol_39, e = nominal_value(molv), std_dev(molv)
        mol_39_perr = e / mol_39 * 100

        age = unk.age
        age_err = unk.age_err_wo_j
        age_err_w_j = unk.age_err

        cols = [step + 1, temp - self.temp_offset, time_at_temp - self.time_offset,
                mol_39, mol_39_perr, cum39, age, age_err, age_err_w_j, age, age_err]
        cols = ','.join([str(v) for v in cols])
        return '{}\n'.format(cols)

    def traits_view(self):
        g = VGroup(Item('temp_offset', label='Temp. Offset (C)', tooltip='Subtract Temp Offset from nominal lab '
                                                                         'extraction temperature. e.g '
                                                                         'temp = lab_temp - temp_offset'),
                   Item('time_offset', label='Time Offset (Min)', tooltip='Subtract Time Offset from nominal lab '
                                                                          'extraction time. e.g '
                                                                          'time = lab_time - time_offset'))
        return okcancel_view(g, title='Configure Lab Table')


class FilesNode(MDDNode):
    name = 'Files'
    configuration_name = 'files'
    executable_name = 'files_py3'

    configurable = False
    _dumpables = ['rootname']


class GeometryMixin(HasTraits):
    geometry = Enum(*GEOMETRIES)

    def __init__(self, *args, **kw):
        super(GeometryMixin, self).__init__(*args, **kw)
        bind_preference(self, 'geometry', 'pychron.mdd.default_geometry')

    @property
    def _geometry(self):
        idx = 0
        if self.geometry in GEOMETRIES:
            idx = GEOMETRIES.index(self.geometry)

        return idx+1


class ArrMeNode(MDDNode, GeometryMixin):
    name = 'Arrme'
    configuration_name = 'arrme'
    executable_name = 'arrme_py3'

    _dumpables = ('_geometry',)

    def traits_view(self):
        v = okcancel_view(Item('geometry'), title='Configure ArrMe')
        return v


class ArrMultiNode(MDDNode):
    name = 'ArrMulti'
    configuration_name = 'arrmulti'
    executable_name = 'arrmulti_py3'

    npoints = Int(10)
    _dumpables = ('npoints', 'rootname')

    e = CFloat
    e_err = CFloat
    ordinate = CFloat
    ordinate_err = CFloat

    def handle_stdout(self, proc, msg):
        mt = MDD_PARAM_REGEX.match(msg)
        if mt:
            self.e = mt.group('E')
            self.e_err = mt.group('Eerr')
            self.ordinate = mt.group('O')
            self.ordinate_err = mt.group('Oerr')

    def handle_interrupt(self, proc):
        fortranlogger.debug('starting interrupt')
        v = okcancel_view(VGroup(HGroup(Item('e', format_str='%0.5f'),
                                        UItem('e_err', format_str='%0.5f')),
                                 HGroup(Item('ordinate', format_str='%0.5f'),
                                        UItem('ordinate_err', format_str='%0.5f'))),
                          width=500,
                          title='Edit Model Parameters')

        info = self.edit_traits(v, kind='livemodal')
        if info.result:
            # print([str(getattr(self, v)).encode() for v in ('e', 'e_err', 'ordinate', 'ordinate_err')])
            l = ' '.join([str(getattr(self, v)) for v in ('e', 'e_err', 'ordinate', 'ordinate_err')])
            proc.stdin.write(l.encode())
            proc.stdin.flush()
            proc.stdin.close()
        fortranlogger.debug('finished interrupt')

    def traits_view(self):
        return okcancel_view(Item('npoints'),
                             title='Configure ArrMulti')


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
        v = okcancel_view(Item('use_defaults'),
                          Item('n_max_domains'),
                          Item('n_min_domains'),
                          Item('use_do_fix'), title='Configure AutoArr')
        return v


class CoolingStep(HasTraits):
    ctime = Float
    ctemp = Float

    def __init__(self, time, temp):
        self.ctime = float(time)
        self.ctemp = float(temp)


class CoolingHistory(HasTraits):
    steps = List
    kind = Enum('Linear')
    start_age = Float(10)
    stop_age = Float(0)
    start_temp = Float(600)
    stop_temp = Float(300)
    nsteps = Int(10)
    generate_curve = Button

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

    def _generate_curve_fired(self):
        s = []
        tstep = (self.start_age - self.stop_age) / (self.nsteps - 1)
        ttstep = (self.start_temp - self.stop_temp) / (self.nsteps - 1)
        for i in range(self.nsteps):
            ctime = self.start_age - i * tstep
            ctemp = self.start_temp - i * ttstep
            cs = CoolingStep(ctime, ctemp)
            s.append(cs)

        self.steps = s

    def traits_view(self):

        cgrp = VGroup(HGroup(Item('start_age', label='Start'), Item('stop_age', label='Stop'), show_border=True,
                             label='Time'),
                      HGroup(Item('start_temp', label='Start'), Item('stop_temp', label='Stop'), show_border=True,
                             label='Temp.'),
                      HGroup(Item('nsteps', label='N Steps'), icon_button_editor('generate_curve', '')))
        cols = [ObjectColumn(name='ctime', format='%0.1f', label='Time (Ma)'),
                ObjectColumn(name='ctemp', format='%0.1f', label='Temp. (C)')]

        v = View(VGroup(cgrp, UItem('steps', editor=TableEditor(columns=cols, sortable=False))))
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
        cool = VGroup(UItem('cooling_history', style='custom'), show_border=True)
        geom = VGroup(Item('geometry'), show_border=True)
        g = VGroup(geom, cool)
        return okcancel_view(g, resizable=True, width=300, height=600, title='Configure AgesMe')


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
                   Item('max_age'), title='Configure AutoAgeMon')
        return okcancel_view(g)


class ConfIntNode(MDDNode):
    name = 'Conf. Int'
    configuration_name = 'confint'
    executable_name = 'confint_py3'

    agein = Float
    agend = Float
    nsteps = Int

    _dumpables = ('agein', 'agend', 'nsteps')

    def traits_view(self):
        g = VGroup(Item('agein', label='Initial Age'),
                   Item('agend', label='Final Age'),
                   Item('nsteps', label='Number of Age Intervals'))
        return okcancel_view(g)


class CorrFFTNode(MDDNode):
    name = 'Corr. FFT'
    executable_name = 'corrfft_py3'


class MDDFigureNode(FigureNode):
    name = 'MDD Figure'
    editor_klass = 'pychron.mdd.tasks.mdd_figure_editor,MDDFigureEditor'
    plotter_options_manager_klass = MDDFigureOptionsManager

    def run(self, state):
        if not state.mdd_workspace:
            state.canceled = True
            return

        editor = self._editor_factory()
        editor.roots = state.mdd_workspace.roots

        na = sorted((os.path.basename(ni) for ni in editor.roots))
        na = grouped_name(na)
        editor.name = '{} mdd'.format(na)

        editor.replot()

        state.editors.append(editor)
        self.editor = editor
        for name, es in groupby_key(state.editors, 'name'):
            for i, ei in enumerate(es):
                ei.name = '{} {:02n}'.format(ei.name, i + 1)
# ============= EOF =============================================
