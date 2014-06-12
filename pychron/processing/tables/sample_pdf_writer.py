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
#===============================================================================

#============= enthought library imports =======================
import os

from reportlab.lib import colors


#============= standard library imports ========================
#============= local library imports  ==========================
from reportlab.lib.units import inch
import yaml
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.core.pdf.items import Row, FooterRow

rock_type_map = {'L': 'Lava',
                 'LAg': 'Lava/Agglutinate',
                 'L(gl)': 'Lava glassy',
                 'B': 'Autobreccia',
                 'B(gl)': 'Hyaloclastite Breccia',
                 'D': 'Dike',
                 'VZI': 'Vent zone intrusion',
                 'T': 'Pyroclastic Tuff or Lapilli Tuff',
                 'S': 'Polymict sediment',
                 'T(gl)': 'Hydrovolcanic tuff'}

class SamplePDFTableWriter(BasePDFTableWriter):
    yaml_options_path = None

    def _build(self, doc, samples, *args, **kw):
        """
        use a yaml file to configure table

        """
        self._load_yaml_options()
        self.col_widths = [0.75 * inch,
                           0.75 * inch,
                           0.95 * inch,
                           0.75 * inch,
                           0.75 * inch,
                           0.75 * inch,
                           0.95 * inch, ]

        st = self._make_sample_table(samples)
        # st._argW[0]=0.7*inch
        # st._argW[1]=0.7*inch
        # st._argW[2]=0.9*inch
        # st._argW[3]=0.7*inch
        # st._argW[4]=0.7*inch
        # st._argW[5]=0.7*inch
        # st._argW[6]=0.7*inch

        flowables = [self._make_table_title(), st,
                     self._vspacer(0.1),
                     self._make_footnote_table()]

        return flowables, None

    def _make_footnote_table(self):
        style = self._new_style(debug_grid=False)
        style.add('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey)

        l = ', '.join(['{}= {}'.format(k, v) for k, v in rock_type_map.items()[:5]])
        l2 = ', '.join(['{}= {}'.format(k, v) for k, v in rock_type_map.items()[5:9]])
        l3 = ', '.join(['{}= {}'.format(k, v) for k, v in rock_type_map.items()[9:]])
        r = FooterRow(fontsize=7)
        r.add_item(value='Rock Types: {}'.format(l), span=7)

        r2 = FooterRow(fontsize=7)
        r2.add_blank_item(1)
        r2.add_item(value=l2, span=6)

        r3 = FooterRow(fontsize=7)
        r3.add_blank_item(1)
        r3.add_item(value=l3, span=6)

        r4 = FooterRow(fontsize=7)
        r4.add_item(value='Materials: GMC= Groundmass Concentrate', span=7)
        fdata = [r, r2, r3, r4]
        ft = self._new_table(style, fdata)
        return ft

    def _make_sample_table(self, samples):
        ts = self._new_style(header_line_idx=0, header_line_width=2)

        ts.add('LINEBELOW', (0, 1), (-1, -1), 1.0, colors.black)

        t = self._new_table(ts, list(self._row_generator(samples)))
        return t

    def _row_generator(self, samples):
        attrs = ['name', 'material', 'lithology', 'rock_type', ('lat', '{:0.5f}'), ('lon', '{:0.5f}'),
                 ('elevation', '{}', 'm')]
        MATERIAL_MAP = {'Groundmass concentrate': 'GMC'}

        hr = Row()
        for ai in attrs:
            if isinstance(ai, tuple):
                if len(ai) == 2:
                    ai = ai[0]
                elif len(ai) == 3:
                    ai = '{} ({})'.format(ai[0], ai[2])

            h = ' '.join(map(str.capitalize, ai.split('_')))
            hr.add_item(value=h)

        yield hr

        for si in samples:
            if si.name.startswith('MB'):
                r = Row()
                for ai in attrs:
                    fmt = '{}'
                    if isinstance(ai, tuple):
                        if len(ai) == 2:
                            ai, fmt = ai

                        elif len(ai) == 3:
                            ai, fmt, u = ai

                    v = getattr(si, ai)
                    if ai == 'material':
                        v = MATERIAL_MAP.get(v, v)
                    if ai == 'elevation':
                        v = int(v)

                    if not v:
                        v = '-'
                    else:
                        v = fmt.format(v)
                    r.add_item(value=v)

                yield r

    def _make_table_title(self):
        title = 'Sample Table'
        if self._yaml_options:
            title = self._yaml_options.get('title', title)

        return self._new_paragraph(title)

    def _load_yaml_options(self):
        if self.yaml_options_path:
            if os.path.isfile(self.yaml_options_path):
                with open(self.yaml_options_path, 'r') as fp:
                    try:
                        self._yaml_options = yaml.load(fp)
                    except yaml.YAMLError:
                        pass

#============= EOF =============================================

