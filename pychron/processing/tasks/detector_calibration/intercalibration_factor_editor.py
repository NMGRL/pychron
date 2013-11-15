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
from traits.api import Instance
from pychron.pychron_constants import IC_ANALYSIS_TYPE_MAP
from pychron.processing.tasks.analysis_edit.interpolation_editor import InterpolationEditor
#============= standard library imports ========================
from numpy import array
from pychron.helpers.isotope_utils import sort_detectors
#============= local library imports  ==========================
from pychron.processing.tasks.detector_calibration.detector_calibration_tool import DetectorCalibrationTool


class IntercalibrationFactorEditor(InterpolationEditor):
    standard_ratio = 1.0
    tool = Instance(DetectorCalibrationTool)
    auto_find = False
    pickle_path = 'ic_fits'

    def save(self):
        if not any([si.valid for si in self.tool.fits]):
            return

        db = self.processor.db
        with db.session_ctx():
            cname = 'detector_intercalibration'
            self.info('Attempting to save corrections to database')

            for unk in self.unknowns:
                meas_analysis = db.get_analysis_uuid(unk.uuid)

                histories = getattr(meas_analysis, '{}_histories'.format(cname))
                phistory = histories[-1] if histories else None
                history = self.processor.add_history(meas_analysis, cname)
                for si in self.tool.fits:
                    if si.valid:
                        self.debug('saving {} {}'.format(unk.record_id, si.name))
                        self.processor.apply_correction(history, unk, si,
                                                        self._clean_references(), cname)

                unk.sync(meas_analysis)

                #if not si.use:
                #    self.debug('using previous value {} {}'.format(unk.record_id, si.name))
                #    self.processor.apply_fixed_value_correction(phistory, history, si, cname)
                #else:
                #    self.debug('saving {} {}'.format(unk.record_id, si.name))
                #    self.processor.apply_correction(history, unk, si,
                #                                    self.references, cname)

    def _tool_default(self):
        with self.processor.db.session_ctx():
            atypes = [ai.name for ai in self.processor.db.get_analysis_types()]
            ntypes = ['']
            for ai in atypes:
                if ai in IC_ANALYSIS_TYPE_MAP:
                    idx = IC_ANALYSIS_TYPE_MAP[ai]
                    while idx > len(ntypes):
                        ntypes.append('')

                    ntypes[idx] = ai
                else:
                    ntypes.append(ai)

            tool = DetectorCalibrationTool()
            tool.analysis_types = ntypes

            dets = [det.name for det in self.processor.db.get_detectors()]
            tool.detectors = sort_detectors(dets)

            return tool

    def _update_references_hook(self):
        pass

    def _load_refiso(self, refiso):
        #keys = refiso.isotope_keys
        dets = [iso.detector for iso in refiso.isotopes.itervalues()]
        dets = sort_detectors(dets)

        self.tool.detectors = dets

    def _set_interpolated_values(self, iso, reg, xs):
        p_uys = reg.predict(xs)
        p_ues = reg.predict_error(xs, error_calc=self.tool.error_calc.lower())

        _, d = iso.split('/')
        for ui, v, e in zip(self.sorted_unknowns, p_uys, p_ues):
            ui.set_temporary_ic_factor(d, v, e)

        return p_uys, p_ues

    def _get_reference_values(self, dets):
        n, d = dets.split('/')
        nys = array([ri.get_isotope(detector=n).uvalue for ri in self.references])
        dys = array([ri.get_isotope(detector=d).uvalue for ri in self.references])
        try:
            rys = (nys / dys) / self.tool.standard_ratio
            return zip(*[(ri.nominal_value, ri.std_dev) for ri in rys])
        except ZeroDivisionError:
            return None, None

            #rys = [ri.nominal_value for ri in rys]
            #return rys, None

    def _get_current_values(self, dets):
        #return None, None
        n, d = dets.split('/')
        nys = array([ri.get_ic_factor(n) for ri in self.unknowns])
        dys = array([ri.get_ic_factor(d) for ri in self.unknowns])
        try:
            rys = dys / nys
            return zip(*[(ri.nominal_value, ri.std_dev) for ri in rys])
        except ZeroDivisionError:
            return None, None


            #============= EOF =============================================
