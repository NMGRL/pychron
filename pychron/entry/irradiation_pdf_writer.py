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

# ============= enthought library imports =======================
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from traits.api import Bool, Float
from traitsui.api import View, VGroup, Tabbed, Item

from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.core.pdf.items import Row
from pychron.core.pdf.options import BasePDFOptions, dumpable
from pychron.dvc.meta_repo import irradiation_holder_holes, irradiation_chronology
from pychron.entry.editors.level_editor import load_holder_canvas
from pychron.loading.component_flowable import ComponentFlowable


class RotatedParagraph(Paragraph):
    rotation = 0

    def draw(self):
        self.canv.saveState()

        self.canv.rotate(self.rotation)
        self.canv.translate(-self.width / 2. - 100, -self.height)
        Paragraph.draw(self)
        self.canv.restoreState()


class IrradiationPDFTableOptions(BasePDFOptions):
    status_width = dumpable(Float(0.25))
    position_width = dumpable(Float(0.5))
    identifier_width = dumpable(Float(0.6))
    sample_width = dumpable(Float(1.25))
    material_width = dumpable(Float(0.5))
    project_width = dumpable(Float(1.25))

    only_selected_level = dumpable(Bool(False))

    _persistence_name = 'irradiation_pdf_table_options'

    def widths(self, units=inch):
        return [getattr(self, '{}_width'.format(w)) * units for w in ('status', 'position', 'identifier', 'sample',
                                                                      'material',
                                                                      'project')]

    def traits_view(self):
        layout_grp = self._get_layout_group()
        layout_grp.show_border = False
        width_grp = VGroup(Item('status_width', label='Status (in)'),
                           Item('position_width', label='Pos. (in)'),
                           Item('identifier_width', label='L# (in)'),
                           Item('sample_width', label='Sample (in)'),
                           Item('material_width', label='Material (in)'),
                           Item('project_width', label='Project (in)'),
                           label='Column Widths')

        main_grp = VGroup(Item('only_selected_level',
                               label='Only Selected Level'),
                          label='Main')

        v = View(Tabbed(main_grp,
                        layout_grp,
                        width_grp),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 title='PDF Save Options',
                 resizable=True)
        return v


