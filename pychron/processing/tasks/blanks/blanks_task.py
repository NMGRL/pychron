# ===============================================================================
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
# ===============================================================================

#============= enthought library imports =======================
# from traits.api import HasTraits
import os

from pyface.tasks.task_layout import TaskLayout, PaneItem, HSplitter, Tabbed

from pychron.core.helpers.filetools import add_extension
from pychron.core.helpers.iterfuncs import partition
from pychron.paths import r_mkdir
from pychron.processing.tasks.analysis_edit.interpolation_editor import bin_analyses
from pychron.processing.tasks.analysis_edit.interpolation_task import InterpolationTask, no_auto_ctx

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.browser.util import browser_pane_item


class BlanksTask(InterpolationTask):
    id = 'pychron.processing.blanks'
    blank_editor_count = 1
    name = 'Blanks'
    default_reference_analysis_type = 'blank_unknown'

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.processing.blanks',
            left=HSplitter(
                Tabbed(
                    browser_pane_item(),
                    PaneItem('pychron.search.query')),
                Tabbed(
                    PaneItem('pychron.processing.unknowns'),
                    PaneItem('pychron.processing.references'),
                    PaneItem('pychron.processing.controls'))))

    def new_blank(self):
        from pychron.processing.tasks.blanks.blanks_editor import BlanksEditor

        editor = BlanksEditor(name='Blanks {:03n}'.format(self.blank_editor_count),
                              processor=self.manager,
                              task=self,
                              default_reference_analysis_type=self.default_reference_analysis_type)

        self._open_editor(editor)
        self.blank_editor_count += 1

    #def _set_selected_analysis(self, new):
    #    if not new:
    #        return
    #
    #    self._load_references(new)

    def do_easy_blanks(self):
        self._do_easy_func()

    def _easy_func(self, ep, manager):
        db = self.manager.db

        doc = ep.doc('blanks')
        fits = doc['blank_fit_isotopes']
        projects = doc['projects']

        unks = [ai for proj in projects
                for si in db.get_samples(project=proj)
                for ln in si.labnumbers
                for ai in ln.analyses
                if ai.measurement.mass_spectrometer.name == 'MAP'
            and ai.extraction.extraction_device.name in ('Furnace', 'Eurotherm')]
        # for proj in projects:
        #     for si in db.get_samples(project=proj):
        #         for ln in si.labnumbers:
        #             for ai in ln.analyses:
        #                 print ai.measurement.mass_spectrometer.name,ai.extraction.extraction_device.name
        #                 print ai.measurement.mass_spectrometer.name == 'nmgrl map' and ai.extraction.extraction_device.name in ('Furnace','Eurotherm')
        print len(unks)
        prog = manager.progress
        # prog = self.manager.open_progress(len(ans) + 1)
        #bin analyses
        prog.increase_max(len(unks))

        preceding_fits, non_preceding_fits = map(list, partition(fits, lambda x: x['fit'] == 'preceding'))
        if preceding_fits:
            for ai in unks:
                if prog.canceled:
                    return
                elif prog.accepted:
                    break
                l, a, s = ai.labnumber.identifier, ai.aliquot, ai.step
                prog.change_message('Save preceding blank for {}-{:02n}{}'.format(l, a, s))
                hist = db.add_history(ai, 'blanks')
                ai.selected_histories.selected_blanks = hist
                for fi in preceding_fits:
                    self._preceding_correct(db, fi, ai, hist)

        #make figure root dir
        if doc['save_figures']:
            root = doc['figure_root']
            r_mkdir(root)

        with no_auto_ctx(self.active_editor):
            if non_preceding_fits:
                for fi in self.active_editor.tool.fits:
                    fi.fit = 'average'
                    fi.error_type = 'SEM'
                    fi.filter_outliers = True
                    fi.filter_iterations = 1
                    fi.filter_std_devs = 2

                for ais in bin_analyses(unks):
                    if prog.canceled:
                        return
                    elif prog.accepted:
                        break

                    self.active_editor.set_items(ais, progress=prog)
                    self.active_editor.find_references(progress=prog)

                    #refresh graph
                    # invoke_in_main_thread(self.active_editor.rebuild_graph)
                    #
                    # if not manager.wait_for_user():
                    #     return

                    #save a figure
                    if doc['save_figures']:
                        title = self.active_editor.make_title()
                        p = os.path.join(root, add_extension(title, '.pdf'))
                        self.active_editor.save_file(p)

                    self.active_editor.save(progress=prog)

                    self.active_editor.dump_tool()
        return True

    def _preceding_correct(self, db, fi, ai, hist):
        pa = db.get_preceding(ai.analysis_timestamp,
                              ai.measurement.mass_spectrometer.name)
        if pa:
            an_pa = self.manager.make_analysis(pa)
            iso = fi['name']
            # print an_pa.record_id
            if iso in an_pa.isotopes:
                blank = an_pa.isotopes[iso].get_non_detector_corrected_value()
                # print iso, blank.nominal_value, blank.std_dev

                dbblank = db.add_blanks(hist,
                                        isotope=iso,
                                        user_value=float(blank.nominal_value),
                                        user_error=float(blank.std_dev),
                                        fit='preceding')

                db.add_blanks_set(dbblank, pa)

            else:
                self.warning('{} does not have iso {}'.format(an_pa.record_id, iso))

        else:
            self.warning('No preceding analyses for {}-{:02n}{}'.format(ai.labnumber.identifier,
                                                                        ai.aliquot, ai.step))


# ============= EOF =============================================
