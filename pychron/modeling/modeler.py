#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import  Any, Instance, Str, \
    Directory, List, on_trait_change, Property, Enum, Int, Button
from traitsui.api import View, Item, VSplit, TableEditor, EnumEditor, HGroup, VGroup
from traitsui.table_column import ObjectColumn
from traitsui.extras.checkbox_column import CheckboxColumn
from pyface.api import FileDialog, OK
from pyface.directory_dialog import DirectoryDialog
# from enthought.pyface.timer import do_later
# from traitsui.menu import Action, Menu, MenuBar
# import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import os
from Queue import Queue
from threading import Thread
import time
import sys
#============= local library imports  ==========================
from pychron.paths import paths
# from pychron.helpers.paths import LOVERA_PATH
from pychron.graph.diffusion_graph import DiffusionGraph  # , GROUPNAMES
from pychron.loggable import Loggable
from pychron.modeling.data_loader import DataLoader
from pychron.modeling.model_data_directory import ModelDataDirectory
from pychron.helpers.color_generators import colorname_generator, paired_colorname_generator
from pychron.modeling.fortran_process import FortranProcess
from pychron.graph.diffusion_graph import GROUPNAMES

class DummyDirectoryDialog(object):
    path = os.path.join(paths.modeling_data_dir, '59702-43')
    def open(self):
        return OK

class Modeler(Loggable):
    '''
    '''

    graph = Instance(DiffusionGraph)
    name = Str(enter_set=True, auto_set=False)

    datum = Property(Directory,
                     depends_on='_datum')  # (value=paths.modeling_data_dir)
    _datum = Directory
    data = List(ModelDataDirectory)

    selected = Any

    refresh = Button

    data_loader = Instance(DataLoader)
    graph_title = Property

    status_text = Str
    sync_groups = None

    panel1 = Str('spectrum')
    panel2 = Str('arrhenius')
    panel3 = Str('logr_ro')
    panel4 = Str('cooling_history')

    logr_ro_line_width = Int(1)
    arrhenius_plot_type = Enum('scatter', 'line', 'line_scatter')

    clovera_directory = Directory
    data_directory = Directory

    fortran_processes = List

    def _get_datum(self):
        if not self._datum:
            return self.data_directory
        else:
            return self._datum

    def _set_datum(self, d):
        self._datum = d

#===============================================================================
# fortran
#===============================================================================
    def parse_autoupdate(self):
        '''
        '''

        f = FileDialog(action='open',
#                       default_directory=paths.modeling_data_dir
                       default_directory=self.data_directory
                       )
        if f.open() == OK:
            self.info('loading autoupdate file {}'.format(f.path))

            # open a autoupdate config dialog
            from clovera_configs import AutoUpdateParseConfig
            adlg = AutoUpdateParseConfig('', '')
            info = adlg.edit_traits()
            if info.result:
                self.info('tempoffset = {} (C), timeoffset = {} (min)'.format(adlg.tempoffset, adlg.timeoffset))
                rids = self.data_loader.load_autoupdate(f.path, adlg.tempoffset, adlg.timeoffset)
                auto_files = True
                if auto_files:
                    for rid in rids:
                        root = f.path + '_data'
                        with open(os.path.join(root, rid, 'samples.lst'), 'w') as s:
                            s.write('{}'.format(rid))

                        self.execute_files(rid=rid, root=root,
                                           block=True)


        #=======================================================================
        # debug
        #=======================================================================
        # path='/Users/Ross/Pychrondata_beta/data/modeling/ShapFurnace.txt'
        # self.data_loader.load_autoupdate(path)

    def execute_files(self, rid=None, root=None, **kw):
        if rid is None:
            rid, root = self._get_rid_root()

        if rid is not None:
            from clovera_configs import FilesConfig
            # make a config obj
            f = FilesConfig(rid, root)

            # write config to ./files.cl
            f.dump()

            # change current working dir
            os.chdir(os.path.join(root, rid))

            # now ready to run fortran
            name = 'files_py'
