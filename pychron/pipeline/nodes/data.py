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
import time
from datetime import datetime, timedelta

from pyface.constant import OK
from pyface.file_dialog import FileDialog
from pyface.message_dialog import warning, information
from pyface.timer.do_later import do_after
from traits.api import Instance, Bool, Int, Str, List, Enum, Float, Time
from traitsui.api import Item, EnumEditor, CheckListEditor

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.globals import globalv
from pychron.pipeline.nodes.base import BaseNode
from pychron.pychron_constants import ANALYSIS_TYPES


class BaseDVCNode(BaseNode):
    dvc = Instance('pychron.dvc.dvc.DVC')


class DVCNode(BaseDVCNode):
    """

    Base node for all nodes that need access to a DVC instance or BrowserModel for
    retrieving analyses
    """

    browser_model = Instance('pychron.envisage.browser.browser_model.BrowserModel')

    def get_browser_analyses(self, irradiation=None, level=None):
        from pychron.envisage.browser.view import BrowserView

        self.browser_model.activated()
        # self.browser_model.do_filter()

        if irradiation:
            self.browser_model.irradiation_enabled = True
            self.browser_model.irradiation = irradiation
            if level:
                self.browser_model.level = level

        browser_view = BrowserView(model=self.browser_model)
        info = browser_view.edit_traits(kind='livemodal')
        records = None
        if info.result:
            self.browser_model.add_analysis_set()
            self.browser_model.dump_browser()

            records = self.browser_model.get_analysis_records()
            if records:
                records = self.dvc.make_analyses(records)
        return browser_view.is_append, records

    def set_browser_analyses(self):
        is_append, analyses = self.get_browser_analyses()
        if analyses:
            if is_append:
                ans = getattr(self, self.analysis_kind)
                ans.extend(analyses)
            else:
                self.trait_set(**{self.analysis_kind: analyses})

            return True


class InterpretedAgeNode(DVCNode):
    name = 'Interpreted Ages'
    interpreted_ages = List

    def configure(self, pre_run=False, **kw):
        if not pre_run:
            self._manual_configured = True

        from pychron.envisage.browser.view import InterpretedAgeBrowserView

        self.browser_model.activated()

        browser_view = InterpretedAgeBrowserView(model=self.browser_model)
        info = browser_view.edit_traits(kind='livemodal')

        if info.result:
            self.browser_model.dump_browser()

            records = self.browser_model.get_interpreted_age_records()

            if records:
                interpreted_ages = self.dvc.make_interpreted_ages(records)

                if browser_view.is_append:
                    ias = self.interpreted_ages
                    ias.extend(interpreted_ages)
                else:
                    self.interpreted_ages = interpreted_ages

            return True

    def run(self, state):
        state.interpreted_ages = self.interpreted_ages
        state.unknowns = self.interpreted_ages


class DataNode(DVCNode):
    name = 'Data'

    analysis_kind = None

    def configure(self, pre_run=False, **kw):
        # print(self, pre_run, getattr(self, self.analysis_kind), self.index)
        if pre_run and getattr(self, self.analysis_kind) and self.index == 0:
            return True

        if not pre_run:
            self._manual_configured = True

        return self.set_browser_analyses()


