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
import os
import shelve
from pyface.tasks.traits_task_pane import TraitsTaskPane

from traits.api import Instance, on_trait_change, List
from pyface.tasks.task_layout import TaskLayout, Splitter, PaneItem, Tabbed
from pychron.entry.sensitivity_entry import SensitivityEntry
from pychron.entry.tasks.sensitivity_entry_panes import SensitivityPane

from pychron.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pychron.processing.tasks.batch_edit.batch_editor import BatchEditor
from pychron.processing.tasks.batch_edit.panes import BatchEditPane
from pychron.paths import paths

#from pychron.processing.entry.sensitivity_entry import SensitivityEntry
#from pychron.processing.tasks.entry.sensitivity_entry_panes import SensitivityPane
from pychron.processing.tasks.browser.browser_task import BaseBrowserTask
#from pychron.processing.tasks.figures.panes import MultiSelectAnalysisBrowser
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.smart_selection.panes import SmartSelection


class BatchEditTask(AnalysisEditTask):
    name = 'Batch Edit'
    id = 'pychron.analysis_edit.batch'
    central_pane = Instance(TraitsTaskPane)
    central_pane_klass = BatchEditPane
    batch_editor = Instance(BatchEditor, ())

    unknowns = List

    smart_selection = Instance(SmartSelection, ())

    #def create_dock_panes(self):
    #panes = AnalysisEditTask.create_dock_panes(self)
    #slp = SmartSelectio nConfigurePane(model=self.smart_selection)
    #panes.append(slp)

    #return panes

    #@on_trait_change('smart_selection:[project_filter,]')
    #def _handle_smart_selection(self, new):
    #    print new

    def _create_control_pane(self):
        pass

    def create_central_pane(self):
        self.central_pane = self.central_pane_klass(model=self.batch_editor)
        return self.central_pane

    def prepare_destroy(self):
        p = os.path.join(paths.hidden_dir, self.id)
        d = shelve.open(p)
        d['values'] = self.batch_editor.values
        d['blanks'] = self.batch_editor.blanks

        d.close()
        self.dump_browser_selection()

    def activated(self):
        p = os.path.join(paths.hidden_dir, self.id)
        if os.path.isfile(p):
            d = shelve.open(p)

            try:
                self.batch_editor.values = d['values']
                self.batch_editor.blanks = d['blanks']
            except Exception:
                pass

        BaseBrowserTask.activated(self)

    #             d.close()
    #             for bin in self.central_pane.blanks:
    #                 print bin.use

    def _prompt_for_save(self):
        return True

    def _save_to_db(self):

        # already in a db session
        self.debug('save to database')
        cname = 'blanks'
        proc = self.manager
        for ui in self.analyses:
            # blanks
            history = proc.add_history(ui, cname)
            for bi in self.central_pane.blanks:
                if bi.use:
                    self.debug('applying blank correction {} {}'.format(ui.record_id, bi.name))
                    proc.apply_fixed_correction(history, bi.name,
                                                bi.nominal_value, bi.std_dev,
                                                cname)

            # disc/ic factors
            ics = []
            for value in self.central_pane.values:
                if value.use:
                    if value.name == 'disc':
                        self._add_discrimination(ui.dbrecord, value.nominal_value,
                                                 value.std_dev)
                    else:
                        '''
                            value.name == 'IC <det_key>'
                        '''
                        det = value.name[3:]
                        ics.append((det, value.nominal_value, value.std_dev))
            dets = [args[0] for args in ics]
            for args in ics:
                self._add_ic_factory(ui.dbrecord, dets, *args)


    def _add_ic_factory(self, analysis, dets, det, v, e):
        '''
            det= current detector 
            dets= all detectors that will be added. use this so that previous ics
            are not copied. ie. if prev_hist_det in dets dont copy prev_hist_det 
        '''
        db = self.manager.db

        history = db.add_detector_intercalibration_history(analysis)
        #         db.flush()
        dbdet = db.get_detector(det)
        if dbdet is None:
            self.warning_dialog('Could not find Detector database entry for {}'.format(det))
            return

        # copy previous intercalibrations for other detectors
        phist = analysis.selected_histories.selected_detector_intercalibration
        if phist is not None:
            for ics in phist.detector_intercalibrations:
                if not ics.detector == dbdet and ics.detector.name not in dets:
                    db.add_detector_intercalibration(history, ics.detector,
                                                     user_value=ics.user_value,
                                                     user_error=ics.user_error,
                                                     sets=ics.sets,
                                                     fit=ics.fit
                    )

        db.add_detector_intercalibration(history, dbdet,
                                         user_value=v, user_error=e
        )
        analysis.selected_histories.selected_detector_intercalibration = history

    def _add_discrimination(self, analysis, v, e):
        db = self.manager.db
        hist = db.add_detector_parameter_history(analysis)

        db.add_detector_parameter(hist, disc=v, disc_error=e)
        analysis.dbrecord.selected_histories.selected_detector_param = hist

    @on_trait_change('unknowns_pane:[items, update_needed]')
    def _update_unknowns_runs(self, obj, name, old, new):
        AnalysisEditTask._update_unknowns_runs(self, obj, name, old, new)

        # ans=self.manager.make_analyses(self.unknowns_pane.items)
        self.batch_editor.populate(self.unknowns_pane.items)

    @on_trait_change('unknowns_pane:[append_button, replace_button]')
    def _append_unknowns(self, obj, name, old, new):

        s=self._get_selected_analyses(self.analyses)
        if s:
            if name=='replace_button':
                self.unknowns_pane.items=s
            else:
                self.unknowns_pane.items.extend(s)

        #is_append = name == 'append_button'
        #unks = None
        #if is_append:
        #    unks = self.unknowns

        #s = self._get_selected_analyses(unks)
        #if s:
        #    s = self.manager.make_analyses(s)
            #if is_append:
            #    unks.extend(s)
            #else:
            #    self.unknowns = s
            #
            #self.unknowns_pane.items = self.unknowns

            #===============================================================================

        # handlers
    #===============================================================================
    #     @on_trait_change('unknowns_pane:items')
    #     def _update_unknowns_runs(self, obj, name, old, new):
    #         if not obj._no_update:
    #             self.unknowns = unks = self.manager.make_analyses(self.unknowns_pane.items)
    # #             self.manager.load_analyses(unks)
    #             self.central_pane.unknowns = unks

    @on_trait_change('batch_editor:db_sens_button')
    def _update_db_sens_button(self):
        app = self.window.application
        #entry = app.get_service('pychron.entry.modal_sensitivity')
        #if entry:
        #    print entry

        se = SensitivityEntry()
        se.activate()

        p = SensitivityPane(model=se)
        info = p.edit_traits(kind='livemodal', view='readonly_view')
        if info.result:
            s = se.selected
            if s is not None:
                self.batch_editor.sens_value = s.sensitivity

            #===============================================================================
            # defaults
            #===============================================================================

    def _default_layout_default(self):
        #c=PaneItem('pychron.smart_selection.configure')
        search = Tabbed(PaneItem('pychron.browser'))
                        #PaneItem('pychron.search.query'))

        #a=Splitter(d,orientation='vertical')

        unk = PaneItem('pychron.analysis_edit.unknowns')

        left = Splitter(search, unk)

        return TaskLayout(
            id='pychron.analysis_edit.batch',
            left=left)

#============= EOF =============================================
