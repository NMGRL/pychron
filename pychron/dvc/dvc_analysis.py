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
from uncertainties import ufloat, std_dev, nominal_value
import yaml
from pychron.core.helpers.filetools import add_extension, subdirize
from pychron.paths import paths
from pychron.processing.analyses.analysis import Analysis
from pychron.processing.isotope import Isotope
from pychron.pychron_constants import INTERFERENCE_KEYS

EXTRACTION_ATTRS = ('weight', 'extract_device', 'tray', 'extract_value',
                    'extract_units',
                    # 'duration',
                    # 'cleanup',
                    'extract_duration',
                    'cleanup_duration',
                    'pattern', 'beam_diameter', 'ramp_duration', 'ramp_rate')

META_ATTRS = ('analysis_type', 'uuid', 'sample', 'project', 'material', 'aliquot', 'increment',
              'irradiation', 'irradiation_level', 'irradiation_position',
              'comment', 'mass_spectrometer',
              'username', 'queue_conditionals_name', 'identifier',
              'experiment_id')


def analysis_path(runid, experiment, modifier=None, extension='.yaml'):
    root = os.path.join(paths.experiment_dataset_dir, experiment)
    root, tail = subdirize(root, runid, l=3)

    # head, tail = runid[:3], runid[3:]
    # # if modifier:
    # #     tail = '{}{}'.format(tail, modifier)
    # root = os.path.join(paths.experiment_dataset_dir, experiment, head)
    # if not os.path.isdir(root):
    #     os.mkdir(root)

    if modifier:
        d = os.path.join(root, modifier)
        if not os.path.isdir(d):
            os.mkdir(d)

        root = d
        fmt = '{}.{}'
        if modifier.startswith('.'):
            fmt = '{}{}'
        tail = fmt.format(tail, modifier[:4])

    name = add_extension(tail, extension)

    return os.path.join(root, name)


def experiment_path(project):
    return os.path.join(paths.dvc_dir, 'experiments', project)


class DVCAnalysis(Analysis):
    def __init__(self, record_id, experiment_id, *args, **kw):
        super(DVCAnalysis, self).__init__(*args, **kw)

        self.path = path = analysis_path(record_id, experiment_id)
        self.experiment_id = experiment_id
        root = os.path.dirname(path)
        bname = os.path.basename(path)
        head, ext = os.path.splitext(bname)
        with open(os.path.join(root, 'extraction', '{}.extr{}'.format(head, ext))) as rfile:
            yd = yaml.load(rfile)
            for attr in EXTRACTION_ATTRS:
                tag = attr
                if attr == 'cleanup_duration':
                    if attr not in yd:
                        tag = 'cleanup'
                elif attr == 'extract_duration':
                    if attr not in yd:
                        tag = 'duration'
                # tag = attr
                # if attr == 'cleanup':
                #     tag = 'cleanup_duration'
                # elif attr == 'duration':
                #     tag = 'extract_duration'

                v = yd.get(tag)
                # print attr, tag, v
                if v is not None:
                    setattr(self, attr, v)

        with open(path, 'r') as rfile:
            yd = yaml.load(rfile)
            for attr in META_ATTRS:
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
            dets = yd['detectors']
            for k in keys:
                if k in isos:
                    if k in self.isotopes:
                        iso = self.isotopes[k]

                        signal = isos[k]['signal']
                        baseline = dets[isos[k]['detector']]['baseline']['signal']

                        iso.unpack_data(base64.b64decode(signal))
                        iso.baseline.unpack_data(base64.b64decode(baseline))

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
                    blank['references'] = self._make_ref_list(refs)
                    iso['blank'] = blank

        self._dump(yd)

    def dump_icfactors(self, dkeys, fits, refs):
        yd = self._get_yd()

        dets = yd.get('detectors', {})
        for dk, fi in zip(dkeys, fits):
            v = self.temporary_ic_factors.get(dk)
            if v is None:
                v, e = 1, 0
            else:
                v, e = nominal_value(v), std_dev(v)

            det = dets.get(dk, {})
            icf = det.get('ic_factor', {})
            icf['ic_factor'] = float(v)
            icf['ic_factor_err'] = float(e)
            icf['fit'] = fi
            icf['references'] = self._make_ref_list(refs)
            det['ic_factor'] = icf

            dets[dk] = det

        yd['detectors'] = dets
        self._dump(yd)

    # private
    def _make_ref_list(self, refs):
        return [{'record_id': r.record_id, 'uuid': r.uuid, 'exclude': r.temp_status} for r in refs]

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
            # raw = v['raw_intercept']
            detname = v['detector']
            self.isotopes[k] = Isotope(name=k,
                                       detector=detname,
                                       # _value=raw['value'],
                                       # _error=raw['error']
                                       )
            # if detname not in self.deflections:
            # self.deflections[detname] = det['deflection']

    def _dump(self, obj, path=None):
        if path is None:
            path = self.path

        with open(path, 'w') as wfile:
            yaml.dump(obj, wfile, default_flow_style=False)

# ============= EOF =============================================
