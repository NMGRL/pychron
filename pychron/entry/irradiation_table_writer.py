# ===============================================================================
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
# ===============================================================================
# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Float
# ============= standard library imports ========================
from reportlab.lib import colors
# ============= local library imports  ==========================
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.core.pdf.items import Row


class Irradiation(HasTraits):
    name = Str
    date = Str
    duration = Float
    reactor = Str

    def __init__(self, dbrecord, *args, **kw):
        super(Irradiation, self).__init__(*args, **kw)
        self.name = dbrecord.name

        self.date = dbrecord.chronology.start_date
        self.duration = dbrecord.chronology.duration
        self.reactor = dbrecord.reactor.name.replace('&', '&amp;')


class PDFWriter(BasePDFTableWriter):
    def _build(self, doc, irradiations, *args, **kw):
        flowables = []
        templates = []

        flowables.append(self._make_table_title())
        flowables.append(self._make_table(irradiations))
        flowables.append(self._make_notes())
        return flowables, templates or None

    def _make_notes(self):
        t = """
Texas A&amp;M=  1 MW TRIGA Reactor. Nuclear Science Center, Texas A&amp;M University, College Station, TX. http://nsc.tamu.edu/about-the-nsc/
<br/>
USGS Denver= 1 MW TRIGA Reactor. U.S. Geological Survey, Lakewood, CO. http://pubs.usgs.gov/fs/2012/3093/"""
        p = self._new_paragraph(t, backColor='lightgrey', fontSize=6)
        return p

    def _make_table(self, irrads):
        ts = self._new_style(header_line_idx=0, header_line_width=2)

        ts.add('LINEBELOW', (0, 1), (-1, -1), 1.0, colors.black)

        header = Row()
        header.add_item(value='<b>Irradiation</b>')
        header.add_item(value='<b>Date</b>')
        header.add_item(value='<b>Duration (hr)</b>')
        header.add_item(value='<b>Reactor</b>')

        rows = [header]
        for i in irrads:
            r = Row()
            r.add_item(value=i.name)
            r.add_item(value=i.date)
            r.add_item(value='{:0.1f}'.format(i.duration))
            r.add_item(value=i.reactor)
            rows.append(r)

        t = self._new_table(ts, rows)
        return t

    def _make_table_title(self):
        t = '<b>Table X. Irradiations</b>'
        # p = self._new_paragraph(t, s='Heading1')
        p = self._new_paragraph(t)
        return p

# ============= EOF =============================================
# class IrradiationTableWriter(IsotopeDatabaseManager):
#     def make(self):
#         root = os.path.join(paths.dissertation, 'data', 'minnabluff', 'irradiations')
#         p = os.path.join(root, 'irradiations.yaml')
#         with open(p, 'r') as rfile:
#             yd = yaml.load(rfile)
#
#         db = self.db
#         irrads = []
#         with db.session_ctx():
#             for yi in yd:
#                 dbirrad = db.get_irradiation(yi)
#                 irrads.append(Irradiation(dbirrad))
#
#         outpath = os.path.join(root, 'irradiations.pdf')
#         p = PDFWriter()
#         opt = p.options
#         opt.orientation = 'portrait'
#         p.build(outpath, irrads)
#         view_file(outpath)
#

#
# if __name__ == '__main__':
#     i = IrradiationTableWriter(bind=False, connect=False)
#     i.db.trait_set(name='pychrondata_minnabluff',
#                    kind='mysql',
#                    username='root',
#                    password='Argon')
#     i.connect()
#     i.make()
