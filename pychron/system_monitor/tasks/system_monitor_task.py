#===============================================================================
# Copyright 2013 Jake Ross
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
from PySide.QtCore import Qt
from pyface.timer.do_later import do_later
from traits.api import Instance, List, on_trait_change
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, Splitter, PaneItem, Tabbed, VSplitter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.dashboard.tasks.client.client import DashboardClient
from pychron.envisage.tasks.pane_helpers import ConsolePane
from pychron.processing.tasks.analysis_edit.panes import ControlsPane
from pychron.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane
from pychron.processing.tasks.figures.figure_editor import FigureEditor
from pychron.processing.tasks.figures.figure_task import FigureTask
from pychron.processing.tasks.figures.panes import PlotterOptionsPane
from pychron.system_monitor.tasks.actions import AddSystemMonitorAction
from pychron.system_monitor.tasks.connection_spec import ConnectionSpec
from pychron.system_monitor.tasks.dashboard_editor import DashboardEditor
from pychron.system_monitor.tasks.panes import ConnectionPane, AnalysisPane, DashboardPane
from pychron.system_monitor.tasks.system_monitor_editor import SystemMonitorEditor

from traitsui.api import View, Item, EnumEditor
from pychron.ui.preference_binding import bind_preference


class SystemMonitorTask(FigureTask):
    name = 'System Monitor'

    tool_bars = [SToolBar(AddSystemMonitorAction(),
                          image_size=(16, 16)),
                 SToolBar(
                     image_size=(16, 16))]

    connection_pane = Instance(ConnectionPane)
    controls_pane = Instance(ControlsPane)
    unknowns_pane = Instance(AnalysisPane)
    console_pane = Instance(ConsolePane)

    connections = List
    connection = Instance(ConnectionSpec)

    dashboard_client = Instance(DashboardClient, ())
    dashboard_editor = Instance(DashboardEditor)

    def prepare_destroy(self):
        for e in self.editor_area.editors:
            if isinstance(e, SystemMonitorEditor):
                e.stop()

        super(FigureTask,self).prepare_destroy()

    def add_system_monitor(self):
        return self._editor_factory()

    def add_dashboard_editor(self):
        names = [v.name for v in self.dashboard_client.values]
        return self._dashboard_editor_factory(names)

    def get_connection_view(self):
        v = View(Item('connection',
                      editor=EnumEditor(name='connections')),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 width=300,
                 title='Choose System')
        return v

    def tab_editors(self, *args):
        def func(control, a, b):
            control.tabifyDockWidget(a, b)

        self._layout_editors(func, *args)

    def split_editors(self, a, b, orientation='h'):

        def func(control, aa, bb):
            print aa, bb
            control.splitDockWidget(aa, bb, Qt.Horizontal if orientation == 'h' else Qt.Vertical)

        self._layout_editors(func, a, b)

    def _layout_editors(self, func, aidx, bidx):
        ea = self.editor_area
        control = ea.control
        widgets = control.get_dock_widgets()
        if widgets:
            try:
                a, b = widgets[aidx], widgets[bidx]
                func(control, a, b)
            except IndexError:
                pass

    def _editor_factory(self):
        self.connection = self.connections[0]
        #ask user for system
        #info = self.edit_traits(view='get_connection_view')
        if 1:
        #if info.result and self.connection:
            editor = SystemMonitorEditor(processor=self.manager,
                                         conn_spec=self.connection,
                                         task=self)
            editor.start()
            self._open_editor(editor)
            #if editor:
            #    do_later(editor.run_added_handler)

            return editor

    def _dashboard_editor_factory(self, names):
        editor = DashboardEditor()
        editor.set_measurements(names)
        self._open_editor(editor)
        self.dashboard_editor = editor
        #self.tab_editors(0,1)
        #do_after(1000, self.tab_editors,1,2)
        return editor

    def _active_editor_changed(self):
        if self.active_editor:
            if self.controls_pane:
                tool = None
                if hasattr(self.active_editor, 'tool'):
                    tool = self.active_editor.tool

                self.controls_pane.tool = tool
            if isinstance(self.active_editor, FigureEditor):
                self.plotter_options_pane.pom = self.active_editor.plotter_options_manager
            if isinstance(self.active_editor, SystemMonitorEditor):
                self.console_pane.name = '{} - Console'.format(self.active_editor.name)
                self.console_pane.console_display = self.active_editor.console_display
                self.connection_pane.conn_spec = self.active_editor.conn_spec

            if self.unknowns_pane:
                if hasattr(self.active_editor, 'unknowns'):
                    #print self.active_editor, len(self.active_editor.unknowns)
                    #self.unknowns_pane._no_update=True
                    self.unknowns_pane.items = self.active_editor.unknowns
                    #self.unknowns_pane._no_update=False

    def _prompt_for_save(self):
        """
            dont save just close
        """
        return True

    def _make_connections(self):
        app = self.window.application
        connections = app.preferences.get('pychron.sys_mon.favorites')
        cs = []
        for ci in eval(connections):
            n, sn, h, p = ci.split(',')
            cc = ConnectionSpec(system_name=sn,
                                host=h, port=int(p))
            cs.append(cc)
        self.connections = cs

    def activated(self):
        self._make_connections()
        #editor = self.add_system_monitor()
        self._setup_dashboard_client()

        #if editor:
        #    ideo = self.new_ideogram(add_table=False, add_iso=False)
        #    editor._ideogram_editor = ideo
        #    #self.active_editor.unknowns=[]
        #    self.activate_editor(self.editor_area.editors[0])

    @on_trait_change('window:opened')
    def _opened(self):
        editor = self.add_system_monitor()
        self.add_dashboard_editor()

        #if editor:
        #    ideo = self.new_ideogram(add_table=False, add_iso=False)
        #    editor._ideogram_editor = ideo
        #self.active_editor.unknowns=[]
        #self.split_editors(0, 1, orientation='v')
        #self.activate_editor(self.editor_area.editors[0])

    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                Splitter(
                    PaneItem('pychron.sys_mon.connection'),
                    PaneItem('pychron.analysis_edit.controls'),
                    orientation='vertical'),
                PaneItem('pychron.sys_mon.analyses'),
                orientation='horizontal'),
            right=VSplitter(Tabbed(PaneItem('pychron.console'),
                                   PaneItem('pychron.plot_editor')),
                            PaneItem('pychron.dashboard.client')))

    def create_dock_panes(self):
        self.connection_pane = ConnectionPane()
        self.controls_pane = ControlsPane()
        self.unknowns_pane = AnalysisPane()
        self.plotter_options_pane = PlotterOptionsPane()
        self.plot_editor_pane = PlotEditorPane()

        self.console_pane = ConsolePane()

        self.dashboard_pane = DashboardPane(model=self.dashboard_client)

        return [self.connection_pane,
                self.controls_pane,
                self.unknowns_pane,
                self.plotter_options_pane,
                self.console_pane,
                self.plot_editor_pane,
                self.dashboard_pane]

    def _setup_dashboard_client(self):
        client = self.dashboard_client
        bind_preference(client, 'host', 'pychron.dashboard.host')
        bind_preference(client, 'port', 'pychron.dashboard.port')

        client.connect()
        client.load_configuration()
        client.listen()

    @on_trait_change('dashboard_client:values:value')
    def _value_changed(self, obj, name, old, new):
        self.debug('dashboard_client value change {} {}'.format(obj.name, new))
        if self.dashboard_editor:
            self.dashboard_editor.update_measurements(obj.name, new)

#============= EOF =============================================