class CSVNode(BaseNode):
    path = Str
    name = 'CSV Data'

    def reset(self):
        super(CSVNode, self).reset()
        self.path = ''

    def configure(self, pre_run=False, **kw):
        if not pre_run:
            self._manual_configured = True

        if not self.path or not os.path.isfile(self.path):
            msg = '''CSV File Format
Create/select a file with a column header as the first line. 
The following columns are required:

runid, age, age_err

Optional columns are:

group, aliquot

e.x.
runid, age, age_error
SampleA, 10, 0.24
SampleB, 11, 0.32
SampleC, 10, 0.40'''
            information(None, msg)

            dlg = FileDialog()
            if dlg.open() == OK:
                self.path = dlg.path

        return bool(self.path)

    def run(self, state):
        if not self.unknowns:
            if not self.configure():
                state.canceled = True
                return

        unks = self._load_analyses()
        if unks:
            self.unknowns.extend(unks)

        # add our analyses to the state
        items = state.unknowns
        items.extend(self.unknowns)

    def _load_analyses(self):
        from pychron.core.csv.csv_parser import CSVColumnParser

        par = CSVColumnParser(delimiter=',')
        par.load(self.path)
        if par.check(('runid', 'age', 'age_err')):
            return self._get_items_from_file(par)
        else:
            warning(None, 'Invalid file format. Minimum columns required are "runid", "age", "age_err"')

    def _get_items_from_file(self, parser):
        from pychron.processing.analyses.file_analysis import FileAnalysis

        def gen():
            for d in parser.values():
                try:
                    f = FileAnalysis(age=float(d['age']),
                                     age_err=float(d['age_err']),
                                     record_id=d['runid'],
                                     sample=d.get('sample', ''),
                                     aliquot=int(d.get('aliquot', 0)),
                                     group_id=int(d.get('group', 0)))
                    yield f
                except TypeError:
                    pass

        try:
            return tuple(gen())
        except ValueError as e:
            warning(None, 'Invalid values in the import file. Error="{}"'.format(e))


class UnknownNode(DataNode):
    name = 'Unknowns'
    analysis_kind = 'unknowns'

    def set_last_n_analyses(self, n):
        db = self.dvc.db
        ans = db.get_last_n_analyses(n)
        self.unknowns = self.dvc.make_analyses(ans)

    def set_last_n_hours_analyses(self, n):
        db = self.dvc.db
        ans = db.get_last_nhours_analyses(n)
        if ans:
            self.unknowns = self.dvc.make_analyses(ans)

    def pre_run(self, state, configure=True):
        # force Unknown node to always configure
        return super(UnknownNode, self).pre_run(state, configure=True)

    def run(self, state):
        # add our analyses to the state
        items = getattr(state, self.analysis_kind)
        items.extend(self.unknowns)

        state.projects = {ai.project for ai in state.unknowns if hasattr(ai, 'project')}


class ReferenceNode(DataNode):
    name = 'References'
    analysis_kind = 'references'

    def pre_run(self, state, configure=True):
        self.unknowns = state.unknowns
        refs = state.references
        if refs:
            self.references = refs

        if not self.references:
            if configure:
                self.configure(pre_run=True)

        return self.references

    def run(self, state):
        pass


class FluxMonitorsNode(DataNode):
    name = 'Flux Monitors'
    analysis_kind = 'unknowns'
    auto_configure = False

    def run(self, state):
        items = getattr(state, self.analysis_kind)
        self.unknowns = items