class IrradiationPDFWriter(BasePDFTableWriter):
    page_break_between_levels = Bool(True)
    show_page_numbers = True

    selected_level = None
    _options_klass = IrradiationPDFTableOptions

    def _build(self, doc, irrad, *args, **kw):
        if not self.options.only_selected_level:
            self.options.page_number_format = '{} {{page:d}} - {{total:d}}'.format(irrad.name)
        flowables = self._make_levels(irrad)
        return flowables, None

    def _make_levels(self, irrad, progress=None):
        irradname = irrad.name

        flowables = []
        if self.options.only_selected_level:
            levels = [l for l in irrad.levels if l.name == self.selected_level]
        else:
            # make coversheet
            summary = self._make_summary(irrad)
            summary_table = self._make_summary_table(irrad)

            flowables = [summary, self._vspacer(1), summary_table, self._page_break()]

            levels = sorted(irrad.levels, key=lambda x: x.name)

        for level in levels:
            if progress is not None:
                progress.change_message('Making {}{}'.format(irradname, level.name))

            c = self._make_canvas(level)
            fs = self._make_level_table(irrad, level, c)
            if c:
                c = ComponentFlowable(c)
                flowables.append(self._make_table_title(irrad, level))
                flowables.append(c)
                flowables.append(self._page_break())

            flowables.extend(fs)

        return flowables

    def _make_summary(self, irrad):
        fontsize = lambda x, f: '<font size={}>{}</font>'.format(f, x)

        name = irrad.name
        levels = ', '.join(sorted([li.name for li in irrad.levels]))

        chron = irradiation_chronology(name)
        dur = chron.total_duration_seconds
        date = chron.start_date

        dur /= (60 * 60.)
        date = 'Irradiation Date: {}'.format(date)
        dur = 'Irradiation Duration: {:0.1f} hrs'.format(dur)

        name = fontsize(name, 40)
        txt = '<br/>'.join((name, levels, date, dur))

        klass = Paragraph
        rotation = 0
        if self.options.orientation == 'landscape':
            klass = RotatedParagraph
            rotation = 90

        p = self._new_paragraph(txt,
                                klass=klass,
                                s='Title',
                                textColor=colors.black,
                                alignment=TA_CENTER)
        p.rotation = rotation
        return p

    def _make_summary_table(self, irrad):
        ts = self._new_style(header_line_idx=0)
        header = Row()
        header.add_item(value='<b>Level</b>')
        header.add_item(value='<b>Tray</b>')

        def make_row(level):
            row = Row()
            row.add_item(value=level.name)
            row.add_item(value=level.holder)
            return row

        rows = [make_row(li) for li in sorted(irrad.levels, key=lambda x: x.name)]
        rows.insert(0, header)

        t = self._new_table(ts, rows, col_widths=[1*inch, 2*inch])
        return t

    def _make_level_table(self, irrad, level, c):
        row = Row()
        row.add_item(span=-1, value=self._make_table_title(irrad, level), fontsize=18)
        rows = [row]

        row = Row()
        for v in ('', 'Pos.', 'L#', 'Sample', 'Material', 'Project', 'PI', 'Note'):
            row.add_item(value=self._new_paragraph('<b>{}</b>'.format(v)))
        rows.append(row)

        srows = []
        spos = sorted(level.positions, key=lambda x: x.position)
        for i in xrange(c.scene.nholes):
            pos = i + 1
            item = next((p for p in spos if p.position == pos), None)
            if not item:
                row = self._make_blank_row(pos)
            else:
                row = self._make_row(item, c)
                spos.remove(item)
            srows.append(row)

        rows.extend(srows)

        ts = self._new_style(header_line_idx=0, header_line_width=2)

        ts.add('LINEBELOW', (0, 1), (-1, -1), 1.0, colors.black)

        cw = self.options.widths()
        t = self._new_table(ts, rows, colWidths=cw)
        t.repeatRows = 2

        flowables = [t]
        if self.page_break_between_levels:
            flowables.append(self._page_break())
        else:
            flowables.append(self._new_spacer(0, 0.25 * inch))
        return flowables

    def _make_table_title(self, irrad, level):
        t = '{}{} {}'.format(irrad.name, level.name, level.holder)
        p = self._new_paragraph(t, s='Heading1', alignment=TA_CENTER)
        return p

    def _make_blank_row(self, pos):
        r = Row()
        r.add_item(value='[  ]')
        r.add_item(value=pos)
        for i in xrange(6):
            r.add_item(value='')

        return r

    def _make_row(self, pos, canvas):
        r = Row()
        sample = pos.sample
        project, pi, material = '', '', ''
        if sample:
            if sample.material:
                material = sample.material.name[:15]
            project = sample.project.name
            pi = sample.project.principal_investigator.name
            sample = sample.name
            if sample == 'FC-2':
                project, pi, material = '', '', ''

        r.add_item(value='[  ]')
        r.add_item(value=pos.position)
        r.add_item(value=pos.identifier or '')
        r.add_item(value=sample or '')
        r.add_item(value=material, fontsize=8)
        r.add_item(value=project)
        r.add_item(value=pi)
        r.add_item(value='')

        if sample:
            item = canvas.scene.get_item(pos.position)
            item.fill = True

        return r

    def _make_canvas(self, level):
        if level.holder:
            holes = irradiation_holder_holes(level.holder)
            canvas = IrradiationCanvas()
            load_holder_canvas(canvas, holes)
            return canvas


class LabbookPDFWriter(IrradiationPDFWriter):
    def _build(self, doc, irrads, progress=None, *args, **kw):
        flowables = []

        flowables.extend(self._make_title_page(irrads))

        for irrad in irrads:
            self.options.page_number_format = '{} {{page:d}} - {{total:d}}'.format(irrad.name)
            fs, _ = self._make_levels(irrad, progress)
            flowables.extend(self._make_summary(irrad))

            flowables.extend(fs)

        return flowables, None

    def _make_title_page(self, irrads):
        start = irrads[0].name
        end = irrads[-1].name
        l1 = 'New Mexico Geochronology Research Laboratory'
        l2 = 'Irradiation Labbook'
        if start != end:
            l3 = '{} to {}'.format(start, end)
        else:
            l3 = start

        t = '<br/>'.join((l1, l2, l3))
        p = self._new_paragraph(t, s='Title')
        return p, self._page_break()

    def _make_summary(self, irrad):
        fontsize = lambda x, f: '<font size={}>{}</font>'.format(f, x)

        name = irrad.name
        levels = ', '.join(sorted([li.name for li in irrad.levels]))

        chron = irradiation_chronology(name)
        dur = chron.total_duration_seconds
        date = chron.start_date

        # dur = 0
        # if chron:
        #     doses = chron.get_doses()
        #     for pwr, st, en in doses:
        #         dur += (en - st).total_seconds()
        #     _, _, date = chron.get_doses(todatetime=False)[-1]

        dur /= (60 * 60.)
        date = 'Irradiation Date: {}'.format(date)
        dur = 'Irradiation Duration: {:0.1f} hrs'.format(dur)

        name = fontsize(name, 40)
        # levels = fontsize(levels, 28)
        # dur = fontsize(dur, 28)
        txt = '<br/>'.join((name, levels, date, dur))
        p = self._new_paragraph(txt,
                                s='Title',
                                textColor=colors.green,
                                alignment=TA_CENTER)

        return p, self._page_break()

# ============= EOF =============================================
