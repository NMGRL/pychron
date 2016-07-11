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
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Instance, Bool, Button
from traitsui.api import View, UItem, VGroup, HGroup, EnumEditor
# ============= standard library imports ========================
from datetime import datetime, timedelta
# ============= local library imports  ==========================
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.browser.browser_task import BaseBrowserTask
from pychron.envisage.browser.recall_editor import RecallEditor
from pychron.envisage.browser.search.searcher import Searcher
from pychron.envisage.browser.view import PaneBrowserView
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.actions import ToggleFullWindowAction
from pychron.globals import globalv
from pychron.pipeline.tasks.actions import ConfigureRecallAction, ConfigureAnalysesTableAction, \
    LoadReviewStatusAction, EditAnalysisAction, DiffViewAction
from pychron.pipeline.tasks.analysis_range_selector import AnalysisRangeSelector


class BrowserPane(TraitsDockPane, PaneBrowserView):
    id = 'pychron.browser.pane'
    name = 'Analysis Selection'


class SearcherPane(TraitsDockPane):
    name = 'Search'
    id = 'pychron.browser.searcher.pane'
    add_search_entry_button = Button

    def _add_search_entry_button_fired(self):
        self.model.add_search_entry()

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('search_entry'),
                               UItem('search_entry', editor=EnumEditor(name='search_entries'), width=-35),
                               icon_button_editor('pane.add_search_entry_button', 'add')),
                        UItem('object.analysis_table.analyses',
                              editor=myTabularEditor(adapter=self.model.analysis_table.tabular_adapter,
                                                     operations=['move', 'delete'],
                                                     column_clicked='object.analysis_table.column_clicked',
                                                     refresh='object.analysis_table.refresh_needed',
                                                     selected='object.analysis_table.selected',
                                                     dclicked='object.analysis_table.dclicked'))))
        return v


class BrowserTask(BaseBrowserTask):
    name = 'Analysis Browser'

    searcher = Instance(Searcher)
    model = Instance('pychron.envisage.browser.browser_model.BrowserModel')
    tool_bars = [SToolBar(ConfigureRecallAction(),
                          ConfigureAnalysesTableAction(),
                          name='Configure'),
                 SToolBar(ToggleFullWindowAction(),
                          LoadReviewStatusAction(),
                          DiffViewAction(),
                          name='View'),
                 SToolBar(EditAnalysisAction(),
                          name='Edit')]

    diff_enabled = Bool

    def activated(self):
        if self.application.get_plugin('pychron.mass_spec.plugin'):
            self.diff_enabled = True
        super(BrowserTask, self).activated()

    def _opened_hook(self):
        super(BrowserTask, self)._opened_hook()

        self.browser_model.activated()
        self._activate_sample_browser()

        if globalv.browser_debug:
            if self.browser_model.analysis_table.analyses:
                r = self.browser_model.analysis_table.analyses[0]
                self.recall(r)

    # menu actions
    def open_time_view_browser(self):
        self.debug('open time view')

        v = AnalysisRangeSelector()
        v.load()

        db = self.dvc.db
        spec_names = db.get_mass_spectrometer_names()
        v.set_mass_spectrometers(spec_names)

        # open a time view selector
        info = v.edit_traits(kind='livemodal')
        if info.result:
            v.dump()

        sms = v.selected_mass_spectrometers
        ants = v.selected_analysis_types
        # with db.session_ctx():
        #     if v.use_date_range:
        #         h, l = v.high_post, v.low_post
        #         ans = db.get_analyses_date_range(l, h,
        #                                          analysis_type=ants,
        #                                          mass_spectrometers=sms)
        #     else:
        #         # get analyses
        #         ans, h, l = db.get_last_nhours_analyses(v.nhours,
        #                                                 return_limits=True,
        #                                                 analysis_types=ants,
        #                                                 mass_spectrometers=sms)
        #
        #     def func(x, prog, i, n):
        #         return x.record_views
        #
        #     records = progress_loader(ans, func)
        #
        # # set analysis_table.analyses
        # bm.analysis_table.set_analyses(records)
        # bm.analysis_table.scroll_to_row = len(records)
        if v.use_date_range:
            h, l = v.high_post, v.low_post
        else:
            now = datetime.now()
            h, l = now, now - timedelta(hours=v.nhours)
        bm = self.browser_model
        if sms:
            bm.mass_spectrometers_enabled = True
            bm.mass_spectrometer_includes = v.selected_mass_spectrometers
        if ants:
            bm.use_analysis_type_filtering = True
            bm._analysis_include_types = ants

        bm._low_post = l.date()
        bm.use_low_post = True

        bm._high_post = h.date()
        bm.use_high_post = True

        bm.do_filter()
        bm.select_all()

        at = bm.analysis_table
        end = len(at.analyses)
        at.scroll_to_row = end

    # toolbar actions
    def diff_analysis(self):
        self.debug('diff analysis')
        if not self.has_active_editor():
            return

        active_editor = self.active_editor
        if not isinstance(active_editor, RecallEditor):
            self.warning_dialog('Active tab must be a Recall tab')
            return

        left = active_editor.analysis

        recaller = self.application.get_service('pychron.mass_spec.mass_spec_recaller.MassSpecRecaller')
        if recaller is None:
            self.warning_dialog('Could not access MassSpec database')
            return

        if not recaller.connect():
            self.warning_dialog('Could not connect to MassSpec database. {}'.format(recaller.db.datasource_url))
            return

        from pychron.pipeline.editors.diff_editor import DiffEditor
        editor = DiffEditor(recaller=recaller)
        # left.set_stored_value_states(True, save=True)

        if not left.check_has_n():
            left.load_raw_data(n_only=True)

        if editor.setup(left):
            editor.set_diff(left)
            self._open_editor(editor)
        else:
            self.warning_dialog('Failed to locate analysis {} in MassSpec database'.format(left.record_id))
            # left.revert_use_stored_values()

    def create_dock_panes(self):
        return [BrowserPane(model=self.browser_model),
                SearcherPane(model=self.searcher)]

    def _searcher_default(self):
        db = self.application.get_service('pychron.dvc.dvc.DVC')
        s = Searcher(db=db,
                     analysis_table=self.browser_model.analysis_table)
        return s

    def _default_layout_default(self):
        # return TaskLayout(left=PaneItem('pychron.browser.pane'))
        return TaskLayout(left=PaneItem('pychron.browser.searcher.pane'))

# ============= EOF =============================================