#            if sys.platform != 'darwin':
#                name += '.exe'
            self._execute_fortran(name, **kw)

    def _get_rid_root(self):

        #=======================================================================
        # #debug

#        d = DummyDirectoryDialog()
#        =======================================================================

        d = DirectoryDialog(action='open',
                            default_path=self.data_directory
#                            default_path=paths.modeling_data_dir
                            )

        if d.open() == OK:
            rid = os.path.basename(d.path)
            root = os.path.dirname(d.path)

            # set this root as the working directory
            os.chdir(d.path)
            self.info('setting working directory to {}'.format(d.path))

            return rid, root
        return None, None

    def execute_autoarr(self):
        from clovera_configs import AutoarrConfig
        self._execute_fortran_helper('Autoarr', 'autoarr_py', AutoarrConfig)

    def execute_autoagemon(self):
        from clovera_configs import AutoagemonConfig
        self._execute_fortran_helper('Autoagemon', 'autoagemon_py', AutoagemonConfig)

    def execute_autoagefree(self):
        from clovera_configs import AutoagefreeConfig
        self._execute_fortran_helper('Autoagefree',
                                     'autoagefree_py',
                                      AutoagefreeConfig)

#    def execute_confidence_interval(self):
#        from clovera_configs import ConfidenceIntervalConfig
#        self._execute_fortan_helper('Confidence Interval', 'confint_py',
#                                    ConfidenceIntervalConfig)

    def execute_correlation(self):
        from clovera_configs import CorrelationConfig
        self._execute_fortran_helper('Correlation', 'corrfft_py', CorrelationConfig)

    def execute_arrme(self):
        from clovera_configs import ArrmeConfig
        self._execute_fortran_helper('Arrme', 'arrme_py', ArrmeConfig)

    def execute_agesme(self):
        from clovera_configs import AgesmeConfig
        self._execute_fortran_helper('Agesme', 'agesme_py', AgesmeConfig)

    def _execute_fortran_helper(self, name, fortan, config_klass):
        self.info('------- {} -------'.format(name))
        rid, root = self._get_rid_root()
        if rid:
            a = config_klass(rid, root)
            info = a.edit_traits()
            if info.result:
                self._execute_fortran(fortan)
            else:
                self.info('------- {} aborted-------'.format(name))

        else:
            self.info('------- {} aborted-------'.format(name))


    def _execute_fortran(self, name, block=False):
        if sys.platform != 'darwin':
            name += '.exe'
        self.info('excecute fortran program {}'.format(name))
        q = Queue()

        croot = self.clovera_directory

        if not croot:
            croot = paths.clovera_root

        rid = os.path.basename(os.getcwd())
        p = FortranProcess(name, croot, rid, q)
        self.fortran_processes.append(p)
        if len(self.fortran_processes) > 50:
            self.fortran_processes.pop(0)
        p.start()

        t = Thread(target=self._handle_stdout, args=(name, p, q))
        t.start()

        if block:
            t.join()

    def _handle_stdout(self, name, t, q):
        def _handle(msg):
            if msg:
                self.info(msg)

        st = time.time()
        # handle std.out
        while t.isAlive() or not q.empty():
            l = q.get().rstrip()
            _handle(l)
            time.sleep(0.001)

        # handle addition msgs
        for m in t.get_remaining_stdout():
            _handle(m)

        dur = time.time() - st
        self.info('{} run time {:e} s'.format(name, dur))

        if t.success:
            pstate = 'finished'
        else:
            pstate = 'failed'
        self.info('------ {} {} ------'.format(name.capitalize(), pstate))

        t.state = pstate

    #===========================================================================
    # graph
    #===========================================================================
    def get_panel_plotids(self, name):
        return [i for i, p in enumerate(self.get_panels()) \
                    if p == name]

    def get_panels(self):
        return [getattr(self, 'panel{}'.format(i + 1)) for i in range(4)]

    def refresh_graph(self):
        '''
        '''
        # before destroying the current graph we should sync with its values
        sync = False

        g = self.graph
        if g is None:
            panels = self.get_panels()
            l = len(panels)
            r = int(round(l / 2.0))
            c = 1
            if l > 2:
                c = 2

            g = DiffusionGraph(include_panels=panels,
                               container_dict=dict(
                                            type='h' if c == 1 else 'g',
                                            bgcolor='white',
                                            padding=[10, 10, 40, 10],

                                            # padding=[25, 5, 50, 30],
                                            # spacing=(5,5),
                                            # spacing=32 if c==1 else (32, 25),
                                            shape=(r, c)
                                            )

                               )

            self.graph = g
        else:
        # if g is not None:
            sync = True
            xlims = []
            ylims = []
            axis_params = []

            for i, p in enumerate(g.plots):
                xlims.append(g.get_x_limits(plotid=i))
                ylims.append(g.get_y_limits(plotid=i))

                pa = (p.x_axis.tick_label_font,
                     p.y_axis.tick_label_font,
                     p.x_axis.title_font,
                     p.y_axis.title_font,
                     )

                axis_params.append(pa)

            title = g._title
            title_font = g._title_font
            title_size = g._title_size

            bgcolor = g.plotcontainer.bgcolor
            graph_editor = g.graph_editor

            self.sync_groups = g.groups
            bindings = g.bindings

        # self.graph = g = DiffusionGraph()
        g.clear()
        g.new_graph()
        self._spec_cnt = 0
        self._chist_cnt = 0
        self._arr_cnt = 0
        self._logr_cnt = 0
        self._unchist_cnt = 0

        if sync:
            g.bindings = bindings

            g.set_title(title, font=title_font, size=title_size)

            g.plotcontainer.bgcolor = bgcolor

            for i, (xlim, ylim, axp) in enumerate(zip(xlims, ylims, axis_params)):
                plot = g.plots[i]
                plot.x_axis.tick_label_font = axp[0]
                plot.y_axis.tick_label_font = axp[1]
                plot.x_axis.title_font = axp[2]
                plot.y_axis.title_font = axp[3]

                # check to see limits are not inf or -inf
                if xlim[0] != float('-inf') and xlim[1] != float('inf'):
                    g.set_x_limits(min_=xlim[0], max_=xlim[1], plotid=i)
                    g.set_y_limits(min_=ylim[0], max_=ylim[1], plotid=i)

            # sync open editors
            if graph_editor is not None:
                graph_editor.graph = g

    def _load_graph(self, data_directory, gid, pcolor, scolor):

        data_directory.id = gid

        path = data_directory.path
        self.info('loading graph for {}'.format(path))
        g = self.graph

        runid = g.add_runid(path, kind='path')
        dl = self.data_loader
        dl.root = data_directory.path
        for i, pi in enumerate(self.get_panels()):
            func = getattr(self, '_load_{}'.format(pi))
            func(data_directory, i, runid, pcolor, scolor)


        self._sync_groups(data_directory)

    def _sync_groups(self, data_directory):
        g = self.graph
        g.set_group_visiblity(data_directory.show, gid=data_directory.id)
        # sync thecolors
