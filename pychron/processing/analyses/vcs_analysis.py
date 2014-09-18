
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

#============= standard library imports ========================
import os

import yaml
from uncertainties import ufloat

#============= local library imports  ==========================
from pychron.paths import paths
from pychron.processing.analyses.dbanalysis import DBAnalysis
from pychron.processing.isotope import Isotope


class VCSAnalysis(DBAnalysis):
    """
        uses local data with db metadata
    """

    def _load_file(self):
        pr = self.project.replace(' ', '_')

        p = os.path.join(paths.vcs_dir, pr, self.sample, self.labnumber, '{}.yaml'.format(self.record_id))
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                return yaml.load(fp)


    def _sync(self, meas_analysis, unpack=False, load_aux=False):
        """
            if unpack is true load original signal data from db
        """

        self._sync_meas_analysis_attributes(meas_analysis)
        self._sync_analysis_info(meas_analysis)
        self.analysis_type = self._get_analysis_type(meas_analysis)
        self._sync_extraction(meas_analysis)
        self._sync_experiment(meas_analysis)

        self.has_raw_data = unpack
        use_local = not unpack
        if not unpack:
            yd = self._load_file()
            if not yd:
                use_local = False

        if use_local:
            self._sync_irradiation(yd, meas_analysis.labnumber)
            self._sync_isotopes(yd, meas_analysis, unpack)
            self._sync_detector_info(yd, meas_analysis)
        else:
            super(VCSAnalysis, self)._sync_irradiation(meas_analysis.labnumber)
            super(VCSAnalysis, self)._sync_isotopes(meas_analysis, unpack)
            super(VCSAnalysis, self)._sync_detector_info(meas_analysis)

        if load_aux:
            self._sync_changes(meas_analysis)

    def _sync_irradiation(self, yd, ln):

        cs = []
        for ci in yd['chron_segments']:
            cs.append((ci['power'], ci['duration'], ci['dt']))

        self.chron_segments = cs
        self.production_ratios = yd['production_ratios']

        ifc = yd['interference_corrections']
        nifc = dict()
        for k in ifc:
            if k.endswith('_err'):
                continue
            nifc[k] = self._to_ufloat(ifc, k)

        self.interference_corrections = nifc

        self.j = ufloat(yd['j'], yd['j_err'])

    def _sync_isotopes(self, yd, meas_analysis, unpack):
        """
            load isotopes from file
        """
        isos = {}
        # print yd['isotopes']
        for iso in yd['isotopes']:
            ii = Isotope(name=iso['name'],
                         detector=iso['detector'],
                         ic_factor=self._to_ufloat(iso, 'ic_factor'),
                         discrimination=self._to_ufloat(iso, 'discrimination'))

            ii.trait_set(_value=iso['value'], _error=iso['error'])

            ii.set_blank(iso['blank'], iso['blank_err'])
            ii.set_baseline(iso['baseline'], iso['baseline_err'])

            isos[iso['name']] = ii
        self.isotopes = isos
        # print self.isotopes

    def _to_ufloat(self, obj, attr):
        return ufloat(obj[attr], obj['{}_err'.format(attr)])

    def _sync_detector_info(self, yd, meas_analysis, **kw):
        pass

#============= EOF =============================================