class BaseAutoUnknownNode(UnknownNode):
    mode = Enum('Normal', 'Window')
    hours = Int(12)
    mass_spectrometer = Str
    available_spectrometers = List
    analysis_types = List(['Unknown'])
    available_analysis_types = List(ANALYSIS_TYPES)
    engine = None
    single_shot = False
    verbose = Bool

    _cached_unknowns = None
    _unks_ids = None
    _updated = False
    _alive = False

    def finish_load(self):
        self.available_spectrometers = self.dvc.get_mass_spectrometer_names()
        if self.available_spectrometers:
            self.mass_spectrometer = self.available_spectrometers[0]

        self._finish_load_hook()

    def configure(self, pre_run=False, *args, **kw):
        if pre_run:
            info = self.edit_traits()
            return info.result
        return BaseNode.configure(self, pre_run=pre_run, *args, **kw)

    def traits_view(self):
        v = okcancel_view(Item('mode', tooltip='Normal: get analyses between now and start of pipeline - hours\n'
                                      'Window: get analyses between now and now - hours'),
                 Item('hours'),
                 Item('period', label='Update Period (s)',
                      tooltip='Default time (s) to delay between "check for new analyses"'),
                 Item('mass_spectrometer', label='Mass Spectrometer',
                      editor=EnumEditor(name='available_spectrometers')),
                 Item('analysis_types', style='custom',
                      editor=CheckListEditor(name='available_analysis_types', cols=len(self.available_analysis_types))),
                 Item('post_analysis_delay', label='Post Analysis Found Delay',
                      tooltip='Time (min) to delay before next "check for new analyses"'),
                 Item('verbose'))
        return v

    def post_run(self, engine, state):
        if not self._alive:
            self.engine = engine
            if not self.single_shot:
                self._start_listening()

            self._post_run_hook(engine, state)

    def reset(self):
        super(BaseAutoUnknownNode, self).reset()
        self._stop_listening()

    def _post_run_hook(self, engine, state):
        pass

    def _finish_load_hook(self):
        if globalv.auto_pipeline_debug:
            self.mass_spectrometer = 'jan'
            self.period = 15
            self.hours = 48

    def _start_listening(self):
        self._alive = True
        self._updated = False
        self._iter()

    def _stop_listening(self):
        self._alive = False

    def _iter(self):
        raise NotImplementedError

    def _load_analyses(self):
        td = timedelta(hours=self.hours)
        high = datetime.now()
        updated = False

        if self.mode == 'Normal':
            low = self._low - td
        else:
            low = high - td

        with self.dvc.session_ctx(use_parent_session=False):
            ats = [a.lower().replace(' ', '_') for a in self.analysis_types]
            records = self.dvc.get_analyses_by_date_range(low, high,
                                                          analysis_types=ats,
                                                          mass_spectrometers=self.mass_spectrometer,
                                                          verbose=self.verbose)

            if not self._cached_unknowns:
                updated = True
                ans = self.dvc.make_analyses(records)
            else:
                ans = []
                ais = []
                for ri in records:
                    ca = next((ci for ci in self._cached_unknowns if ci.record_id == ri.record_id), None)
                    if ca is not None:
                        ans.append(ca)
                    else:
                        ais.append(ri)

                if ais:
                    updated = True
                    # the database may have updated but the repository not yet updated.
                    # sleeping X seconds is a potential work around but a little dumb.
                    # better solution is to save to database after repository is updated
                    try:
                        ans.extend(self.dvc.make_analyses(ais))
                    except BaseException:
                        time.sleep(10)
                        try:
                            ans.extend(self.dvc.make_analyses(ais))
                        except BaseException:
                            pass

        self._cached_unknowns = ans
        return ans, updated


