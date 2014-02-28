#===============================================================================
# Copyright 2014 Jake Ross
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

from reportlab.lib import colors
from traits.api import HasTraits, Str, Date, Float


#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.core.helpers.filetools import view_file
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.core.pdf.items import Row
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.paths import paths


class Irradiation(HasTraits):
    name = Str
    date = Date
    duration = Float
    reactor = Str

    def __init__(self, dbrecord, *args, **kw):
        super(Irradiation, self).__init__(*args, **kw)
        self.name = dbrecord.name

        #calculate duration
        self.duration = dbrecord.chronology.duration
        self.reactor = dbrecord.reactor.name.replace('&', '&amp;')


class IrradiationTableWriter(IsotopeDatabaseManager):
    def make(self):
        root = os.path.join(paths.dissertation, 'data', 'minnabluff', 'irradiations')
        p = os.path.join(root, 'irradiations.yaml')
        with open(p, 'r') as fp:
            yd = yaml.load(fp)

        db = self.db
        irrads = []
        with db.session_ctx():
            for yi in yd:
                dbirrad = db.get_irradiation(yi)
                irrads.append(Irradiation(dbirrad))

        outpath = os.path.join(root, 'irradiations.pdf')
        p = PDFWriter()
        p.build(outpath, irrads)
        view_file(outpath)


class PDFWriter(BasePDFTableWriter):
    def _build(self, doc, irradiations, *args, **kw):
        flowables = []
        templates = []

        flowables.append(self._make_table_title())
        flowables.append(self._make_table(irradiations))
        return flowables, templates or None

    def _make_table(self, irrads):
        ts = self._new_style(header_line_idx=0, header_line_width=2)

        ts.add('LINEBELOW', (0, 1), (-1, -1), 1.0, colors.black)

        header = Row()
        header.add_item(value='Irradiation')
        header.add_item(value='Duration')
        header.add_item(value='Reactor')

        rows = [header]
        for i in irrads:
            r = Row()
            r.add_item(value=i.name)
            r.add_item(value='{:0.1f}'.format(i.duration))
            r.add_item(value=i.reactor)
            rows.append(r)

        t = self._new_table(ts, rows)
        return t

    def _make_table_title(self):
        t = 'Table X. Irradiations'
        p = self._new_paragraph(t, s='Heading1')
        return p

#============= EOF =============================================
