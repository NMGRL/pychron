# ===============================================================================
# Copyright 2017 ross
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
from traits.api import Bool, List, Instance
from traitsui.api import View, UItem, Item, VGroup, InstanceEditor, Tabbed

from pychron.core.helpers.filetools import unique_path
from pychron.core.pdf.base_pdf_writer import BasePDFWriter
from pychron.core.pdf.options import BasePDFOptions
from pychron.loading.component_flowable import ComponentFlowable
from pychron.options.options_manager import SeriesOptionsManager, OptionsController
from pychron.options.views.views import view
from pychron.paths import paths
from pychron.pipeline.plot.editors.series_editor import SeriesEditor


class BUReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'bu_report_series'


class AirReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'air_report_series'


class ReportOptions(BasePDFOptions):
    blank_unknowns_enabled = Bool
    airs_enabled = Bool
    cocktails_enabled = Bool
    blank_unknowns_enabled = Bool

    blank_unknowns_series_options_manager = Instance(BUReportSeriesOptionsManager, ())
    blank_unknowns_series_options_controller = Instance(OptionsController)

    airs_series_options_manager = Instance(AirReportSeriesOptionsManager, ())
    airs_series_options_controller = Instance(OptionsController)

    def set_names(self, names):
        self.blank_unknowns_series_options_manager.set_names(names)
        self.airs_series_options_manager.set_names(names)

    @property
    def path(self):
        p, _ = unique_path(paths.report_dir, 'report', extension='.pdf')
        return p

    def traits_view(self):
        bu_grp = VGroup(Item('blank_unknowns_enabled', label='Enabled'),
                        UItem('blank_unknowns_series_options_controller',
                              editor=InstanceEditor(view=view('Blank Unknowns')),
                              style='custom',
                              enabled_when='blank_unknowns_enabled'),
                        label='Blank Unknowns')

        air_grp = VGroup(Item('airs_enabled', label='Enabled'),
                         UItem('airs_series_options_controller',
                               editor=InstanceEditor(view=view('Airs')),
                               style='custom',
                               enabled_when='airs_enabled'),
                         label='Airs')

        v = View(Tabbed(bu_grp, air_grp),
                 buttons=['OK', 'Cancel'])
        return v

    def _blank_unknowns_series_options_controller_default(self):
        o = OptionsController(model=self.blank_unknowns_series_options_manager)
        return o

    def _airs_series_options_controller_default(self):
        o = OptionsController(model=self.airs_series_options_manager)
        return o


class ReportWriter(BasePDFWriter):
    _analyses = List
    options = Instance(ReportOptions)

    def make_report(self, analyses):
        self._analyses = analyses

        path = self.options.path
        self.build(path)

    # private
    def _build(self, *args, **kw):
        flowables = []
        templates = None

        f = self._make_time_series('blank_unknown')
        flowables.extend(f)

        f = self._make_time_series('air')
        flowables.extend(f)

        return flowables, templates

    def _make_time_series(self, analysis_type, ):

        opt = getattr(self.options, '{}s_series_options_manager'.format(analysis_type)).selected_options

        ans = self._get_analyses(analysis_type)
        name = ' '.join((a.capitalize() for a in analysis_type.split('_')))
        if ans:
            s = SeriesEditor(plotter_options=opt)
            s.set_items(ans)

            s.component.use_backbuffer = False

            s = (self._new_paragraph(name),
                 ComponentFlowable(s.component),
                 self._page_break())
        else:
            s = (self._new_paragraph('No {}s'.format(name)), self._page_break())

        return s

    def _get_analyses(self, analysis_type):
        return [a for a in self._analyses if a.analysis_type == analysis_type]

# ============= EOF =============================================
