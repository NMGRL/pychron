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

#============= enthought library imports =======================
# from traits.api import HasTraits
# from traitsui.api import View, Item
#============= standard library imports ========================
#============= local library imports  ==========================
# from pychron.core.pdf.base_pdf_writer import BasePDFWriter
# from pychron.loading.component_flowable import ComponentFlowable
# from reportlab.platypus.flowables import PageBreak
from pychron.processing.tasks.smart_project.interpolation_pdf_writer import InterpolationPDFWriter


class DetectorIntercalibrationPDFWriter(InterpolationPDFWriter):
    pass
#     def _build(self, doc, component, gs, refs):
#         flowables = [ComponentFlowable(component),
#                      PageBreak(),
#                      ]
#
#         templates = [self._new_page_template(frames=[self._default_frame(doc)])]
#
#         return flowables, templates
# ============= EOF =============================================