class ListenUnknownNode(BaseAutoUnknownNode):
    name = 'Unknowns (Auto)'

    exclude_uuids = List
    period = Int(15)

    post_analysis_delay = Float(5)

    max_period = 10
    _between_updates = None
    pipeline = None
    state = None
    _low = None

    def clear_data(self):
        super(ListenUnknownNode, self).clear_data()
        self.pipeline = None
        self.state = None
        self.skip_configure = False

    def reset(self):
        super(ListenUnknownNode, self).reset()
        self.pipeline = None
        self.state = None
        self.skip_configure = False

    def _start_listening(self):
        self._alive = True
        self._updated = False
        self._iter()
        self._status_loop()

    def _status_loop(self):
        self.active = not self.active
        self.visited = not self.active
        self.engine.refresh_all_needed = True
        do_after(1000, self._status_loop)

    def _post_run_hook(self, engine, state):
        self.pipeline = engine.pipeline
        engine.pipeline.active = True

    def traits_view(self):
        v = okcancel_view(Item('mode', tooltip='Normal: get analyses between now and start of pipeline - hours\n'
                                      'Window: get analyses between now and now - hours'),
                 Item('hours'),
                 Item('period', label='Update Period (s)',
                      tooltip='Default time (s) to delay between "check for new analyses"'),
                 Item('mass_spectrometer', label='Mass Spectrometer',
                      editor=EnumEditor(name='available_spectrometers')),
                 Item('analysis_types', style='custom',
                      editor=CheckListEditor(name='available_analysis_types', cols=len(self.available_analysis_types))),
                 Item('post_analysis_delay', label='Post Analysis Found Delay',
                      tooltip='Time (min) to delay before next "check for new analyses"'),
                 Item('verbose'),
                 title='Configure',
                 )
        return v

    def run(self, state):
        if not self._alive:
            self._low = datetime.now()
            unks, updated = self._load_analyses()
            state.unknowns = unks
            self.unknowns = unks
            self.state = state
            self.skip_configure = True

    def _finish_load_hook(self):
        if globalv.auto_pipeline_debug:
            self.mass_spectrometer = 'jan'
            self.period = 15
            self.hours = 48

    def _iter(self, last_update=None):
        if not self._alive:
            return

        unks, updated = self._load_analyses()
        if not self._alive:
            return

        st = None
        if updated:

            self.state.unknowns = unks
            self.unknowns = unks
            self.engine.run(post_run=False, pipeline=self.pipeline, state=self.state, configure=False)

            self.engine.post_run_refresh(state=self.state)
            self.engine.refresh_figure_editors()
            self.engine.selected = self.pipeline.nodes[-1]

            if not self._alive:
                return

            st = time.time()
            if last_update:
                if self._between_updates:
                    self._between_updates = ((st - last_update) + self._between_updates) / 2.
                else:
                    self._between_updates = st - last_update

                period = self._between_updates * 0.75

            else:
                period = 60 * self.post_analysis_delay
        else:
            period = self.period

        do_after(int(period * 1000), self._iter, st)


class CalendarUnknownNode(BaseAutoUnknownNode):
    name = 'Unknowns (Calendar)'
    run_time = Time
    _ran = False

    def run(self, state):
        self._low = datetime.now()
        super(CalendarUnknownNode, self).run(state)

    def _run_time_default(self):
        return (datetime.now() + timedelta(minutes=2)).time()

    def _post_run_hook(self, engine, state):
        self._flash_iter(0)

    def _flash_iter(self, cnt):
        if not self._alive:
            return

        self.visited = bool(cnt % 2)
        self.engine.update_needed = True

        if cnt > 100:
            cnt = 0
        do_after(1000, self._flash_iter, cnt + 1)

    def _iter(self):
        if not self._alive:
            return

        now = datetime.now()
        print('now={} run_time={}. hourmatch={}, minutematch={} ran={}'.format(now, self.run_time,
                                                                               now.hour >= self.run_time.hour,
                                                                               now.minute >= self.run_time.minute,
                                                                               self._ran))
        if now.hour >= self.run_time.hour:
            if now.minute >= self.run_time.minute:
                if not self._ran:
                    self._ran = True
                    unks, updated = self._load_analyses()
                    if not self._alive:
                        return
                    print('updated={} loaded unks={}'.format(updated, unks))

                    if unks:
                        self.engine.rerun_with(unks, post_run=False)
        else:
            self._ran = False

        period = 60 * 10
        do_after(1000 * period, self._iter)

    def traits_view(self):
        v = okcancel_view(Item('run_time'),
                 Item('hours'),
                 # Item('period', label='Update Period (s)',
                 #      tooltip='Defauly time (s) to delay between "check for new analyses"'),
                 Item('mass_spectrometer', label='Mass Spectrometer',
                      editor=EnumEditor(name='available_spectrometers')),
                 Item('analysis_types', style='custom',
                      editor=CheckListEditor(name='available_analysis_types', cols=len(self.available_analysis_types))),
                 # Item('post_analysis_delay', label='Post Analysis Found Delay',
                 #      tooltip='Time (min) to delay before next "check for new analyses"'),
                 Item('verbose'))
        return v
# ============= EOF =============================================
