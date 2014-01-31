#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import List, Callable
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.graph.tools.point_inspector import PointInspector

class AnalysisPointInspector(PointInspector):
    analyses = List
    value_format = Callable
    additional_info = Callable


    def assemble_lines(self):
        lines = []
        if self.current_position:
            inds = self.get_selected_index()
            if inds is not None:
                for ind in inds:
                    analysis = self.analyses[ind]

                    rid = analysis.record_id
                    name = self.component.container.y_axis.title

                    y = self.component.value.get_data()[ind]

                    if hasattr(self.component, 'yerror'):
                        ye = self.component.yerror.get_data()[ind]
                        pe=self.percent_error(y,ye)
                        if self.value_format:
                            ye=self.value_format(ye)
                        if self.value_format:
                            y = self.value_format(y)

                        y='{} +/-{} {}'.format(y,ye, pe)
                    else:
                        if self.value_format:
                            y = self.value_format(y)

                        #                 if analysis.status == 0 and analysis.temp_status != 0:
                        #                     status = 'Temp. Omitted'
                        #                 else:
                    status = analysis.status_text
                    tag = analysis.tag

                    lines.extend(['Analysis= {}'.format(rid),
                             'Status= {}'.format(status),
                             'Tag= {}'.format(tag),
                             '{}= {}'.format(name, y)])

                    if self.additional_info is not None:
                        lines.append(self.additional_info(analysis))
                    lines.append('           ')

                #remove last new line
                lines=lines[:-1]

        return lines

#============= EOF =============================================
