# ===============================================================================
# Copyright 2013 Jake Ross
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
from datetime import datetime
import time

from traits.api import Instance, List, on_trait_change, Bool
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem, Tabbed, VSplitter



# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.dashboard.client import DashboardClient
from pychron.envisage.tasks.pane_helpers import ConsolePane
from pychron.experiment.utilities.identifier import ANALYSIS_MAPPING, SPECIAL_MAPPING
from pychron.globals import globalv
from pychron.processing.tasks.analysis_edit.panes import ControlsPane
from pychron.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane
from pychron.processing.tasks.figures.figure_editor import FigureEditor
from pychron.processing.tasks.figures.figure_task import FigureTask
from pychron.processing.tasks.figures.panes import PlotterOptionsPane
from pychron.system_monitor.tasks.actions import AddSystemMonitorAction, ClearFigureAction, PauseAction, PlayAction, \
    NewSeriesAction
from pychron.system_monitor.tasks.connection_spec import ConnectionSpec
from pychron.system_monitor.tasks.dashboard_editor import DashboardEditor
from pychron.system_monitor.tasks.panes import ConnectionPane, AnalysisPane, DashboardPane
from pychron.system_monitor.tasks.system_monitor_editor import SystemMonitorEditor

from traitsui.api import View, Item, EnumEditor
from pychron.core.ui.preference_binding import bind_preference


