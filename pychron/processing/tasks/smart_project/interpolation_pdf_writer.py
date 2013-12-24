#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================

from datetime import datetime

from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus.flowables import PageBreak

from pychron.core.pdf.base_pdf_writer import BasePDFWriter
from pychron.loading.component_flowable import ComponentFlowable

#============= standard library imports ========================
#============= local library imports  ==========================

class InterpolationPDFWriter(BasePDFWriter):

    def _build(self, doc, component, unknowns, blanks, collate=True):
        '''
            needs to return 
                flowables, templates
                
            flowables: Flowable list
            templates: PageTemplate list
        '''
        flowables = [ComponentFlowable(component),
                     PageBreak(),
                     ]
        ts = self._new_style(header_line_idx=1, header_line_width=2)
        ts.add('SPAN', (0, 0), (-1, 0))

        if collate:
            unknowns.extend(blanks)
            ans = sorted(unknowns, key=lambda x: x.timestamp)

            bidx = [i for i, ai in enumerate(ans)
                    if ai.analysis_type.startswith('blank')]

            for bi in bidx:
                ts.add('BACKGROUND', (0, bi + 2), (-1, bi + 2), colors.lightgrey)

            ai = unknowns[0]
            title = ' '.join(map(str.capitalize, ai.analysis_type.split('_')))
            t = self._make_table(ans, ts, title)
            flowables.append(t)

        else:
            for ans in (unknowns, blanks):
                ai = ans[0]
                title = ' '.join(map(str.capitalize, ai.analysis_type.split('_')))
                t = self._make_table(ans, ts, title)

                flowables.append(t)
                flowables.append(self._new_spacer(0, 0.5))

#         frames = [self._default_frame(doc)]
#         template = self._new_page_template(frames)

        return flowables, None

    def _make_table(self, ans, style, title):
        rows = [(ai.record_id, datetime.fromtimestamp(ai.timestamp))
                        for ai in ans]

        data = [(self._new_paragraph('<b>Table X.</b> {}'.format(title)), ''),
                ('RunID', 'Time'), ]

        data.extend(rows)
        t = self._new_table(style, data,
                            colWidths=[1.5 * inch, 2 * inch],
                            hAlign='LEFT')
        return t
#============= EOF =============================================
