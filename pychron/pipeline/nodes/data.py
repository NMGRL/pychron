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
from pyface.message_dialog import information
from pyface.timer.do_later import do_after
from traits.api import Instance, Bool, Int, Str, List, Enum, Float, Time
from traitsui.api import View, Item, EnumEditor, CheckListEditor

from pychron.globals import globalv
from pychron.pipeline.nodes.base import BaseNode
from pychron.pychron_constants import ANALYSIS_TYPES


class DVCNode(BaseNode):
    """

    Base node for all nodes that need access to a DVC instance or BrowserModel for
    retrieving analyses
    """
    dvc = Instance('pychron.dvc.dvc.DVC')
    browser_model = Instance('pychron.envisage.browser.browser_model.BrowserModel')

    def get_browser_analyses(self, irradiation=None, level=None):
        from pychron.envisage.browser.view import BrowserView

        self.browser_model.activated()
        self.browser_model.do_filter()

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

    check_reviewed = Bool(False)

    def configure(self, pre_run=False, **kw):
        if pre_run and getattr(self, self.analysis_kind):
            return True

        if not pre_run:
            self._manual_configured = True

        return self.set_browser_analyses()


class CSVNode(BaseNode):
    path = Str
    name = 'CSV Data'

    def configure(self, pre_run=False, **kw):
        if not pre_run:
            self._manual_configured = True

        if not self.path or not os.path.isfile(self.path):
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
        return self._get_items_from_file(par)

    def _get_items_from_file(self, parser):
        from pychron.processing.analyses.file_analysis import FileAnalysis

        def gen():
            for d in parser.itervalues():
                if d['age'] is not None:
                    f = FileAnalysis(age=float(d['age']),
                                     age_err=float(d['age_err']),
                                     record_id=d['runid'],
                                     sample=d.get('sample', ''),
                                     aliquot=int(d.get('aliquot', 0)),
                                     group_id=int(d.get('group', 0)))
                    yield f

        return tuple(gen())


class UnknownNode(DataNode):
    name = 'Unknowns'
    analysis_kind = 'unknowns'

    def set_last_n_analyses(self, n):
        db = self.dvc.db
        ans = db.get_last_n_analyses(n)
        records = [ri for ai in ans for ri in ai.record_views]
        self.unknowns = self.dvc.make_analyses(records)

    def set_last_n_hours_analyses(self, n):
        db = self.dvc.db
        ans = db.get_last_nhours_analyses(n)
        if ans:
            records = [ri for ai in ans for ri in ai.record_views]
            self.unknowns = self.dvc.make_analyses(records)

    def run(self, state):
        # if not self.unknowns and not state.unknowns:
        #     if not self.configure():
        #         state.canceled = True
        #         return

        review_req = []
        unks = self.unknowns
        for ai in unks:
            ai.group_id = 0
            if self.check_reviewed:
                for attr in ('blanks', 'iso_evo'):
                    # check analyses to see if they have been reviewed
                    if attr not in review_req:
                        if not self.dvc.analysis_has_review(ai, attr):
                            review_req.append(attr)

        if review_req:
            information(None, 'The current data set has been '
                              'analyzed and requires {}'.format(','.join(review_req)))

        # add our analyses to the state
        items = getattr(state, self.analysis_kind)
        items.extend(self.unknowns)

        state.projects = {ai.project for ai in state.unknowns}


class ReferenceNode(DataNode):
    name = 'References'
    analysis_kind = 'references'

    def pre_run(self, state):
        self.unknowns = state.unknowns
        refs = state.references
        if refs:
            if state.append_references:
                self.references.extend(refs)
            else:
                self.references = refs

        if not self.references:
            self.configure(pre_run=True)

        return self.references

    def run(self, state):
        pass


class FluxMonitorsNode(DataNode):
    name = 'Flux Monitors'
    analysis_kind = 'flux_monitors'
    auto_configure = False

    def run(self, state):
        items = getattr(state, self.analysis_kind)
        self.unknowns = items


