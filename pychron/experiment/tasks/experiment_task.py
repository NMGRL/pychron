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
from traits.api import on_trait_change, Bool, Instance, Event, Color
# from traitsui.api import View, Item
from pyface.tasks.task_layout import PaneItem, TaskLayout, Splitter, Tabbed
from pyface.constant import CANCEL, NO
#============= standard library imports ========================
import shutil
import weakref
import os
#============= local library imports  ==========================
import xlrd
from pychron.core.ui.preference_binding import bind_preference, color_bind_preference
from pychron.envisage.tasks.pane_helpers import ConsolePane
from pychron.experiment.queue.base_queue import extract_meta
from pychron.experiment.tasks.experiment_panes import ExperimentFactoryPane, StatsPane, \
    ControlsPane, WaitPane, IsotopeEvolutionPane, ConnectionStatusPane

from pychron.envisage.tasks.editor_task import EditorTask
from pychron.experiment.tasks.experiment_editor import ExperimentEditor, UVExperimentEditor
from pychron.experiment.utilities.identifier import convert_extract_device
from pychron.image.tasks.video_pane import VideoDockPane
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.paths import paths
from pychron.core.helpers.filetools import add_extension, unique_date_path
from pychron.messaging.notify.notifier import Notifier
from pychron.lasers.pattern.pattern_maker_view import PatternMakerView


