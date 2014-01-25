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
from pychron.pychron_constants import IC_ANALYSIS_TYPE_MAP
from pychron.processing.tasks.analysis_edit.interpolation_editor import InterpolationEditor
#============= standard library imports ========================
from numpy import array
from pychron.core.helpers.isotope_utils import sort_detectors
#============= local library imports  ==========================
from pychron.processing.tasks.detector_calibration.detector_calibration_tool import DetectorCalibrationTool


class IntercalibrationFactorEditor(InterpolationEditor):
    standard_ratio = 1.0
    # tool_klass =
    # tool = Instance(DetectorCalibrationTool)
    auto_find = False
    pickle_path = 'ic_fits'

    def _get_dump_tool(self):
        return self.tool.fits

    def save(self, progress=None):
        fs = [si for si in self.tool.fits if si.save]
        if not fs:
            return

        db = self.processor.db

        with db.session_ctx():
            cname = 'detector_intercalibration'
            self.info('Attempting to save corrections to database')

            n=len(self.analyses)
            if n>1:
                if progress is None:
                    progress=self.processor.open_progress(n)
                else:
                    progress.increase_max(n)

            set_id=self.processor.add_predictor_set(self._clean_references())

            for unk in self.analyses:
                if progress:
                    progress.change_message('Saving ICs for {}'.format(unk.record_id))

                meas_analysis = db.get_analysis_uuid(unk.uuid)
                history = self.processor.add_history(meas_analysis, cname)

                for si in self.tool.fits:
                    if si.save:
                        # self.debug('saving {} {}'.format(unk.record_id, si.name))
                        self.processor.apply_correction(history, unk, si, set_id, cname)

                # unk.sync_detector_info(meas_analysis)

            if self.auto_plot:
                self.rebuild_graph()

            fits=','.join(('{} {}'.format(fi.name,fi.fit) for fi in self.tool.fits))
            self.processor.update_vcs_analyses(self.analyses,
                                               'Update detector intercalibration fits={}'.format(fits))
            if progress:
                progress.soft_close()

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
            tool.analysis_types = ['']+ntypes

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
        p_ues = reg.predict_error(xs)

        _, d = iso.split('/')
        for ui, v, e in zip(self.sorted_analyses, p_uys, p_ues):
            ui.set_temporary_ic_factor(d, v, e)

        return p_uys, p_ues

    def _get_reference_values(self, dets, ans=None):
        if ans is None:
            ans=self.references

        if not self.tool.standard_ratio:
            self.debug('no standard ratio set')
            return None, None

        n, d = dets.split('/')
        self.debug('get reference values {}, {}'.format(n,d))
        nys = [ri.get_isotope(detector=n) for ri in ans]
        dys = [ri.get_isotope(detector=d) for ri in ans]
        nys = array([ni.get_corrected_value() for ni in nys if ni is not None])
        dys = array([di.get_corrected_value() for di in dys if di is not None])

        try:
            rys = (nys / dys) / self.tool.standard_ratio
            return zip(*[(ri.nominal_value, ri.std_dev) for ri in rys])
        except ZeroDivisionError, e:
            import traceback

            traceback.print_exc()
            return None, None

    def _get_current_values(self, dets, ans=None):
        if ans is None:
            ans=self.analyses

        #return None, None
        n, d = dets.split('/')
        nys = array([ri.get_ic_factor(n) for ri in ans])
        dys = array([ri.get_ic_factor(d) for ri in ans])
        try:
            rys = dys / nys
            return zip(*[(ri.nominal_value, ri.std_dev) for ri in rys])
        except ZeroDivisionError:
            return None, None


            #============= EOF =============================================