class BaseAutoUnknownNode(UnknownNode):
    mode = Enum('Normal', 'Window')
    hours = Int(12)
    mass_spectrometer = Str
    available_spectrometers = List
    analysis_types = List(ANALYSIS_TYPES)
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
        v = View(Item('mode', tooltip='Normal: get analyses between now and start of pipeline - hours\n'
                                      'Window: get analyses between now and now - hours'),
                 Item('hours'),
                 Item('period', label='Update Period (s)',
                      tooltip='Default time (s) to delay between "check for new analyses"'),
                 Item('mass_spectrometer', label='Mass Spectrometer',
                      editor=EnumEditor(name='available_spectrometers')),
                Item('analysis_types',style='custom',
                     editor=CheckListEditor(name='available_analysis_types', cols=len(self.available_analysis_types))),
                 Item('post_analysis_delay', label='Post Analysis Found Delay',
                      tooltip='Time (min) to delay before next "check for new analyses"'),
                 Item('verbose'),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v

    def post_run(self, engine, state):
        if not self._alive:
            self.engine = engine
            if not self.single_shot:
                self._start_listening()

            self._post_run_hook()

    def reset(self):
        self._stop_listening()

    def _post_run_hook(self):
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

            print 'low={}'.format(low)
            print 'high={}'.format(high)
            print 'ats={}'.format(ats)
            print 'ms={}'.format(self.mass_spectrometer)
            unks = self.dvc.get_analyses_by_date_range(low, high,
                                                       analysis_types=ats,
                                                       mass_spectrometers=self.mass_spectrometer, verbose=self.verbose)
            records = [ri for unk in unks for ri in unk.record_views]

            print 'retrived n records={}'.format(len(records))
            if not self._cached_unknowns:
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


class CalendarUnknownNode(BaseAutoUnknownNode):
    name = 'Unknowns (Calendar)'
    run_time = Time
    _ran = False

    def run(self, state):
        self._low = datetime.now()
        super(CalendarUnknownNode, self).run(state)

    def _run_time_default(self):
        return (datetime.now() + timedelta(minutes=2)).time()

    def _post_run_hook(self):
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
        print 'now={} run_time={}. hourmatch={}, minutematch={} ran={}'.format(now, self.run_time,
                                                                               now.hour >= self.run_time.hour,
                                                                               now.minute >= self.run_time.minute,
                                                                               self._ran)
        if now.hour >= self.run_time.hour:
            if now.minute >= self.run_time.minute:
                if not self._ran:
                    self._ran = True
                    unks, updated = self._load_analyses()
                    if not self._alive:
                        return
                    print 'updated={} loaded unks={}'.format(updated, unks)

                    if unks:
                        self.engine.rerun_with(unks, post_run=False)
        else:
            self._ran = False

        period = 60*10
        do_after(1000 * period, self._iter)

    def traits_view(self):
        v = View(Item('run_time'),
                 Item('hours'),
                 # Item('period', label='Update Period (s)',
                 #      tooltip='Defauly time (s) to delay between "check for new analyses"'),
                 Item('mass_spectrometer', label='Mass Spectrometer',
                      editor=EnumEditor(name='available_spectrometers')),
                 Item('analysis_types', style='custom',
                      editor=CheckListEditor(name='available_analysis_types', cols=len(self.available_analysis_types))),
                 # Item('post_analysis_delay', label='Post Analysis Found Delay',
                 #      tooltip='Time (min) to delay before next "check for new analyses"'),
                 Item('verbose'),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v


class ListenUnknownNode(BaseAutoUnknownNode):
    name = 'Unknowns (Auto)'

    exclude_uuids = List
    period = Int(15)

    post_analysis_delay = Float(5)

    max_period = 10
    _between_updates = None

    def configure(self, pre_run=False, *args, **kw):
        if pre_run:
            info = self.edit_traits()
            return info.result
        return BaseNode.configure(self, pre_run=pre_run, *args, **kw)

    def traits_view(self):
        v = View(Item('mode', tooltip='Normal: get analyses between now and start of pipeline - hours\n'
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
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v

    def run(self, state):
        self._low = datetime.now()
        unks, updated = self._load_analyses()
        state.unknowns = unks

    def _finish_load_hook(self):
        if globalv.auto_pipeline_debug:
            self.mass_spectrometer = 'jan'
            self.period = 15
            self.hours = 48

    def _iter(self, acc=1.0, last_update=None):
        if not self._alive:
            return

        unks, updated = self._load_analyses()
        if not self._alive:
            return

        if unks:
            unks_ids = [id(ai) for ai in unks]
            if self._unks_ids != unks_ids:
                # self.unknowns = unks
                self._unks_ids = unks_ids
                self.engine.rerun_with(unks, post_run=False)
                self.engine.refresh_figure_editors()

        if not self._alive:
            return

        st = None
        if updated:
            # if a new analysis was just found wait
            # for at least `post_analysis_delay` mins before querying again
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

        do_after(int(period * 1000), self._iter, acc, st)

# ============= EOF =============================================