#        try:

#            if self.sync_groups:
#                for si in self.sync_groups:
#                    try:
#                        tg = g.groups[si]
#                        sg = self.sync_groups[si]
#                    except KeyError, e:
#                        print __name__, e
#                        return
#
#                    for i, subgroup in enumerate(sg):
#                        for j, series in enumerate(subgroup):
#                            try:
#
#                                tseries = tg[i][j]
#                                if series.__class__.__name__ == 'PolygonPlot':
#                                    for a in ['face_color', 'edge_color']:
#                                        color = series.trait_get(a)
#                                        tseries.trait_set(**color)
#                                else:
#                                    tseries.trait_set(**{'color':series.color})
#
#                            except IndexError, e:
#                                print __name__, e

#        except Exception, e:
#            print 'sync groups', e
#============= views ===================================
#
    def traits_view(self):
        return self.data_select_view()

    def data_select_view(self):
        tree = Item('datum', style='custom', show_label=False, height=0.75,
                  width=0.25)

        cols = [
                ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='show'),
                CheckboxColumn(name='bind'),
#                ObjectColumn(name='primary_color',
# #                             editable=False,
#                             label='Pc',
# #                             style='simple'
#                             style='custom'
#                             ),
#                ObjectColumn(name='secondary_color', editable=False, label='Sc',
#                             style='custom',
#                             graph_color_='red'
# #                             style='simple'
#                             ),
                CheckboxColumn(name='model_spectrum_enabled', label='Ms'),
                CheckboxColumn(name='inverse_model_spectrum_enabled', label='IMs'),
                CheckboxColumn(name='model_arrhenius_enabled', label='Ma'),

              ]

        editor = TableEditor(columns=cols,
                             editable=True,
                             reorderable=True,
                             deletable=True,
                             show_toolbar=True,
                             selection_mode='rows',
                             selected='selected'
                             )
        selected = Item('data', show_label=False, height=0.25,
                      editor=editor,
                      width=0.25
                      )

        v = View(Item('refresh', show_label=False),
                 VSplit(selected,
                        tree))
        return v

    def graph_view(self):
        graph = Item('graph', show_label=False,
                    style='custom',
                    # width = 0.75
                    )
        v = View(graph)
        return v

    def configure_view(self):
        editor = EnumEditor(values=GROUPNAMES)
        a = Item(
                 'panel1', editor=editor,
                 show_label=False)
        b = Item(
                 'panel2', editor=editor,
                 show_label=False)
        c = Item(
                 'panel3', editor=editor,
                 show_label=False)
        d = Item(
                 'panel4', editor=editor,
                 show_label=False)

        v = View(VGroup(
                        HGroup(a, b),
                        HGroup(c, d)
                        ),
               kind='modal',
               buttons=['OK', 'Cancel'],
               title='Panel Layout'
               )

        return v


    def _datum_changed(self):
        '''
        '''

        d = self.datum
        # validate datum as proper directory
        if self.data_loader.validate_data_dir(d):

            # dont add if already in list
            for di in self.data:
                if di.path == d:
                    self.selected = d
                    return

            pid = len(self.data)
            d = ModelDataDirectory(path=d,
                                modeler=self,
                                show=True,  # if len(self.data) >= 1 else False,
                                bind=True,
                                model_spectrum_enabled=True,
                                inverse_model_spectrum_enabled=True,
                                model_arrhenius_enabled=True,
                                id=pid,
                                )

            self.graph.set_group_binding(pid, True)
            self.data.append(d)
            self.selected = d

    @on_trait_change('refresh,data[]')
    def _update_(self, a, b, c, d):
        '''
        '''
        self.refresh_graph()
        color_gen = paired_colorname_generator()
        for gid, d in enumerate(self.data):
            # need to load all graphs even if we are not going to show them
            # this is to ensure proper grouping
            # set visiblity after