class ExperimentEditorTask(EditorTask):
    wildcard = '*.txt'
    group_count = 0
    name = 'Experiment'

    use_notifications = Bool
    use_syslogger = Bool
    #notifications_port = Int

    loading_manager = Instance('pychron.loading.loading_manager.LoadingManager')
    notifier = Instance(Notifier, ())
    syslogger = Instance('pychron.experiment.sys_log.SysLogger')

    # analysis_health = Instance(AnalysisHealth)
    last_experiment_changed = Event

    bgcolor=Color
    def new_pattern(self):
        pm = PatternMakerView()
        self.window.application.open_view(pm)

    def open_pattern(self):
        pm = PatternMakerView()
        if pm.load_pattern():
            self.window.application.open_view(pm)

    def send_test_notification(self):
        self.debug('sending test notification')
        db = self.manager.db
        #         an=db.get_last_analysis('bu-FD-o')
        an = db.get_last_analysis('ba-01-o')
        an = self.manager.make_analysis(an)
        if an:
            self.debug('test push {}'.format(an.record_id))
            self._publish_notification(an)
        else:
            self.debug('problem recalling last analysis')

    def deselect(self):
        if self.active_editor:
            self.active_editor.queue.selected = []
            self.active_editor.queue.executed_selected = []

    def undo(self):
        if self.has_active_editor():
            self.manager.experiment_factory.undo()

    def edit_default_conditions(self):
        if self.has_active_editor():
            from pychron.experiment.conditions_edit_view import edit_conditions
            edit_conditions(self.manager.queue_factory.default_conditions_name,
                            app=self.application)

    def prepare_destroy(self):
        super(ExperimentEditorTask, self).prepare_destroy()

        self.manager.experiment_factory.destroy()

        if self.use_notifications:
            self.notifier.close()

    def activated(self):

        #notifications
        bind_preference(self, 'use_notifications',
                        'pychron.experiment.use_notifications')
        bind_preference(self.notifier, 'port',
                        'pychron.experiment.notifications_port')
        #force notifier setup
        if self.use_notifications:
            self.notifier.setup(self.notifier.port)

            #sys logger
        bind_preference(self, 'use_syslogger',
                        'pychron.use_syslogger')
        if self.use_syslogger:
            self._use_syslogger_changed()

        color_bind_preference(self, 'bgcolor', 'pychron.experiment.bg_color')

        super(ExperimentEditorTask, self).activated()

    def _use_syslogger_changed(self):
        if self.use_syslogger:
            from pychron.experiment.sys_log import SysLogger

            self.syslogger = SysLogger()
            bind_preference(self.syslogger, 'username',
                            'pychron.syslogger.username')
            bind_preference(self.syslogger, 'password',
                            'pychron.syslogger.password')
            bind_preference(self.syslogger, 'host',
                            'pychron.syslogger.host')

    def create_dock_panes(self):
        self.isotope_evolution_pane = IsotopeEvolutionPane()

        self.experiment_factory_pane = ExperimentFactoryPane(model=self.manager.experiment_factory)
        self.wait_pane = WaitPane(model=self.manager.executor)

        panes = [StatsPane(model=self.manager),
                 ControlsPane(model=self.manager.executor),
                 ConsolePane(model=self.manager.executor),
                 #AnalysisHealthPane(model=self.analysis_health),
                 ConnectionStatusPane(model=self.manager.executor),
                 self.experiment_factory_pane,
                 self.isotope_evolution_pane,
                 self.wait_pane]

        if self.loading_manager:
            self.load_pane = self.window.application.get_service('pychron.loading.panes.LoadDockPane')
            self.load_table_pane = self.window.application.get_service('pychron.loading.panes.LoadTablePane')
            self.load_table_pane.model = self.loading_manager

            panes.extend([self.load_pane,
                          self.load_table_pane])

        panes = self._add_canvas_pane(panes)

        app = self.window.application
        man = app.get_service(ILaserManager)
        if man:
            if hasattr(man.stage_manager, 'video'):
                #vt = VideoTask()
                #             plugin = app.get_plugin('pychron.video')
                #             task = plugin.tasks[0].factory()
                #             self.window.add_task(task)

                video = man.stage_manager.video
                man.initialize_video()
                pane = VideoDockPane(video=video)
                #pane = vt.new_video_dock_pane(video=video)
                panes.append(pane)

            from pychron.lasers.tasks.laser_panes import ClientDockPane

            lc = ClientDockPane(model=man)
            self.laser_control_client_pane = lc
            panes.append(lc)

        return panes

    #===============================================================================
    # generic actions
    #===============================================================================
    def _open_experiment(self, path, **kw):

        if path.endswith('.xls'):
            txt, is_uv = self._open_xls(path)
        else:
            txt, is_uv = self._open_txt(path)

        klass = UVExperimentEditor if is_uv else ExperimentEditor
        editor = klass(path=path, bgcolor=self.bgcolor)
        editor.new_queue(txt)
        self._open_editor(editor)

        # loading queue editor set dirty
        # clear dirty flag
        editor.dirty = False

        self._show_pane(self.experiment_factory_pane)

    def _open_xls(self, path):
        """
            open the workbook and convert it to text
            construct the text to mimic a normal experiment file
        """
        wb = xlrd.open_workbook(path)
        sh = wb.sheet_by_index(0)
        #write meta
        meta_rows = 7
        rows = []
        is_uv = False
        for r in range(meta_rows):
            attr = sh.cell_value(r, 0)
            v = sh.cell_value(r, 1)
            if attr == 'extract_device':
                is_uv = v == 'Fusions UV'

            rows.append('{}: {}'.format(attr,
                                        v))
        rows.append('#{}'.format('=' * 80))

        header = sh.row_values(meta_rows)
        rows.append('\t'.join(header))
        for r in range(meta_rows + 2, sh.nrows):
            t = '\t'.join(map(str, sh.row_values(r)))
            rows.append(t)

        txt = '\n'.join(map(str, rows))
        return txt, is_uv

    def _open_txt(self, path):
        with open(path, 'r') as fp:
            txt = fp.read()

            f = (l for l in txt.split('\n'))
            meta, metastr = extract_meta(f)
            is_uv = False
            if meta.has_key('extract_device'):
                is_uv = meta['extract_device'] in ('Fusions UV', )

        return txt, is_uv

    def _set_last_experiment(self, p):
        with open(paths.last_experiment, 'w') as fp:
            fp.write(p)
        self.last_experiment_changed = True

    def open(self, path=None):
        self.manager.experiment_factory.activate(load_persistence=False)
        #path = '/Users/ross/Pychrondata_dev/experiments/uv.xls'
        #        path = '/Users/ross/Pychrondata_dev/experiments/uv.txt'
        if not os.path.isfile(path):
            path = None

        if path is None:
            ps = self.open_file_dialog(action='open files',
                                       #default_path='/Users/ross/Pychrondata_dev/experiments/Current Experiment.txt',
                                       default_filename='Current Experiment.txt')
        else:
            ps = (path,)

        if ps:
            manager = self.manager
            if manager.verify_database_connection(inform=True):
                if manager.load():
                    for path in ps:
                        self.manager.info('Opening experiment {}'.format(path))
                        self._open_experiment(path)

                    manager.path = path
                    manager.executor.reset()
                    manager.update_info()

                    #                     manager.update_queues()
                    #                    manager.start_file_listener(path)

            # do_later(self._show_pane,self.experiment_factory_pane)

            return True
        else:
            self.notifier.close()

    #def _split_text(self, txt):
    #    ts = []
    #    tis = []
    #    a = ''
    #    for l in txt.split('\n'):
    #        a += l
    #        if l.startswith('*' * 80):
    #            ts.append(''.join(tis))
    #            tis = []
    #            continue
    #
    #        tis.append(l)
    #    ts.append('\n'.join(tis))
    #    return ts

    def reset_queues(self):
        for editor in self.editor_area.editors:
            editor.queue.reset()

        # reset the experimentors db session
        # since the executor session will have made changes
        man = self.manager
        ex = man.executor
        man.update_info()
        man.stats.reset()

        ex.end_at_run_completion = False
        ex.set_extract_state('')

    def new(self):

        # ms = self.manager.experiment_factory.queue_factory.mass_spectrometer
        self.manager.experiment_factory.activate(load_persistence=True)

        editor = ExperimentEditor()
        editor.new_queue()#mass_spectrometer=ms)

        self._open_editor(editor)
        # self._show_pane(self.experiment_factory_pane)

        if not self.manager.executor.isAlive():
            self.manager.executor.executable = False

    def _save_file(self, path):
        if self.active_editor.save(path):
            self.manager.refresh_executable()
            self.debug('queues saved')
            self.manager.reset_run_generator()
            return True

    def _active_editor_changed(self):
        if self.active_editor:
            self.manager.experiment_queue = self.active_editor.queue
            self._show_pane(self.experiment_factory_pane)

    def _publish_notification(self, run):
        if self.use_notifications:
            #msg = 'RunAdded {}'.format(run.uuid)
            #self.info('pushing notification {}'.format(msg))
            self.notifier.send_notification(run.uuid)

    #===============================================================================
    # handlers
    #===============================================================================
    @on_trait_change('manager:executor:auto_save_event')
    def _auto_save(self):
        self.save()

    @on_trait_change('source_pane:[selected_connection, source:+]')
    def _update_source(self, name, new):
        from pychron.image.video_source import parse_url

        if name == 'selected_connection':
            islocal, r = parse_url(new)
            if islocal:
                pass
            else:
                self.source_pane.source.host = r[0]
                self.source_pane.source.port = r[1]
        else:
            url = self.source_pane.source.url()

            self.video_source.set_url(url)

    @on_trait_change('loading_manager:group_positions')
    def _update_group_positions(self, new):
        if not new:
            ef = self.manager.experiment_factory
            rf = ef.run_factory
            rf.position = ''
        else:
            pos = self.loading_manager.selected_positions
            self._update_selected_positions(pos)

    @on_trait_change('loading_manager:selected_positions')
    def _update_selected_positions(self, new):
        ef = self.manager.experiment_factory
        ef.selected_positions = new
        if new:
            rf = ef.run_factory

            nn = new[0]

            rf.selected_irradiation = nn.irradiation
            rf.selected_level = nn.level
            rf.labnumber = nn.labnumber

            # filter rows that dont match the first rows labnumber
            ns = [str(ni.positions[0]) for ni in new
                  if ni.labnumber == nn.labnumber]

            group_positions = self.loading_manager.group_positions
            #             group_positions = False
            if group_positions:
                rf.position = ','.join(ns)

    @on_trait_change('manager.experiment_factory:extract_device')
    def _handle_extract_device(self, new):
        app = self.window.application
        if new:
            ed = convert_extract_device(new)
            man = app.get_service(ILaserManager, 'name=="{}"'.format(ed))
            if man:
                self.laser_control_client_pane.model = man

        if new == 'Fusions UV':
            if self.active_editor and not isinstance(self.active_editor, UVExperimentEditor):
                editor = UVExperimentEditor()

                ms = self.manager.experiment_factory.queue_factory.mass_spectrometer
                editor.new_queue(mass_spectrometer=ms)
                editor.dirty = False

                #print self.active_editor
                #ask user to copy runs into the new editor
                ans = self.active_editor.queue.cleaned_automated_runs
                if ans:
                    if self.confirmation_dialog('Copy runs to the new UV Editor?'):
                        #editor.queue.executed_runs=self.active_editor.queue.executed_runs
                        editor.queue.automated_runs = self.active_editor.queue.automated_runs

                        #self.warning_dialog('Copying runs not yet implemented')

                self.active_editor.close()

                self._open_editor(editor)
                if not self.manager.executor.isAlive():
                    self.manager.executor.executable = False


    @on_trait_change('manager.experiment_factory:queue_factory:load_name')
    def _update_load(self, new):
        lm = self.loading_manager
        if lm is not None:
            if lm.load_name != new:
                lm.load_name = new
                canvas = lm.make_canvas(new, editable=False)
                self.load_pane.component = weakref.ref(canvas)()

            lm.load_load(new, group_labnumbers=False)

            self.load_pane.load_name = new

    @on_trait_change('active_editor:queue:refresh_blocks_needed')
    def _update_blocks(self):
        self.manager.experiment_factory.run_factory.load_run_blocks()

    @on_trait_change('active_editor:queue:update_needed')
    def _update_runs(self, new):
        self.manager.update_info()
        if self.active_editor.queue.initialized:
            self.active_editor.dirty = True

    @on_trait_change('editor_area:editors[]')
    def _update_editors(self, new):
        self.manager.experiment_queues = [ei.queue for ei in new]

    #        self.manager.executor.executable = False

    @on_trait_change('manager:executor:measuring_run:plot_panel')
    def _update_plot_panel(self, new):
        if new is not None:
            self.isotope_evolution_pane.plot_panel = new
            #         self.summary_pane.plot_panel = new

    @on_trait_change('manager:executor:console_updated')
    def _update_console(self, new):
        if self.use_notifications:
            self.notifier.send_console_message(new)

        if self.use_syslogger:
            self.syslogger.executor = self.manager.executor
            self.syslogger.trigger(new)

    @on_trait_change('manager:executor:run_completed')
    def _update_run_completed(self, new):
        self._publish_notification(new)

        load_name = self.manager.executor.experiment_queue.load_name
        if load_name:
            self._update_load(load_name)

    @on_trait_change('manager:add_queues_flag')
    def _add_queues(self, new):
        self.debug('add_queues_flag trigger n={}'.format(self.manager.add_queues_count))
        for _i in range(new):
            self.new()

    @on_trait_change('manager:activate_editor_event')
    def _set_active_editor(self, new):
        for ei in self.editor_area.editors:
            if id(ei.queue) == new:
                try:
                    self.editor_area.activate_editor(ei)
                except AttributeError:
                    pass
                break

    def _backup_editor(self, editor):
        p = editor.path
        p = add_extension(p, '.txt')

        if os.path.isfile(p):
            # make a backup copy of the original experiment file
            bp, _ = os.path.splitext(os.path.basename(p))

            pp = unique_date_path(paths.backup_experiment_dir, bp)

            self.info('{} - saving a backup copy to {}'.format(bp, pp))
            shutil.copyfile(p, pp)

    def _close_external_windows(self):
        """
            ask user if ok to close open spectrometer and extraction line windows
        """
        # ask user if ok to close windows
        windows = []
        names = []
        for wi in self.application.windows:
            wid = wi.active_task.id
            if wid == 'pychron.spectrometer':
                windows.append(wi)
                names.append('Spectrometer')
            elif wid == 'pychron.extraction_line':
                windows.append(wi)
                names.append('Extraction Line')

        if windows:
            is_are, them = 'is', 'it'
            if len(windows) > 1:
                is_are, them = 'are', 'them'
            msg = '{} {} open. Is it ok to close {}?'.format(','.join(names), is_are, them)

            if self.confirmation_dialog(msg):
                for wi in windows:
                    wi.close()

    @on_trait_change('manager:execute_event')
    def _execute(self):
        if self.editor_area.editors:
            self._close_external_windows()

            for ei in self.editor_area.editors:
                self._backup_editor(ei)

            qs = [ei.queue for ei in self.editor_area.editors
                  if ei != self.active_editor]

            if self.active_editor:
                qs.insert(0, self.active_editor.queue)

            # launch execution thread
            # if successful open an auto figure task
            if self.manager.execute_queues(qs):
                self._show_pane(self.wait_pane)
                self._set_last_experiment(self.active_editor.path)
            else:
                self.warning('experiment queue did not start properly')

    @on_trait_change('manager:executor:[measuring,extracting]')
    def _update_measuring(self, name, new):
        if new:
            if name == 'measuring':
                self._show_pane(self.isotope_evolution_pane)
            elif name == 'extracting':
                self._show_pane(self.wait_pane)

    @on_trait_change('active_editor:queue:dclicked')
    def _edit_event(self):
        p = self.experiment_factory_pane
        self._show_pane(p)

    @on_trait_change('manager:[save_event, executor:auto_save_event]')
    def _save_queue(self):
        self.save()

    def _prompt_for_save(self):
        """
            Prompt the user to save when exiting.
        """
        if self.manager.executor.isAlive():
            name = self.manager.executor.experiment_queue.name
            result = self._confirmation('{} is running. Are you sure you want to quit?'.format(name))
            if result in (CANCEL, NO):
                return False
            else:
                ret = super(ExperimentEditorTask, self)._prompt_for_save()
                if ret:
                    self.manager.executor.cancel(confirm=False)
                return ret
        else:
            return super(ExperimentEditorTask, self)._prompt_for_save()

    @on_trait_change('active_editor:dirty')
    def _update_active_editor_dirty(self):
        if self.active_editor:
            if self.active_editor.dirty:
                self.manager.executor.executable = False

    #===============================================================================
    # default/factory
    #===============================================================================

    #def _notifier_factory(self):
    #    n = Notifier(port=self.notifications_port)
    #    return n

    def _manager_factory(self):
        from pychron.experiment.experimentor import Experimentor
        from pychron.initialization_parser import InitializationParser

        ip = InitializationParser()
        plugin = ip.get_plugin('Experiment', category='general')
        mode = ip.get_parameter(plugin, 'mode')

        app = None
        if self.window:
            app = self.window.application

        exp = Experimentor(application=app,
                           mode=mode)

        return exp

    def _manager_default(self):
        return self._manager_factory()

    #def _notifier_default(self):
    #    return self._notifier_factory()

    # def _analysis_health_default(self):
    #     ah = AnalysisHealth(db=self.manager.db)
    #     return ah

    def _loading_manager_default(self):
        lm = self.window.application.get_service('pychron.loading.loading_manager.LoadingManager')
        if lm:
            lm.trait_set(db=self.manager.db,
                         show_group_positions=True)
            #         lm = LoadingManager(db=self.manager.db,
            #                             show_group_positions=True
            #                             )
            return lm

    def _default_directory_default(self):
        return paths.experiment_dir

    def _default_layout_default(self):
        #return TaskLayout(left=PaneItem('pychron.lasers.client'))

        return TaskLayout(
            left=Splitter(
                PaneItem('pychron.experiment.wait', height=100),
                Tabbed(
                    PaneItem('pychron.experiment.factory'),
                    PaneItem('pychron.experiment.isotope_evolution')),
                orientation='vertical'),
            right=Splitter(
                Tabbed(
                    PaneItem('pychron.experiment.stats'),
                    PaneItem('pychron.console', height=425),
                    PaneItem('pychron.experiment.explanation', height=425),
                    PaneItem('pychron.experiment.connection_status')),
                orientation='vertical'),
            top=PaneItem('pychron.experiment.controls'))
        #============= EOF =============================================
        #         editor = self.active_editor
        #         if editor is None:
        #             if self.editor_area.editors:
        #                 editor = self.editor_area.editors[0]
        #
        #         if editor:
        #             p = editor.path
        #             p = add_extension(p, '.txt')
        #
        #             if os.path.isfile(p):
        #                 # make a backup copy of the original experiment file
        #                 shutil.copyfile(p, '{}.orig'.format(p))
        #
        # #                 group = editor.group
        # #                 min_idx = editor.merge_id
        # #                 text = open(p, 'r').read()
        # #                 hash_val = hashlib.sha1(text).hexdigest()
        # #                 qs = [ei.queue
        # #                         for ei in self.editor_area.editors
        # #                             if ei.group == group and ei.merge_id >= min_idx]
        #                 qs = [ei.queue for ei in self.editor_area.editors]
        #                 # launch execution thread
        #                 # if successful open an auto figure task
        # #                 if self.manager.execute_queues(qs, p, text, hash_val):
        #                 if self.manager.execute_queues(qs, p):
        #                     self._open_auto_figure()

        #     def merge(self):
        #         eqs = [self.active_editor.queue]
        #         self.active_editor.merge_id = 1
        #         self.active_editor.group = self.group_count
        #         self.group_count += 1
        #         for i, ei in enumerate(self.editor_area.editors):
        #             if not ei == self.active_editor:
        #                 eqs.append(ei.queue)
        #                 ei.merge_id = i + 2
        #                 ei.group = self.group_count
        #
        #         path = self.save_file_dialog()
        #         if path:
        #             self.active_editor.save(path, eqs)
        #             for ei in self.editor_area.editors:
        #                 ei.path = path