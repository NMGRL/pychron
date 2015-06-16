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
from datetime import datetime, timedelta
import random
from threading import Timer, Lock
import time
# from apptools.preferences.preference_binding import bind_preference

from traits.api import Instance, Int, Bool, on_trait_change, Any, List, Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import ufloat
from pychron.displays.display import DisplayController
from pychron.globals import globalv
from pychron.messaging.notify.subscriber import Subscriber
from pychron.processing.analyses.file_analysis import FileAnalysis
from pychron.processing.plotter_options_manager import SystemMonitorOptionsManager, SysMonIdeogramOptionsManager
from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor
from pychron.pipeline.plot.editors.series_editor import SeriesEditor
from pychron.pychron_constants import ALPHAS
from pychron.system_monitor.tasks.connection_spec import ConnectionSpec
from pychron.system_monitor.tasks.controls import SystemMonitorControls
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.preference_binding import color_bind_preference

"""
    subscribe to pyexperiment
    or poll database for changes

    use poll to check subscription availability
    suspend db poll when subscription becomes available

"""


def camel_case(name):
    args = name.split('_')
    return ''.join(map(str.capitalize, args))


class SysMonIdeogramEditor(IdeogramEditor):
    plotter_options_manager = Instance(SysMonIdeogramOptionsManager, ())