#            c = color_gen.next()
#            d.primary_color = c
            pc, sc = color_gen.next()

            self._load_graph(d, gid, pc, sc)

            d.primary_color = pc
            d.secondary_color = sc


            # skip a color
#            color_gen.next()

        self.update_graph_title()
        # force update of notes and summary
        d = self.selected
        self.selected = None
        self.selected = d

#===============================================================================
# graph loaders
#===============================================================================
    def _try(self, func, data):
        if data is not None:
            try:
                func(data)
            except Exception, e:
                import traceback
                traceback.print_exc()
                self.info(e)

    def _load_arrhenius(self, data_directory, plotidcounter, runid,
                        pcolor, scolor):
        dl = self.data_loader
        g = self.graph

        def build(data):
            p = g.build_arrhenius(pid=plotidcounter,
                              color=pcolor,
                              type=self.arrhenius_plot_type, *data)
            data_directory.plots += p
            g.set_series_label('{}.arr.meas'.format(runid), plotid=plotidcounter, series=self._arr_cnt)
            self._arr_cnt += 1

        data = dl.load_arrhenius('arr.samp')
        self._try(build, data)

        if data_directory.model_arrhenius_enabled:
            def build(data):
                p = g.build_arrhenius(ngroup=False, pid=plotidcounter,
                                  type=self.arrhenius_plot_type,
                                  color=scolor,
                                  *data)
                data_directory.plots += p

                g.set_series_label('{}.arr.model'.format(runid), plotid=plotidcounter, series=self._arr_cnt)
                self._arr_cnt += 1
            data = dl.load_arrhenius('arr.dat')
            self._try(build, data)

    def _load_logr_ro(self, data_directory, plotidcounter, runid,
                      pcolor, scolor):
        dl = self.data_loader
        g = self.graph

        data = dl.load_logr_ro('logr.samp')  # Produced by Autoarr with dictated/automated arrhenius parameters
        data2 = dl.load_logr_ro('log.smp')  # Produced by running'files' during parsing of autoupdate
        if data is not None:
            def build(data):
                p = g.build_logr_ro(pid=plotidcounter, line_width=self.logr_ro_line_width,
                                    color=pcolor,
                                    *data)
                data_directory.plots += p

