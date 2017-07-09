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
from reportlab.lib import colors
from traits.api import Bool, List, Instance
from traitsui.api import View, UItem, Item, VGroup, InstanceEditor, Tabbed

from pychron.core.helpers.filetools import unique_path, view_file
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.core.pdf.items import Row
from pychron.core.pdf.options import BasePDFOptions
from pychron.loading.component_flowable import ComponentFlowable
from pychron.options.options_manager import SeriesOptionsManager, OptionsController
from pychron.options.views.views import view
from pychron.paths import paths
from pychron.persistence_loggable import dumpable
from pychron.pipeline.plot.editors.series_editor import SeriesEditor
from pychron.pipeline.plot.plotter.series import ATTR_MAPPING
from pychron.processing.analyses.analysis_group import AnalysisGroup


class BUReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'bu_report_series'


class AirReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'air_report_series'


class CocktailReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'cocktail_report_series'


class ReportOptions(BasePDFOptions):
    _persistence_name = 'report_options'

    blank_unknowns_enabled = dumpable(Bool(True))
    airs_enabled = dumpable(Bool(True))
    cocktails_enabled = dumpable(Bool(True))
    blank_unknowns_enabled = dumpable(Bool(True))

    blank_unknowns_series_options_manager = Instance(BUReportSeriesOptionsManager, ())
    blank_unknowns_series_options_controller = Instance(OptionsController)

    airs_series_options_manager = Instance(AirReportSeriesOptionsManager, ())
    airs_series_options_controller = Instance(OptionsController)

    cocktails_series_options_manager = Instance(CocktailReportSeriesOptionsManager, ())
    cocktails_series_options_controller = Instance(OptionsController)

    def set_names(self, names):
        self.blank_unknowns_series_options_manager.set_names(names)
        self.airs_series_options_manager.set_names(names)
        self.cocktails_series_options_manager.set_names(names)

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

        cocktail_grp = VGroup(Item('cocktails_enabled', label='Enabled'),
                              UItem('cocktails_series_options_controller',
                                    editor=InstanceEditor(view=view('Cocktails')),
                                    style='custom',
                                    enabled_when='cocktails_enabled'),
                              label='Cocktails')

        layout_grp = self._get_layout_group()
        v = View(Tabbed(bu_grp, air_grp, cocktail_grp, layout_grp),
                 buttons=['OK', 'Cancel'])
        return v

    def _blank_unknowns_series_options_controller_default(self):
        o = OptionsController(model=self.blank_unknowns_series_options_manager)
        return o

    def _airs_series_options_controller_default(self):
        o = OptionsController(model=self.airs_series_options_manager)
        return o

    def _cocktails_series_options_controller_default(self):
        o = OptionsController(model=self.cocktails_series_options_manager)
        return o


class ReportWriter(BasePDFTableWriter):
    _analyses = List
    options = Instance(ReportOptions)

    def make_report(self, analyses):
        self._analyses = analyses

        path = self.options.path
        self.build(path)
        view_file(path)

    # private
    def _build(self, *args, **kw):
        flowables = []
        templates = None
        if self.options.blank_unknowns_enabled:
            f = self._make_time_series('blank_unknown')
            flowables.extend(f)

        if self.options.airs_enabled:
            f = self._make_time_series('air')
            flowables.extend(f)

        if self.options.cocktails_enabled:
            f = self._make_time_series('cocktail')
            flowables.extend(f)

        return flowables, templates

    def _make_time_series(self, analysis_type, ):

        opt = getattr(self.options, '{}s_series_options_manager'.format(analysis_type)).selected_options

        ag = self._get_analyses(analysis_type)
        name = ' '.join((a.capitalize() for a in analysis_type.split('_')))
        if ag:
            s = SeriesEditor(plotter_options=opt)
            s.set_items(ag.analyses)
            s.component.use_backbuffer = False

            table = self._make_summary_table(ag, opt)

            s = (self._new_paragraph(name, s='Heading1'),
                 ComponentFlowable(s.component, bounds=self.options.bounds),
                 table,
                 self._page_break())
        else:
            s = (self._new_paragraph('No {}s'.format(name)), self._page_break())

        return s

    def _make_summary_table(self, ag, opt):

        # ag = editor.analysis_groups[0]

        ts = self._new_style(header_line_idx=0, header_line_width=2)

        ts.add('LINEBELOW', (0, 1), (-1, -1), 1.0, colors.black)

        header = Row()
        header.add_item(value='Attr')
        header.add_item(value='Mean')
        header.add_item(value='SD')
        header.add_item(value='SEM')
        header.add_item(value='MSWD')
        header.add_item(value='Min')
        header.add_item(value='Max')
        header.add_item(value='Dev %')

        rows = [header]
        for i, attr in enumerate(opt.get_plotable_aux_plots()):
            name = key = attr.name
            if name in ATTR_MAPPING:
                key = ATTR_MAPPING[name]
            stat = ag.attr_stats(key)

            r = Row()
            r.add_item(value=name)
            r.add_item(value=stat['mean'], fmt='{:0.4f}')
            r.add_item(value=stat['sd'], fmt='{:0.4f}')
            r.add_item(value=stat['sem'], fmt='{:0.4f}')
            r.add_item(value='{}{}'.format('{:0.4f}'.format(stat['mswd']),
                                           '' if stat['valid_mswd'] else '*'))
            r.add_item(value=stat['max'], fmt='{:0.4f}')
            r.add_item(value=stat['min'], fmt='{:0.4f}')
            r.add_item(value=stat['total_dev'], fmt='{:0.4f}')
            rows.append(r)

            if i % 2 == 0:
                bg_color = colors.whitesmoke
            else:
                bg_color = colors.lightgrey

            ts.add('BACKGROUND', (0, i+1), (-1, i+1), bg_color)

        table = self._new_table(ts, rows)
        return table

    def _get_analyses(self, analysis_type):
        ans = [a for a in self._analyses if a.analysis_type == analysis_type]
        # return ans
        if ans:
            return AnalysisGroup(analyses=ans)

# ============= EOF =============================================
