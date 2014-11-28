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
from datetime import timedelta
#============= local library imports  ==========================
from pychron.processing.tasks.smart_project.base_smarter import BaseSmarter
from pychron.core.helpers.filetools import unique_path
from pychron.processing.tasks.smart_project.detector_intercalibration_pdf_writer import DetectorIntercalibrationPDFWriter

class SmartDetectorIntercalibration(BaseSmarter):

    def set_user_value(self, analysis, v, e):
        pass

    def fit_detector_intercalibration(self, n, ans, fit, reftype, root, save_figure,
                                      with_table):
        func = self._do_detector_intercalibration
        args = (fit, reftype, root, save_figure, with_table)
        self._block_analyses(n, ans, func, args)

    def _do_detector_intercalibration(self, gs, fit, reftype, root,
                                      save_figure, with_table):

        start, end = gs[0].analysis_timestamp, gs[-1].analysis_timestamp

        ds = timedelta(hours=3)

        refs = self._get_analysis_date_range(start - ds, end + ds, (reftype,))
        if refs:
            man = self.processor
            refs = man.make_analyses(refs)
            gs = man.make_analyses(gs)
            man.load_analyses(gs, show_progress=False)
            man.load_analyses(refs, show_progress=False)

            refiso = gs[0]

            ae = self.editor
#             ae.tool.load_fits(ks, fs)
            ae.tool.load_fits(['Ar40/Ar36'], [fit])

            ae.tool.fits[0].show = True
#             fkeys = fits.keys()
#             for fi in ae.tool.fits:
#                 if fi.name in fkeys:
#                     fi.trait_set(show=True, fit=fits[fi.name], trait_change_notify=False)

            ae.unknowns = gs
            ae.references = refs
            ae.rebuild_graph()

            if save_figure:
                p, _ = unique_path(root, base=refiso.record_id,
                                   extension='.pdf')
                if with_table:
                    writer = DetectorIntercalibrationPDFWriter()
                    writer.build(p, ae.component, gs, refs)
                else:
                    ae.graph.save_pdf(p)
# ============= EOF =============================================