#                s = 2 if data_directory.model_arrhenius_enabled else 1
                g.set_series_label('{}.logr_ro.meas'.format(runid), plotid=plotidcounter, series=self._logr_cnt)
#                p.on_trait_change(data_directory.update_pcolor, 'color')
                self._logr_cnt += 1
            self._try(build, data)

        elif data2 is not None:
            def build(data):
                p = g.build_logr_ro(pid=plotidcounter, line_width=self.logr_ro_line_width,
                                    color=pcolor,
                                    *data)
                data_directory.plots += p

                g.set_series_label('{}.logr_ro.meas'.format(runid), plotid=plotidcounter, series=self._logr_cnt)
#                p.on_trait_change(data_directory.update_pcolor, 'color')
                self._logr_cnt += 1

            self._try(build, data2)

        if data_directory.model_arrhenius_enabled:

            def build(data):
                p = g.build_logr_ro(ngroup=False, line_width=self.logr_ro_line_width,
                                    pid=plotidcounter,
                                    color=scolor,
                                    *data)
                data_directory.plots += p

                g.set_series_label('{}.logr_ro.model'.format(runid), plotid=plotidcounter, series=self._logr_cnt)
                self._logr_cnt += 1
#                p.on_trait_change(data_directory.update_scolor, 'color')

            data = dl.load_logr_ro('logr.dat')
            self._try(build, data)

    def _load_unconstrained_thermal_history(self, data_directory, plotidcounter, runid, color):
        dl = self.data_loader
        g = self.graph
        def build(data):
            p = g.build_unconstrained_thermal_history(data, pid=plotidcounter,
                                                  series=self._unchist_cnt
                                                  )
            data_directory.plots += p

            self._unchist_cnt += 1
        data = dl.load_unconstrained_thermal_history()
        self._try(build, data)

    def _load_cooling_history(self, data_directory, plotidcounter, runid, pcolor, scolor):
        dl = self.data_loader
        g = self.graph
        def build(data):
            p = g.build_cooling_history(pid=plotidcounter, colors=[pcolor, scolor], *data)
            data_directory.plots += p

            g.set_series_label('{}.chist.l'.format(runid), plotid=plotidcounter, series=self._chist_cnt)
            g.set_series_label('{}.chist.h'.format(runid), plotid=plotidcounter, series=self._chist_cnt + 1)
            self._chist_cnt += 2

        data = dl.load_cooling_history()
        self._try(build, data)

    def _load_spectrum(self, data_directory, plotidcounter, runid, pcolor, scolor):
        dl = self.data_loader
        data = dl.load_spectrum()
        g = self.graph

        def build(data):
            ps = g.build_spectrum(color=pcolor,
                             pid=plotidcounter,
                             *data)
            data_directory.plots += ps

            g.set_series_label('{}.spec.meas-err'.format(runid),
                               plotid=plotidcounter,
                               series=self._spec_cnt
                               )
            g.set_series_label('{}.spec.meas'.format(runid),
                               plotid=plotidcounter,
                                series=self._spec_cnt + 1)
            self._spec_cnt += 2

        self._try(build, data)

        if data_directory.model_spectrum_enabled:
            def build(data):
                p = g.build_spectrum(*data,
                                     color=scolor,
                                     ngroup=False, pid=plotidcounter)
                data_directory.plots += p
                g.set_series_label('{}.model'.format(runid), plotid=plotidcounter
                                   )
