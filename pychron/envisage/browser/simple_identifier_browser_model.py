# ===============================================================================
# Copyright 2020 ross
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
from pychron.envisage.browser.analysis_browser_model import AnalysisBrowserModel
from pychron.envisage.browser.view import SimpleIdentifierBrowserView


class SimpleIdentifierBrowserModel(AnalysisBrowserModel):

    def _retrieve_labnumbers(self):
        es = []
        ps = []
        ms = []
        ls = []
        if self.load_enabled and self.selected_loads:
            ls = [s.name for s in self.selected_loads]

        if self.mass_spectrometers_enabled:
            if self.mass_spectrometer_includes:
                ms = self.mass_spectrometer_includes

        principal_investigators = None
        if self.principal_investigator_enabled and self.selected_principal_investigators:
            principal_investigators = [p.name for p in self.selected_principal_investigators]

        if self.project_enabled:
            if self.selected_projects:
                ps = [p.unique_id for p in self.selected_projects]

        at = self.analysis_include_types if self.use_analysis_type_filtering else None

        hp = self.high_post
        lp = self.low_post

        ats = []
        samples = None
        if at:
            for a in at:
                if a == 'monitors':
                    if not self.monitor_sample_name:
                        self.warning_dialog('Please Set Monitor name in preferences. Defaulting to FC-2')
                        self.monitor_sample_name = 'FC-2'

                    samples = [self.monitor_sample_name, ]
                else:
                    ats.append(a)

        lns = self.db.get_simple_identifiers(principal_investigators=principal_investigators,
                                             project_ids=ps,
                                             samples=samples,
                                             mass_spectrometers=ms,
                                             analysis_types=ats,
                                             high_post=hp,
                                             low_post=lp,
                                             loads=ls,
                                             filter_non_run=self.filter_non_run_samples)
        return lns

    def _selected_projects_change_hook(self, names):
        self.selected_samples = []
        self.analysis_table.clear_non_frozen()
        #
        if not self._top_level_filter:
            self._top_level_filter = 'project'

    def _browser_view_default(self):
        return SimpleIdentifierBrowserView(model=self)
# ============= EOF =============================================