class SystemMonitorTask(FigureTask):
    name = 'System Monitor'

    tool_bars = [SToolBar(AddSystemMonitorAction(),
                          NewSeriesAction(),
                          PauseAction(),
                          PlayAction()),
                 SToolBar(ClearFigureAction())]

    connection_pane = Instance(ConnectionPane)
    controls_pane = Instance(ControlsPane)
    unknowns_pane = Instance(AnalysisPane)
    console_pane = Instance(ConsolePane)

    connections = List
    connection = Instance(ConnectionSpec)

    dashboard_client = Instance(DashboardClient)
    dashboard_editor = Instance(DashboardEditor)
    dashboard_pane = Instance(DashboardPane)
    last_activated = 0

    _paused = Bool(False)
    pause_visible = Bool(True)
    play_visible = Bool(False)

    def activated(self):
        self._setup_dashboard()
        self._make_connections()

    def activate_editor(self, editor):
        if not self.last_activated or time.time() - self.last_activated > 15:
            super(SystemMonitorTask, self).activate_editor(editor)
            self.last_activated = 0

    def prepare_destroy(self):
        for e in self.editor_area.editors:
            if isinstance(e, SystemMonitorEditor):
                e.stop()
        if self.dashboard_client:
            self.dashboard_client.on_trait_change(self._handle_dashboard, 'values:value', remove=True)

        super(FigureTask, self).prepare_destroy()

    def toggle_pause(self):
        self._paused = not self._paused
        self.play_visible = not self.play_visible
        self.pause_visible = not self.pause_visible

        for ei in self.editor_area.editors:
            if self._paused:
                ei.oname = ei.name
                ei.name = '{} (Paused)'.format(ei.name)
            else:
                ei.name = ei.oname

            if isinstance(ei, SystemMonitorEditor):
                ei.pause()

    def reset_editors(self):
        for ei in self.editor_area.editors:
            if isinstance(ei, SystemMonitorEditor):
                ei.reset_editors()

    def clear_figure(self):
        ac = self.has_active_editor()
        if ac:
            ac.set_items([])

    def new_analysis_series(self):
        from pychron.system_monitor.tasks.series_search_criteria import SearchCriteria


        kw = {'mass_spectrometer': self.connection.system_name,
              'mass_spectrometers': [ci.system_name for ci in self.connections],
              'analysis_type': 'Air',
              'analysis_types': ANALYSIS_MAPPING.values()}

        if self.active_editor and hasattr(self.active_editor, 'search_tool'):
            for attr in ('weeks', 'hours', 'limit', 'days'):
                kw[attr] = getattr(self.active_editor.search_tool, attr)

        sc = SearchCriteria(**kw)
        while 1:
            info = sc.edit_traits()
            if not info.result:
                break

            at = next((k for k, v in ANALYSIS_MAPPING.iteritems() if v == sc.analysis_type))
            at = next((k for k, v in SPECIAL_MAPPING.iteritems() if v == at))

            ans = self.manager.analysis_series(sc.mass_spectrometer,
                                               analysis_type=at,
                                               weeks=sc.weeks,
                                               days=sc.days,
                                               hours=sc.hours,
                                               limit=sc.limit)
            if ans:
                self.new_series(ans)
                break
            else:
                if not self.confirmation_dialog('No analyses found given the provided search criteria. Try Again?'):
                    break

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

    # private
    def _setup_dashboard(self):
        self.dashboard_client = client = self.application.get_service('pychron.dashboard.client.DashboardClient')
        if client:
            client.on_trait_change(self._handle_dashboard, 'values:value')
            bind_preference(client, 'host', 'pychron.dashboard.client.host')
            bind_preference(client, 'port', 'pychron.dashboard.client.port')

            client.connect()
            client.load_configuration()
            client.listen()

    def _refresh_plot_hook(self):
        self.last_activated = time.time()

    def _open_editor(self, editor, **kw):
        super(SystemMonitorTask, self)._open_editor(editor, **kw)
        tol = 3600
        for ei in self.editor_area.editors:
            if hasattr(ei, 'starttime'):
                dev = (datetime.now() - ei.starttime).total_seconds()
                self.debug('check editor duration. close after {}s. current dur:{}'.format(tol, dev))
                if dev > tol:
                    self.close_editor(ei)
                    # for si in self.get_editors(SystemMonitorEditor):
                    # si.close_editor(ei)

    def _editor_factory(self):
        if globalv.system_monitor_debug:
            self.connection = self.connections[0]
            result = True
        else:
            # ask user for system
            info = self.edit_traits(view='get_connection_view')
            result = info.result

        if result and self.connection:
            editor = SystemMonitorEditor(processor=self.manager,
                                         conn_spec=self.connection,
                                         task=self)
            editor.start()
            self._open_editor(editor)

            return editor

    def _dashboard_editor_factory(self, names):
        editor = DashboardEditor(processor=self.manager)
        editor.set_measurements(names)
        self._open_editor(editor)
        self.dashboard_editor = editor
        return editor

    def _active_editor_changed(self, new):
        if new:

            self.last_activated = time.time()

            if self.controls_pane:
                tool = None
                # if hasattr(new, 'tool'):
                # tool = new.tool

                if hasattr(new, 'search_tool'):
                    tool = new.search_tool

                self.controls_pane.tool = tool
            if isinstance(new, FigureEditor):
                self.plotter_options_pane.pom = new.plotter_options_manager
            if isinstance(new, SystemMonitorEditor):
                self.console_pane.name = '{} - Console'.format(new.name)
                self.console_pane.console_display = new.console_display
                self.connection_pane.conn_spec = new.conn_spec

            if self.unknowns_pane:
                if hasattr(new, 'analyses'):
                    with no_update(self.unknowns_pane, fire_update_needed=False):
                        self.unknowns_pane.trait_set(items=new.analyses)

    def _prompt_for_save(self):
        """
            dont save just close
        """
        return True

    def _make_connections(self):
        app = self.window.application
        connections = app.preferences.get('pychron.sys_mon.favorites')
        if not connections:
            self.warning_dialog('No Systems in Preferences')
            return

        cs = []
        for ci in eval(connections):
            n, sn, h, p = ci.split(',')
            cc = ConnectionSpec(system_name=sn,
                                host=h, port=int(p))
            cs.append(cc)
        self.connections = cs

    def create_dock_panes(self):
        self.connection_pane = ConnectionPane()
        self.controls_pane = ControlsPane()
        self.unknowns_pane = AnalysisPane()
        self.plotter_options_pane = PlotterOptionsPane()
        self.plot_editor_pane = PlotEditorPane()

        self.console_pane = ConsolePane()

        panes = [self.connection_pane,
                 self.controls_pane,
                 self.unknowns_pane,
                 self.plotter_options_pane,
                 self.console_pane,
                 self.plot_editor_pane]

        if self.dashboard_client:
            self.dashboard_pane = DashboardPane(model=self.dashboard_client)
            panes.append(self.dashboard_pane)

        return panes

    @on_trait_change('window:opened')
    def _opened(self):
        self.add_system_monitor()

    # # self.add_dashboard_editor()

    def _handle_dashboard(self, obj, name, old, new):
        self.debug('dashboard_client value change {} {}'.format(obj.name, new))
        if self.dashboard_editor:
            self.dashboard_editor.update_measurements(obj.name, new)

    def _default_layout_default(self):
        left = VSplitter(PaneItem('pychron.sys_mon.analyses'),
                         PaneItem('pychron.processing.controls'))
        right = Tabbed(PaneItem('pychron.processing.figures.plotter_options'),
                       PaneItem('pychron.console'))

        return TaskLayout(left=left, right=right)


# ============= EOF =============================================