#                g.color_generators[-1].next()
#                p.color = g.color_generators[-1].next()
                self._spec_cnt += 1

            data = dl.load_model_spectrum()

            self._try(build, data)

        if data_directory.inverse_model_spectrum_enabled:
            def build(data):
                color = g.color_generators[-1].next()
                for i, (ar39, age) in enumerate(zip(*data)):
                    g.build_spectrum(ar39, age,
                                         ngroup='inverse_model_spectrum',
                                         pid=plotidcounter,
                                         color=color
                                         )
                    g.set_series_label('{}.inverse_spec.{}'.format(runid, i),
                                       plotid=plotidcounter,
#                                       series=self._spec_cnt
                                       )
                    self._spec_cnt += 1

            data = dl.load_inverse_model_spectrum()
            self._try(build, data)

    @on_trait_change('graph.status_text')
    def update_statusbar(self, obj, name, value):
        '''
        '''
        if name == 'status_text':
            self.status_text = value

    def _get_graph_title(self):
        '''
        '''
        return ', '.join([a.name for a in self.data if a.show])

    def update_graph_title(self):
        '''
        '''
        self.graph.set_title(self.graph_title, size=18)
    def _data_loader_default(self):
        return DataLoader()
def runfortran():
    q = Queue()
    t = FortranProcess('hello_world', '/Users/Ross/Desktop', q)
    t.start()

    while t.isAlive() or not q.empty():
        l = q.get().rstrip()

        print l

    print t.get_remaining_stdout()


if __name__ == '__main__':
    runfortran()
#    r = RunConfiguration()
#    r.configure_traits()
#============= EOF ====================================
#    setup('modeler')
#    m = Modeler()
#    m.refresh_graph()
#
#    m.configure_traits()
#    def traits_view(self):
#        '''
#        '''
#        namegrp = HGroup(Item('name', show_label = False), spring)
#
#        v = View(HSplit(VSplit(selected,
#                             tree
#                             ),
#                      graph),
#                    width = 800,
#                    height = 600,
#                    menubar = self._get_menubar(),
#                    statusbar = 'status_text',
#                    resizable = True,
#
#                    )
#
#        return v

