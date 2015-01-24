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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, \
    Property, on_trait_change, Button, Enum, List, Instance
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
import re
# ============= local library imports  ==========================
# from pychron.processing.tasks.browser.browser_task import NCHARS
from pychron.core.progress import open_progress
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.processing.tasks.browser.analysis_table import AnalysisTable

NCHARS = 60
REG = re.compile(r'.' * NCHARS)


class BrowserModel(BrowserMixin):
    manager = Any

    filter_focus = Bool(True)
    use_focus_switching = Bool(True)
    filter_label = Property(Str, depends_on='filter_focus')

    irradiation_visible = Property(depends_on='filter_focus')
    analysis_types_visible = Property(depends_on='filter_focus')
    date_visible = Property(depends_on='filter_focus')
    mass_spectrometer_visible = Property(depends_on='filter_focus')
    identifier_visible = Property(depends_on='filter_focus')
    project_visible = Property(depends_on='filter_focus')

    filter_by_button = Button
    graphical_filter_button = Button
    toggle_view = Button
    toggle_focus = Button

    current_task_name = Enum('Recall', 'IsoEvo', 'Blanks', 'ICFactor', 'Ideogram', 'Spectrum')
    datasource_url = Str
    irradiation_enabled = Bool
    irradiations = List
    irradiation = Str
    # irradiation_enabled = Bool
    levels = List
    level = Str
    analysis_table = Instance(AnalysisTable, ())

    is_activated = False

    def activated(self, force=False):
        if not self.is_activated or force:
            self.load_browser_options()
            if self.sample_view_active:
                self.activate_sample_browser(force)
                self.filter_focus = True
            else:
                pass

        self.is_activated = True

    def activate_sample_browser(self, force=False):
        if not self.is_activated or force:
            self.load_projects()

            db = self.manager.db
            with db.session_ctx():
                self._load_mass_spectrometers()

            self.datasource_url = db.datasource_url
            # self._preference_binder('pychron.browsing',
            #                         ('recent_hours','graphical_filtering_max_days',
            #                          'reference_hours_padding'),
            #                         obj=self.search_criteria)

            self.load_browser_selection()

    # handlers
    def _toggle_focus_fired(self):
        self.filter_focus = not self.filter_focus

    # def _toggle_view_fired(self):
    #     self.sample_view_active = not self.sample_view_active
    #     if not self.sample_view_active:
    #         self._activate_query_browser()
    #     else:
    #         self.activate_sample_browser()
    #
    #     self.dump()

    def _selected_samples_changed(self, new):
        if new:
            at = self.analysis_table
            lim = at.limit
            kw = dict(limit=lim,
                      include_invalid=not at.omit_invalid,
                      mass_spectrometers=self._recent_mass_spectrometers)

            ss = self.selected_samples
            xx = ss[:]
            # if not any(['RECENT' in p for p in self.selected_projects]):
            # sp=self.selected_projects
            # if not hasattr(sp, '__iter__'):
            #     sp = (sp, )

            if not any(['RECENT' in p.name for p in self.selected_projects]):
                reftypes = ('blank_unknown',)
                if any((si.analysis_type in reftypes
                        for si in ss)):
                    with self.db.session_ctx():
                        ans = []
                        for si in ss:
                            if si.analysis_type in reftypes:
                                xx.remove(si)
                                dates = list(self._project_date_bins(si.identifier))
                                print dates
                                progress = open_progress(len(dates))
                                for lp, hp in dates:

                                    progress.change_message('Loading Date Range '
                                                            '{} to {}'.format(lp.strftime('%m-%d-%Y %H:%M:%S'),
                                                                              hp.strftime('%m-%d-%Y %H:%M:%S')))
                                    ais = self._retrieve_sample_analyses([si],
                                                                         make_records=False,
                                                                         low_post=lp,
                                                                         high_post=hp, **kw)
                                    ans.extend(ais)
                                progress.close()

                        ans = self._make_records(ans)
                    # print len(ans), len(set([si.record_id for si in ans]))
            if xx:
                lp, hp = self.low_post, self.high_post
                ans = self._retrieve_sample_analyses(xx,
                                                     low_post=lp,
                                                     high_post=hp,
                                                     **kw)
                self.debug('selected samples changed. loading analyses. '
                           'low={}, high={}, limit={}'.format(lp, hp, lim))

            self.analysis_table.set_analyses(ans)
            self.dump_browser()

        self.filter_focus = not bool(new)

    @on_trait_change('analysis_table:selected')
    def _handle_analysis_selected(self, new):
        if self.use_focus_switching:
            self.filter_focus = not bool(new)

    # private
    def _load_mass_spectrometers(self):
        db = self.manager.db
        ms = db.get_mass_spectrometers()
        if ms:
            ms = [mi.name for mi in ms]
            self.available_mass_spectrometers = ms

    def _load_analysis_types(self):
        db = self.manager.db
        ms = [mi.name for mi in db.get_analysis_types()]
        self.analysis_types = ['Analysis Type', 'None'] + ms

    def _load_extraction_devices(self):
        db = self.manager.db
        ms = [mi.name for mi in db.get_extraction_devices()]
        self.extraction_devices = ['Extraction Device', 'None'] + ms

    def _get_analysis_types_visible(self):
        return self._get_visible(self.use_analysis_type_filtering)

    def _get_irradiation_visible(self):
        return self._get_visible(self.irradiation_enabled)

    def _get_date_visible(self):
        return self._get_visible(self.use_low_post or self.use_high_post or self.use_named_date_range)

    def _get_mass_spectrometer_visible(self):
        return self._get_visible(self.use_mass_spectrometers)

    def _get_identifier_visible(self):
        return self.filter_focus if self.use_focus_switching else True

    def _get_project_visible(self):
        return self._get_visible(self.project_enabled)

    def _get_visible(self, default):
        ret = True
        if self.use_focus_switching and not self.filter_focus:
            ret = False  # default
        return ret

    def _get_filter_label(self):
        ss = []
        if self.identifier:
            ss.append('Identifier={}'.format(self.identifier))

        if self.use_mass_spectrometers:
            ss.append('MS={}'.format(','.join(self.mass_spectrometer_includes)))

        if self.project_enabled:
            if self.selected_projects:
                s = 'Project= {}'.format(','.join([s.name for s in self.selected_projects]))
                ss.append(s)

        if self.irradiation_enabled:
            if self.irradiation:
                s = 'Irradiation= {}'.format(self.irradiation)
                ss.append(s)

        if self.use_analysis_type_filtering:
            if self.analysis_include_types:
                s = 'Types= {}'.format(self.analysis_include_types)
                ss.append(s)

        if self.use_low_post:
            # s='>={}'.format(self.low_post.strftime('%m-%d-%Y %H:%M'))
            s = '>={}'.format(self.low_post)
            ss.append(s)

        if self.use_high_post:
            s = '<={}'.format(self.high_post)
            ss.append(s)

        if self.use_named_date_range:
            ss.append(self.named_date_range)

        txt = ''
        if ss:
            txt = ' + '.join(ss)

        n = len(txt)
        if n > NCHARS:
            lines = REG.findall(txt)
            nn = NCHARS * len(lines)
            if nn < n:
                lines.append(txt[nn:])
            return '\n'.join(lines)

        return txt

# ============= EOF =============================================



