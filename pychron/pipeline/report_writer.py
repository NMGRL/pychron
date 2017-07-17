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

from pychron.core.helpers.filetools import unique_path
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.core.pdf.items import Row
from pychron.core.pdf.options import BasePDFOptions
from pychron.loading.component_flowable import ComponentFlowable
from pychron.options.options_manager import SeriesOptionsManager, OptionsController, IdeogramOptionsManager
from pychron.options.views.views import view
from pychron.paths import paths
from pychron.persistence_loggable import dumpable
from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor
from pychron.pipeline.plot.editors.series_editor import SeriesEditor
from pychron.pipeline.plot.plotter.series import ATTR_MAPPING
from pychron.processing.analyses.analysis_group import AnalysisGroup


class BUReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'bu_report_series'


class AirReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'air_report_series'


class CocktailReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'cocktail_report_series'


class CocktailReportIdeogramOptionsManager(IdeogramOptionsManager):
    id = 'cocktail_report_ideogram'


class UnknownsReportSeriesOptionsManager(SeriesOptionsManager):
    id = 'unknowns_report_series'


class UnknownsReportIdeogramOptionsManager(IdeogramOptionsManager):
    id = 'unknowns_report_ideogram'


class ReportOptions(BasePDFOptions):
    _persistence_name = 'report_options'

    blank_unknowns_enabled = dumpable(Bool(True))
    airs_enabled = dumpable(Bool(True))
    cocktails_enabled = dumpable(Bool(True))
    blank_unknowns_enabled = dumpable(Bool(True))
    unknowns_enabled = dumpable(Bool(True))

    blank_unknowns_table_enabled = dumpable(Bool(True))
    airs_table_enabled = dumpable(Bool(True))
    cocktails_table_enabled = dumpable(Bool(True))
    blank_unknowns_table_enabled = dumpable(Bool(True))
    cocktail_ideogram_enabled = dumpable(Bool(True))
    unknowns_ideogram_enabled = dumpable(Bool(True))
    unknowns_table_enabled = dumpable(Bool(True))

    blank_unknowns_series_options_manager = Instance(BUReportSeriesOptionsManager, ())
    blank_unknowns_series_options_controller = Instance(OptionsController)

    airs_series_options_manager = Instance(AirReportSeriesOptionsManager, ())
    airs_series_options_controller = Instance(OptionsController)

    cocktails_series_options_manager = Instance(CocktailReportSeriesOptionsManager, ())
    cocktails_series_options_controller = Instance(OptionsController)

    cocktails_ideogram_options_manager = Instance(CocktailReportIdeogramOptionsManager, ())
    cocktails_ideogram_options_controller = Instance(OptionsController)

    unknowns_series_options_manager = Instance(UnknownsReportSeriesOptionsManager, ())
    unknowns_series_options_controller = Instance(OptionsController)

    unknowns_ideogram_options_manager = Instance(UnknownsReportIdeogramOptionsManager, ())
    unknowns_ideogram_options_controller = Instance(OptionsController)

    email_enabled = dumpable(Bool(True))

    def set_names(self, names):
        for a in ('blank_unknowns', 'airs', 'cocktails', 'unknowns'):
            m = getattr(self, '{}_series_options_manager'.format(a))
            m.set_names(names, clear_missing=False)

    @property
    def path(self):
        p, _ = unique_path(paths.report_dir, 'report', extension='.pdf')
        return p

    def traits_view(self):
        grps = []
        for at, name in (('blank_unknowns', 'Blank Unknowns'),
                         ('airs', 'Airs'),
                         ):
            grp = VGroup(Item('{}_enabled'.format(at), label='Enabled'),
                         Item('{}_table_enabled'.format(at), label='Table'),
                         UItem('{}_series_options_controller'.format(at),
                               style='custom',
                               enabled_when='{}_enabled'.format(at),
                               editor=InstanceEditor(view=view(name))),
                         label=name)
            grps.append(grp)

        sog = UItem('cocktails_series_options_controller',
                    style='custom',
                    enabled_when='cocktails_enabled',
                    editor=InstanceEditor(view=view(name)),
                    label='Series')
        iog = UItem('cocktails_ideogram_options_controller',
                    style='custom',
                    enabled_when='cocktails_enabled',
                    editor=InstanceEditor(view=view(name)),
                    label='Ideogram')

        cocktail_grp = VGroup(Item('cocktails_enabled', label='Enabled'),
                              Item('cocktails_table_enabled', label='Table'),
                              Tabbed(sog, iog),
                              label='Cocktails')

        grps.append(cocktail_grp)

        sog = UItem('unknowns_series_options_controller',
                    style='custom',
                    enabled_when='unknowns_enabled',
                    editor=InstanceEditor(view=view(name)),
                    label='Series')
        iog = UItem('unknowns_ideogram_options_controller',
                    style='custom',
                    enabled_when='unknowns_enabled',
                    editor=InstanceEditor(view=view(name)),
                    label='Ideogram')

        unk_grp = VGroup(Item('unknowns_enabled', label='Enabled'),
                         Item('unknowns_table_enabled', label='Table'),
                         Tabbed(sog, iog),
                         label='Unknowns')

        grps.append(unk_grp)

        layout_grp = self._get_layout_group()
        grps.append(layout_grp)

        v = View(Tabbed(*grps),
                 resizable=True,
                 title='Configure Report',
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

    def _cocktails_ideogram_options_controller_default(self):
        o = OptionsController(model=self.cocktails_ideogram_options_manager)
        return o

    def _unknowns_series_options_controller_default(self):
        o = OptionsController(model=self.unknowns_series_options_manager)
        return o

    def _unknowns_ideogram_options_controller_default(self):
        o = OptionsController(model=self.unknowns_ideogram_options_manager)
        return o


class ReportWriter(BasePDFTableWriter):
    _analyses = List
    options = Instance(ReportOptions)

    def make_report(self, analyses):
        self._analyses = analyses

        path = self.options.path
        self.build(path)
        # view_file(path)
        return path

    # private
    def _build(self, *args, **kw):
        flowables = []
        templates = None
        if self.options.blank_unknowns_enabled:
            f, _ = self._make_time_series('blank_unknown')
            flowables.extend(f)

        if self.options.airs_enabled:
            f, _ = self._make_time_series('air')
            flowables.extend(f)

        if self.options.cocktails_enabled:
            f, ag = self._make_time_series('cocktail')
            flowables.extend(f)
            if ag is not None:
                f = self._make_ideogram('cocktail', ag)
                flowables.extend(f)

        if self.options.unknowns_enabled:
            f, ag = self._make_time_series('unknown')
            flowables.extend(f)
            if ag is not None:
                f = self._make_ideogram('unknown', ag)
                flowables.extend(f)

        return flowables, templates

    def _make_ideogram(self, analysis_type, ag):
        opt = getattr(self.options, '{}s_ideogram_options_manager'.format(analysis_type)).selected_options
        # name = ' '.join((a.capitalize() for a in analysis_type.split('_')))
        pb = self._page_break()

        s = IdeogramEditor(plotter_options=opt)
        s.set_items(ag.analyses)
        s.component.use_backbuffer = False

        comp = ComponentFlowable(s.component, bounds=self.options.bounds)
        return comp, pb

    def _make_time_series(self, analysis_type, ):

        opt = getattr(self.options, '{}s_series_options_manager'.format(analysis_type)).selected_options

        ag = self._get_analyses(analysis_type)
        name = ' '.join((a.capitalize() for a in analysis_type.split('_')))
        pb = self._page_break()
        if ag:
            s = SeriesEditor(plotter_options=opt)
            s.set_items(ag.analyses)
            s.component.use_backbuffer = False

            table = self._make_summary_table(ag, opt)

            title = self._new_paragraph(name, s='Heading1')
            comp = ComponentFlowable(s.component, bounds=self.options.bounds)
            if getattr(self.options, '{}s_table_enabled'.format(analysis_type)):
                s = (title, table, comp, pb)
            else:
                s = (title, comp, pb)
        else:
            s = (self._new_paragraph('No {}s'.format(name)), pb)

        return s, ag

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
            r.add_item(value=stat['min'], fmt='{:0.4f}')
            r.add_item(value=stat['max'], fmt='{:0.4f}')
            r.add_item(value=stat['total_dev'], fmt='{:0.4f}')
            rows.append(r)

            if i % 2 == 0:
                bg_color = colors.whitesmoke
            else:
                bg_color = colors.lightgrey

            ts.add('BACKGROUND', (0, i + 1), (-1, i + 1), bg_color)

        table = self._new_table(ts, rows)
        return table

    def _get_analyses(self, analysis_type):
        ans = [a for a in self._analyses if a.analysis_type == analysis_type]
        # return ans
        if ans:
            return AnalysisGroup(analyses=ans)

# ============= EOF =============================================
