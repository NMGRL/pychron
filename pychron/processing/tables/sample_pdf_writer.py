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
import yaml
from pychron.core.pdf.base_table_pdf_writer import BasePDFTableWriter
from pychron.core.pdf.items import Row


class SamplePDFTableWriter(BasePDFTableWriter):
    yaml_options_path = None

    def _build(self, doc, samples, *args, **kw):
        """
        use a yaml file to configure table

        """
        self._load_yaml_options()
        flowables = [self._make_table_title(), self._make_sample_table(samples)]

        return flowables, None

    def _make_sample_table(self, samples):
        ts = self._new_style(header_line_idx=0, header_line_width=2)

        ts.add('LINEBELOW', (0, 1), (-1, -1), 1.0, colors.black)

        t = self._new_table(ts, list(self._row_generator(samples)))
        return t

    def _row_generator(self, samples):
        attrs = ['name', 'material', 'lithology', ('lat', '{:0.5f}'), ('lon', '{:0.5f}'), 'elevation']
        MATERIAL_MAP = {'Groundmass concentrate': 'GMC'}

        hr = Row()
        for ai in attrs:
            if len(ai) == 2:
                ai = ai[0]
            hr.add_item(value=ai.capitalize())
        yield hr

        for si in samples:
            if si.name.startswith('MB'):
                r = Row()
                for ai in attrs:
                    if len(ai) == 2:
                        ai, fmt = ai
                    else:
                        fmt = '{}'

                    v = getattr(si, ai)
                    if ai == 'material':
                        v = MATERIAL_MAP.get(v, v)

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

