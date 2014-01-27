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
from traits.api import on_trait_change
from pyface.tasks.task_layout import TaskLayout, VSplitter, PaneItem, \
    HSplitter, Tabbed
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.paths import r_mkdir
from pychron.processing.tasks.analysis_edit.interpolation_editor import bin_analyses
from pychron.processing.tasks.analysis_edit.interpolation_task import InterpolationTask, no_auto_ctx


class IntercalibrationFactorTask(InterpolationTask):
    id = 'pychron.processing.ic_factor'
    ic_factor_editor_count = 1
    name = 'Detector Intercalibration'

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.processing.ic_factor',
            left=HSplitter(
                PaneItem('pychron.browser'),
                VSplitter(
                    Tabbed(PaneItem('pychron.processing.unknowns'),
                           PaneItem('pychron.processing.references')),
                    PaneItem('pychron.processing.controls'),
                )
            )
        )

    def new_ic_factor(self):
        from pychron.processing.tasks.detector_calibration.intercalibration_factor_editor import IntercalibrationFactorEditor

        editor = IntercalibrationFactorEditor(name='ICFactor {:03n}'.format(self.ic_factor_editor_count),
                                              processor=self.manager)
        self._open_editor(editor)
        self.ic_factor_editor_count += 1

        #selector = self.manager.db.selector
        #self.unknowns_pane.items = selector.records[156:159]
        #self.references_pane.items = selector.records[150:155]

    @on_trait_change('active_editor:tool:[analysis_type, refresh_references]')
    def _handle_analysis_type(self, obj, name, old, new):
        if name == 'analysis_type':
            if new:
                self._set_analysis_type(new)
        elif name=='refresh_references':
            if obj.analysis_type:
                self._set_analysis_type(self.analysis_type)

    def _set_analysis_type(self, new, progress=None):
        records = self.unknowns_pane.items
        if records:
            ans = self._load_references(records, new)
            ans = self.manager.make_analyses(ans, progress=progress)
            self.references_pane.items = ans

    def do_easy_ic(self):
        self._do_easy_func()

    def _easy_func(self, ep, manager):
        db = self.manager.db

        doc = ep.doc('ic')
        # fits = doc['fits']
        projects = doc['projects']
        atype = doc['atype']

        identifiers = doc.get('identifiers')
        if identifiers:
            # unks = [ai for proj in projects
            #         for si in db.get_samples(project=proj)
            #         for ln in si.labnumbers
            #         if str(ln.identifier) in identifiers
            #         for ai in ln.analyses
            #         if ai.measurement.mass_spectrometer.name.lower() in ('jan', 'obama')]
            unks = [ai for ln in identifiers
                    for ai in db.get_labnumber(ln).analyses
                        if not ai.tag=='invalid']

        else:
            unks = [ai for proj in projects
                    for si in db.get_samples(project=proj)
                    for ln in si.labnumbers
                    for ai in ln.analyses
                    if ai.measurement.mass_spectrometer.name.lower() in ('jan', 'obama') and not ai.tag=='invalid']

        prog = manager.progress
        prog.increase_max(len(unks))

        # preceding_fits, non_preceding_fits = map(list, partition(fits, lambda x: x['fit'] == 'preceding'))
        # if preceding_fits:
        #     self.debug('preceding fits for ic_factors not implemented')
        # for ai in unks:
        #     if prog.canceled:
        #         return
        #     elif prog.accepted:
        #         break
        #     l, a, s = ai.labnumber.identifier, ai.aliquot, ai.step
        #     prog.change_message('Save preceding blank for {}-{:02n}{}'.format(l, a, s))
        #     hist = db.add_history(ai, 'blanks')
        #     ai.selected_histories.selected_blanks = hist
        #     for fi in preceding_fits:
        #         self._preceding_correct(db, fi, ai, hist)

        #make figure root dir
        if doc['save_figures']:
            root = doc['figure_root']
            r_mkdir(root)

        # if non_preceding_fits:
        with no_auto_ctx(self.active_editor):
            for ais in bin_analyses(unks):
                if prog.canceled:
                    return
                elif prog.accepted:
                    break

                self.active_editor.set_items(ais, progress=prog)
                self._set_analysis_type(atype, progress=prog)

                self.active_editor.tool.trait_set(analysis_type=atype)

                if not manager.wait_for_user():
                    return

                if not manager.was_skipped():
                    #save a figure
                    if doc['save_figures']:
                        title = self.active_editor.make_title()
                        p = os.path.join(root, add_extension(title, '.pdf'))
                        self.active_editor.save_file(p)

                    self.active_editor.save(progress=prog)
                    self.active_editor.dump_tool()

        return True

#============= EOF =============================================