# def run_model(self):
#        '''
#        '''
#
#        model_thread = Thread(target=self._run_model_)
#        model_thread.start()
#
#    def _run_model_(self, run_config=None):
#        '''
#
#        '''
# #        src_dir = os.path.join(data_dir, 'TESTDATA')
#        self.info('Running Model')
#        if run_config is None:
#            run_config = self.run_configuration
#
#        if run_config is None:
#            self.warning('no run configuration')
#        else:
#            self.info('Model Options')
#            for a in ['sample', 'geometry', 'max_domains', 'min_domains', 'nruns', 'max_plateau_age']:
#                self.info('{} = {}'.format(a, getattr(run_config, a)))
#
#            #dump the individual config files
#            error = self.run_configuration.write()
#            if error:
#                self.warning('Failed writing config file')
#                self.warning('error = {}'.format(error))
#                return
#
#            if os.path.exists(LOVERA_PATH):
#                #check to see dir has necessary programs
#                if any([not ni in os.listdir(LOVERA_PATH) for ni in  NECESSARY_PROGRAMS]):
#                    self.warning('Incomplete LOVERA_PATH {}'.format(LOVERA_PATH))
#                    return
#
#                src_dir = os.path.join(self.run_configuration.data_dir)
#
#                self.info('copying fortran programs')
#                #copy the lovera codes to src_dir
#                for f in NECESSARY_PROGRAMS:
#                    p = os.path.join(LOVERA_PATH, f)
#                    self.info('copying {} > {}'.format(p, src_dir))
#                    shutil.copy(p, src_dir)
#
#                self.info('change to directory {}'.format(src_dir))
#                #change the working directory
#                os.chdir(src_dir)
#
#            else:
#                self.warning('Invalid LOVERA_PATH {}'.format(LOVERA_PATH))
#                return
#
#            #run the lovera code
#            for cmd in ['filesmod', 'autoarr', 'autoagemon']:
#                msg = 'execute {}'.format(cmd)
#                self.status_test = msg
#                self.info(msg)
#                if sys.platform == 'win32':
#                    os.system(cmd)
#                else:
#                    status, output = commands.getstatusoutput('./{}'.format(cmd))
#                    self.info('{} {}' % (status, output))
#                    if status:
#                        break
#
#            #delete the copied programs
#
#            for f in NECESSARY_PROGRAMS:
#                os.remove(os.path.join(src_dir, f))
#
#            self.info('====== Modeling finished======')
#            self.status_text = 'modeling finished'
# def open_run_configuration(self):
#        def edit_config(*args):
#            if args:
#                m = args[0]
#            else:
#                m = RunConfiguration()
#
#            info = m.edit_traits(kind='modal')
#            if info.result:
#                with open(p, 'w') as f:
#                    pickle.dump(m, f)
#
#                return m
#
#        p = os.path.join(hidden_dir, '.run_config')
#        if os.path.isfile(p):
#            with open(p, 'rb') as f:
#                try:
#                    r = edit_config(pickle.load(f))
#                    if r is not None:
#                        self.run_configuration = r
#
#                except:
#                    r = edit_config()
#                    if r is not None:
#                        self.run_configuration = r
#        else:
#            r = edit_config()
#            if r is not None:
#                self.run_configuration = r
# class RunConfiguration(HasTraits):
#    '''
#    '''
#    data_dir = Directory('~/Pychrondata_beta/data/modeling')
#    sample = Str('59702-52')
#    geometry = Enum('plane', 'sphere', 'cylinder')
#    max_domains = Int(8)
#    min_domains = Int(3)
#    nruns = Int(50)
#    max_plateau_age = Float(375)
#    def write(self):
#        error = None
#        def _write_attrs(p, names):
#            with open(p, 'w') as f:
#                for n in names:
#                    f.write('#%s\n' % n)
#                    f.write('%s\n' % getattr(self, n))
#
#        if os.path.isdir(self.data_dir):
#            #write files mod config
#            p = os.path.join(self.data_dir, 'files_mod_config.in')
#            _write_attrs(p, ['sample'])
#
#            #write autoarr config
#            p = os.path.join(self.data_dir, 'autoarr_config.in')
#            _write_attrs(p, ['max_domains', 'min_domains'])
#
#            #write autoage-mon config
#            p = os.path.join(self.data_dir, 'autoage_mon_config.in')
#            _write_attrs(p, ['nruns', 'max_plateau_age'])
#        else:
#            error = 'Invalid data directory %s' % self.data_dir
#        return error

#    def traits_view(self):
#        '''
#        '''
#        files_mod_group = VGroup(Item('sample'),
#                               Item('geometry'),
#                               label='files_mod')
#        autoarr_group = VGroup(Item('max_domains'),
#                             Item('min_domains'),
#                             label='autoarr')
#        autoage_mon_group = VGroup(Item('nruns'),
#                                 Item('max_plateau_age'),
#                                 label='autoage-mon'
#                                 )
#        return View(
#                       Item('data_dir'),
#                       Group(
#                             files_mod_group,
#                             autoarr_group,
#                             autoage_mon_group,
#                             layout='tabbed'
#                            ),
#                    buttons=['OK', 'Cancel'],
#                    resizable=True,
#                    kind='modal',
#                    width=500,
#                    height=150
#                    )