class SystemMonitorEditor(SeriesEditor):
    conn_spec = Instance(ConnectionSpec, ())
    # name = Property(depends_on='conn_spec:+')
    oname = Str
    search_tool = Instance(SystemMonitorControls)
    subscriber = Instance(Subscriber)
    plotter_options_manager_klass = SystemMonitorOptionsManager
    pickle_path = 'system_monitor'

    use_poll = Bool(False)
    _poll_interval = Int(10)
    _db_poll_interval = Int(10)
    _polling = False

    console_display = Instance(DisplayController)
    # _ideogram_editor = None
    # _spectrum_editor = None
    _ideogram_editors = List
    _spectrum_editors = List

    _air_editor = None
    _blank_air_editor = None
    _blank_unknown_editor = None
    _cocktail_editor = None
    _blank_cocktail_editor = None
    _background_editor = None

    task = Any
    _pause = False

    _flag = False

    def __init__(self, *args, **kw):
        super(SystemMonitorEditor, self).__init__(*args, **kw)
        color_bind_preference(self.console_display.model, 'bgcolor', 'pychron.sys_mon.bgcolor')
        color_bind_preference(self.console_display, 'default_color', 'pychron.sys_mon.textcolor')

    def reset_editors(self):
        """
        Trigger a new editors to be build next update

        :return:
        """
        # self._ideogram_editor = None
        # self._spectrum_editor = None
        self._cnt = 0

    def prepare_destroy(self):
        self.debug('destroy editor')
        self.stop()
        self.dump_tool()
        for e in ('air', 'blank_air',
                  'cocktail', 'blank_cocktail',
                  'background'):
            e = getattr(self, '_{}_editor'.format(e))
            if e is not None:
                e.dump_tool()

        for es in (self._spectrum_editors, self._ideogram_editors):
            for e in es:
                e.dump_tool()

    def stop(self):
        self._polling = False
        self.subscriber.stop()

    def pause(self):
        self._pause = not self._pause

    def console_message_handler(self, msg):
        color = 'green'
        if '|' in msg:
            color, msg = msg.split('|')

        self.console_display.add_text(msg, color=color)

    def start(self):

        self._lock = Lock()
        self.name = '{}-{}'.format(self.conn_spec.system_name, self.conn_spec.host)
        self.oname = self.name

        self.load_tool()

        if self.conn_spec.host:
            sub = self.subscriber
            connected = sub.connect(timeout=0.1)

            sub.subscribe('RunAdded', self._run_added_handler, True)
            sub.subscribe('ConsoleMessage', self.console_message_handler)

            if connected:
                sub.listen()
                self.task.connection_pane.connection_status = 'Connected'
                self.task.connection_pane.connection_color = 'green'

            else:
                self.task.connection_pane.connection_status = 'Not Connected'
                self.task.connection_pane.connection_color = 'red'

                url = self.conn_spec.url
                self.warning('System publisher not available url={}'.format(url))

        # t = Thread(name='poll', target=self._poll)
        # t.setDaemon(True)
        # t.start()
        # self._poll()
        t = Timer(2, self._poll)
        t.start()

    def _get_dump_tool(self):
        return self.search_tool

    def _load_tool(self, obj, **kw):
        self.search_tool = obj

    def _poll(self):
        self._polling = True
        sub = self.subscriber

        db_poll_interval = 3 if globalv.system_monitor_debug else self._db_poll_interval
        poll_interval = 3 if globalv.system_monitor_debug else self._poll_interval

        def func(last_run_uuid, st):
            # only check subscription availability if one poll_interval has elapsed
            # since the last subscription message was received
            if not self._pause:
                self.debug('poll iteration: uuid: {}, st={}'.format(last_run_uuid, st))
                # check subscription availability
                # if time.time() - sub.last_message_time > poll_interval:
                if sub.check_server_availability(timeout=0.5, verbose=True):
                    if not sub.is_listening():
                        self.info('Subscription server now available. starting to listen')
                        self.subscriber.listen()
                else:
                    if sub.was_listening:
                        self.warning('Subscription server no longer available. stop listen')
                        self.subscriber.stop()

                if not sub.is_listening() and not self._pause:
                    if time.time() - st > db_poll_interval:  # or globalv.system_monitor_debug:

                        self._lock.acquire()
                        st = time.time()
                        lr = self._get_last_run_uuid()
                        if lr != last_run_uuid:
                            self.debug('current uuid {} <> {}'.format(last_run_uuid, lr))
                            if not globalv.system_monitor_debug:
                                last_run_uuid = lr
                            self._run_added_handler(lr)

            if self._polling:
                t = Timer(poll_interval, func, args=(last_run_uuid, st))
                t.start()

        func(None, time.time())

    def _get_last_run_uuid(self):
        db = self.processor.db
        with db.session_ctx():
            dbrun = db.get_last_analysis(spectrometer=self.conn_spec.system_name)
            if dbrun:
                return dbrun.uuid

    def _run_added_handler(self, last_run_uuid=None):
        """
            add to sys mon series
            if atype is blank, air, cocktail, background
                add to atype series
            else
                if step heat
                    add to spectrum
                else
                    add to ideogram
        """

        def func(lr):
            self._refresh_sys_mon_series()
            self.info('refresh analyses. last UUID={}'.format(lr))

            proc = self.processor
            db = proc.db
            with db.session_ctx():
                if last_run_uuid is None:
                    dbrun = db.get_last_analysis(spectrometer=self.conn_spec.system_name)
                else:
                    dbrun = db.get_analysis_uuid(last_run_uuid)

                self.debug('run_added_handler dbrun={}'.format(dbrun))
                if dbrun:
                    self.debug('run_added_handler identifier={}'.format(dbrun.labnumber.identifier))
                    an = proc.make_analysis(dbrun)
                    self._refresh_figures(an)

            # self.rebuild()
            self._lock.release()

        invoke_in_main_thread(func, last_run_uuid)

    def _refresh_sys_mon_series(self):
        if globalv.system_monitor_debug:
            ans = [FileAnalysis(age=2 * random.random() + 10,
                                aliquot=i,
                                peak_center=ufloat(random.random(), 0.1),
                                timestamp=time.time(),
                                labnumber='{:04d}'.format(3000),
                                age_err=random.random()) for i in range(min(self.search_tool.limit, 50))]
        else:
            ms = self.conn_spec.system_name
            ans = self.processor.analysis_series(ms, weeks=self.search_tool.weeks,
                                                 days=self.search_tool.days,
                                                 hours=self.search_tool.hours,
                                                 limit=self.search_tool.limit)
        ans = self._sort_analyses(ans)
        self.analyses = ans
        # self.rebuild()
        # self.set_items(ans, update_graph=False)
        # self.rebuild_graph()

    def _refresh_figures(self, an):
        if an.analysis_type == 'unknown':
            if globalv.system_monitor_debug:
                if self._cnt > 40:
                    self._refresh_spectrum('2000', 1)
                else:
                    self._refresh_ideogram('1000' if self._flag else '2000')

            else:

                if an.step:
                    self._refresh_spectrum(an.labnumber, an.aliquot)
                else:
                    self._refresh_ideogram(an.labnumber)
        else:
            atype = an.analysis_type

            func = getattr(self, '_refresh_{}'.format(atype))
            func(an.labnumber)

    def _refresh_blank_unknown(self, identifier):
        self._set_series('blank_unknown', identifier)

    def _refresh_air(self, identifier):
        self._set_series('air', identifier)

    def _refresh_blank_air(self, identifier):
        self._set_series('blank_air', identifier)

    def _refresh_cocktail(self, identifier):
        self._set_series('cocktail', identifier)

    def _refresh_blank_cocktail(self, identifier):
        self._set_series('blank_cocktail', identifier)

    def _refresh_background(self, identifier):
        self._set_series('background', identifier)

    def _set_series(self, attr, identifier):
        name = '_{}_editor'.format(attr)
        editor = getattr(self, name)

        def new():
            e = self.task.new_series(add_table=False,
                                     add_iso=False)
            # self.task.tab_editors(0, -1)
            e.basename = '{} Series'.format(camel_case(attr))
            e.search_tool = self.search_tool
            self.task.controls_pane.tool = self.search_tool

            return e

        editor = self._update_editor(editor, new, identifier, None,
                                     use_date_range=True)
        setattr(self, name, editor)

    # def close_editor(self, ei):
    # if ei in self._ideogram_editors:
    # self._ideogram_editors.remove(ei)
    #     elif ei in self._spectrum_editors:
    #         self._spectrum_editors.remove(ei)

    def _get_editor(self, editors, identifier):
        editor = next((ei for ei in editors if ei.identifier == identifier), None)
        if editor:
            self.task.activate_editor(editor)
        return editor

    def _refresh_ideogram(self, identifier):
        """
            open a ideogram editor for this identifier if one is not already open.
            if an editor with this identifier exists activate it.

        """
        editor = self._get_editor(self._ideogram_editors, identifier)

        f = lambda: self.task.new_ideogram(add_table=False,
                                           klass=SysMonIdeogramEditor,
                                           add_iso=False)
        editor = self._update_editor(editor, f, identifier, None,
                                     calculate_age=True)

        if editor not in self._ideogram_editors:
            self._ideogram_editors.append(editor)

        self._reset_ideogram = False

    def _refresh_spectrum(self, identifier, aliquot):
        """
            open a spectrum editor for this identifier if one is not already open.
            if an editor with this identifier exists activate it.

        """
        editor = self._get_editor(self._spectrum_editors, identifier)
        f = lambda: self.task.new_spectrum(add_table=False, add_iso=False)
        editor = self._update_editor(editor, f, identifier, aliquot,
                                     calculate_age=True)

        if editor not in self._spectrum_editors:
            self._spectrum_editors.append(editor)

        self._reset_spectrum = False

    def _update_editor(self, editor, editor_factory,
                       identifier, aliquot,
                       use_date_range=False, calculate_age=False):
        if editor is None:
            editor = editor_factory()

        if not hasattr(editor, 'starttime'):
            editor.starttime = datetime.now()

        editor.identifier = identifier

        # gather analyses
        if hasattr(editor, 'search_tool'):
            tool = editor.search_tool
        else:
            tool = self.search_tool

        ans = self._get_analyses(tool, identifier,
                                 aliquot, use_date_range)
        ans = self._sort_analyses(ans)

        if calculate_age:
            for ai in ans:
                ai.calculate_age()
        editor.set_items(ans, update_graph=False)
        # group_analyses_by_key(editor.analyses, 'labnumber')

        # editor.clear_aux_plot_limits()
        # do_later(editor.rebuild)
        # editor.rebuild()
        return editor

    def _sort_analyses(self, ans):
        return sorted(ans, key=lambda x: x.timestamp, reverse=True)

    _cnt = 0

    def _get_analyses(self, tool, identifier, aliquot=None, use_date_range=False):
        if globalv.system_monitor_debug:
            import numpy as np

            self._cnt += 1
            if self._cnt > 40:
                return [FileAnalysis(age=2 * random.random() + 10,
                                     aliquot=1,
                                     step=ALPHAS[i],
                                     k39=2 + random.random() * 10,
                                     k39_err=0,
                                     timestamp=time.time(),
                                     labnumber='{:04d}'.format(2000),
                                     age_err=random.random()) for i in range(self._cnt - 4)]
            else:
                np.random.seed(1234567)
                ages = np.random.random((self._cnt, 2))
                return [FileAnalysis(age=a + 10,
                                     aliquot=i,
                                     timestamp=time.time(),
                                     labnumber='{:04d}'.format(1000 if self._flag else 2000),
                                     age_err=e) for i, (a, e) in enumerate(ages)]
        else:
            db = self.processor.db
            with db.session_ctx():
                if aliquot is not None:
                    def func(a, l):
                        return l.identifier == identifier, a.aliquot == aliquot

                    ans = db.get_analyses(func=func)
                elif use_date_range:

                    high = datetime.now()
                    low = tool.low
                    if low is None:
                        low = high - timedelta(hours=tool.hours,
                                               weeks=tool.weeks,
                                               days=tool.days)
                        tool.low = low

                    ans = db.get_analyses_date_range(low, high,
                                                     labnumber=identifier,
                                                     order='desc',
                                                     limit=tool.limit)
                else:
                    ans, tc = db.get_labnumber_analyses(identifier, order='desc', limit=tool.limit)

                return self.processor.make_analyses(ans)

    @on_trait_change('search_tool:[weeks, days, hours, limit]')
    def _handle_tool_change(self, name, new):
        self.debug('tool change name:{}, new:{}'.format(name, new))

        self._lock.acquire()
        self._run_added_handler()

    def _load_refiso(self, ref):
        pass

    def _set_name(self):
        """
        override SeriesMonitor._set_name
        """
        pass

    #
    # def _get_name(self):
    #     return '{}-{}'.format(self.conn_spec.system_name,
    #                           self.conn_spec.host)

    def _search_tool_default(self):
        tool = SystemMonitorControls()
        return tool

    def _console_display_default(self):
        return DisplayController(
            bgcolor='black',
            default_color='limegreen',
            max_blocks=100)

    def _subscriber_default(self):
        h = self.conn_spec.host
        p = self.conn_spec.port

        self.info('Creating subscriber to {}:{}"'.format(h, p))
        sub = Subscriber(host=self.conn_spec.host,
                         port=self.conn_spec.port,
                         verbose=False)
        return sub

# ============= EOF =============================================
