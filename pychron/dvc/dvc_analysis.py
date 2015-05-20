# ===============================================================================
# Copyright 2015 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
import base64
import os
import random
import time
# ============= local library imports  ==========================
from uncertainties import ufloat
import yaml
from pychron.paths import paths
from pychron.processing.analyses.analysis import Analysis
from pychron.processing.isotope import Isotope
from pychron.pychron_constants import INTERFERENCE_KEYS

ANALYSIS_ATTRS = ('analysis_type', 'uuid', 'sample', 'project', 'material', 'aliquot', 'increment',
                  'irradiation', 'weight',
                  'comment', 'irradiation_level', 'mass_spectrometer', 'extract_device',
                  'username', 'tray', 'queue_conditionals_name', 'extract_value',
                  'extract_units', 'position', 'xyz_position', 'duration', 'cleanup',
                  'pattern', 'beam_diameter', 'ramp_duration', 'ramp_rate', 'identifier')


def analysis_path(record):
    path = os.path.join(project_path(record.project), '{}.yaml'.format(record.record_id))
    return path


def project_path(project):
    return os.path.join(paths.dvc_dir, 'projects', project)


class DVCAnalysis(Analysis):

    def __init__(self, record, *args, **kw):
        super(DVCAnalysis, self).__init__(*args, **kw)

        self.path = path = analysis_path(record)

        with open(path, 'r') as rfile:
            yd = yaml.load(rfile)

            for attr in ANALYSIS_ATTRS:
                v = yd.get(attr)
                if v is not None:
                    setattr(self, attr, v)

            self.rundate = yd['timestamp']  # datetime.strptime(yd['timestamp'], '%Y-%m-%dT%H:%M:%S')
            self.timestamp = time.mktime(self.rundate.timetuple())
            self.collection_version = yd['collection_version']

            self._set_isotopes(yd)
            try:
                self.source_parameters = yd['source']
            except KeyError:
                pass

    def load_raw_data(self, keys):
        with open(self.path, 'r') as rfile:
            yd = yaml.load(rfile)

            isos = yd['isotopes']
            for k in keys:
                if k in isos:
                    if k in self.isotopes:
                        iso = self.isotopes[k]
                        iso.unpack_data(base64.b64decode(isos[k]['signal']))
                        iso.baseline.unpack_data(base64.b64decode(isos[k]['baseline']))

    def set_production(self, prod, r):
        self.production_name = prod
        self.production_ratios = r.to_dict(('Ca_K', 'Cl_K'))
        self.interference_corrections = r.to_dict(INTERFERENCE_KEYS)

    def set_chronology(self, chron):
        analts = self.rundate

        convert_days = lambda x: x.total_seconds() / (60. * 60 * 24)
        doses = chron.get_doses()
        segments = [(pwr, convert_days(en - st), convert_days(analts - st))
                    for pwr, st, en in doses
                    if st is not None and en is not None]

        d_o = doses[0][1]
        self.irradiation_time = time.mktime(d_o.timetuple()) if d_o else 0
        self.chron_segments = segments
        self.chron_dosages = doses
        self.calculate_decay_factors()

        age = 10 + 0.4 - random.random()
        age_err = random.random()
        self.age = age
        self.age_err = age_err
        self.uage = ufloat(age, age_err)
        # self.uage_wo_j_err = ufloat(age, age_err_wo_j)

    def set_fits(self, fitobjs):
        isos = self.isotopes
        for fi in fitobjs:
            try:
                iso = isos[fi.name]
            except KeyError:
                continue

            iso.set_fit(fi)

    def dump_fits(self, keys):
        yd = self._get_yd()

        sisos = self.isotopes
        isos = yd['isotopes']
        for k in keys:
            if k in isos and k in sisos:
                iso = isos[k]
                siso = sisos[k]
                iso['fit'] = siso.fit

                # value, error = siso.get_intercept()
                # print k, siso.value
                iso['raw_intercept']['value'] = float(siso.value)
                iso['raw_intercept']['error'] = float(siso.error)

        self._dump(yd)

    def dump_blanks(self, keys, refs):
        yd = self._get_yd()
        sisos = self.isotopes
        isos = yd['isotopes']
        # print keys
        for k in keys:
            if k in isos and k in sisos:
                iso = isos[k]
                siso = sisos[k]

                if siso.temporary_blank is not None:
                    blank = iso.get('blank', {})
                    # print blank, float(siso.temporary_blank.value)
                    blank['value'] = float(siso.temporary_blank.value)
                    blank['error'] = float(siso.temporary_blank.error)
                    blank['fit'] = siso.temporary_blank.fit
                    iso['blank'] = blank

        self._dump(yd)

    # private
    def _get_yd(self):
        with open(self.path, 'r') as rfile:
            yd = yaml.load(rfile)
        return yd

    def _set_isotopes(self, yd):
        isos = yd.get('isotopes')
        if not isos:
            return

        for k, v in isos.items():
            # bsc = v['baseline_corrected']
            raw = v['raw_intercept']
            det = v['detector']
            detname = det['name']

            self.isotopes[k] = Isotope(name=k,
                                       detector=detname,
                                       _value=raw['value'], _error=raw['error'])
            if detname not in self.deflections:
                self.deflections[detname] = det['deflection']

    def _dump(self, obj, path=None):
        if path is None:
            path = self.path

        with open(path, 'w') as wfile:
            yaml.dump(obj, wfile, default_flow_style=False)
# ============= EOF =============================================



