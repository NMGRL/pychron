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
from binascii import unhexlify
import os
import time
# ============= local library imports  ==========================
import datetime
from uncertainties import ufloat, std_dev, nominal_value
# import yaml
import json
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

PATH_MODIFIERS = (None, '.data', 'changeable', 'peakcenter', 'extraction', 'monitor')


def analysis_path(runid, experiment, modifier=None, extension='.json', mode='r'):
    root = os.path.join(paths.experiment_dataset_dir, experiment)

    l = 3
    if runid.count('-') > 1:
        args = runid.split('-')[:-1]
        if len(args[0]) == 1:
            l = 4
        else:
            l = 5

    root, tail = subdirize(root, runid, l=l, mode=mode)

    # head, tail = runid[:3], runid[3:]
    # # if modifier:
    # #     tail = '{}{}'.format(tail, modifier)
    # root = os.path.join(paths.experiment_dataset_dir, experiment, head)
    # if not os.path.isdir(root):
    #     os.mkdir(root)

    if modifier:
        d = os.path.join(root, modifier)
        if not os.path.isdir(d):
            if mode == 'r':
                return

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


def make_ref_list(refs):
    return [{'record_id': r.record_id, 'uuid': r.uuid, 'exclude': r.temp_status} for r in refs]


class Blank:
    pass


class Baseline:
    pass


class TIsotope:
    def __init__(self, name, det):
        self.name = name
        self.detector = det
        self.blank = Blank()
        self.baseline = Baseline()

    def set_fit(self, *args, **kw):
        pass

    def get_intensity(self):
        return ufloat((1, 0.5))


class DVCAnalysis(Analysis):
    def __init__(self, record_id, experiment_id, *args, **kw):
        super(DVCAnalysis, self).__init__(*args, **kw)

        path = analysis_path(record_id, experiment_id)
        self.experiment_id = experiment_id
        # self.irradiation='NM-272'
        # self.irradiation_level = 'A'
        # self.irradiation_position = 2
        self.rundate = datetime.datetime.now()
        self.timestamp = time.mktime(self.rundate.timetuple())

        root = os.path.dirname(path)
        bname = os.path.basename(path)
        head, ext = os.path.splitext(bname)
        # st=time.time()
        with open(os.path.join(root, 'extraction', '{}.extr{}'.format(head, ext))) as rfile:
            yd = json.load(rfile)
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
        # print '  extraction {}'.format(time.time()-st)
        # st=time.time()
        with open(path, 'r') as rfile:
            # sst =time.time()

            yd = json.load(rfile)
            # print '    load {}'.format(time.time()-sst)

            # sst =time.time()
            for attr in META_ATTRS:
                v = yd.get(attr)
                if v is not None:
                    # print attr, v
                    setattr(self, attr, v)
            # print '    attr {}'.format(time.time()-sst)

            # sst=time.time()
            self.rundate = datetime.datetime.strptime(yd['timestamp'], '%Y-%m-%dT%H:%M:%S')
            self.timestamp = time.mktime(self.rundate.timetuple())
            self.collection_version = yd['collection_version']
            # print '    timestamps {}'.format(time.time()-sst)
            # sst=time.time()
            self._set_isotopes(yd)
            # print '    isotopes {}'.format(time.time()-sst)

            # try:
            #     self.source_parameters = yd['source']
            # except KeyError:
            #     pass
        # print '  meta {}'.format(time.time()-st)

        # st=time.time()
        with open(analysis_path(record_id, experiment_id, modifier='changeable', extension='.json')) as rfile:
            # sst=time.time()
            yd = json.load(rfile)
            # print '    load time {}'.format(time.time()-sst)
            self._set_changeables(yd)
            # print '  changeables {}'.format(time.time()-st)

    def load_raw_data(self, keys):
        def format_blob(blob):
            # return base64.b64decode(blob)
            return unhexlify(base64.b64decode(blob))

        path = self._analysis_path(modifier='.data')
        isotopes = self.isotopes
        isos = [i for i in isotopes.itervalues() if i.name in keys and not i.xs.shape[0]]
        if not isos:
            return

        with open(path, 'r') as rfile:
            yd = json.load(rfile)
            signals = yd['signals']
            baselines = yd['baselines']
            sniffs = yd['sniffs']

            # isotopes = self.isotopes
            for sd in signals:
                isok = sd['isotope']
                if isok not in keys:
                    continue

                try:
                    iso = isotopes[isok]
                except KeyError:
                    continue

                iso.unpack_data(format_blob(sd['blob']))

                det = sd['detector']
                bd = next((b for b in baselines if b['detector'] == det), None)
                if bd:
                    iso.baseline.unpack_data(format_blob(bd['blob']))

            for sn in sniffs:
                isok = sn['isotope']
                if isok not in keys:
                    continue

                try:
                    iso = isotopes[isok]
                except KeyError:
                    continue
                iso.sniff.unpack_data(format_blob(sn['blob']))

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
        d_o = 0
        if doses:
            d_o = doses[0][1]
        self.irradiation_time = time.mktime(d_o.timetuple()) if d_o else 0
        self.chron_segments = segments
        self.chron_dosages = doses
        self.calculate_decay_factors()

        # age = 10 + 0.4 - random.random()
        # age_err = random.random()
        # self.age = age
        # self.age_err = age_err
        # self.uage = ufloat(age, age_err)
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
        yd, path = self._get_yd('changeable')

        sisos = self.isotopes
        isos = yd['isotopes']
        for k in keys:
            if k in isos and k in sisos:
                iso = isos[k]
                siso = sisos[k]
                iso['fit'] = siso.fit

                iso['raw_intercept'] = dict(value=float(siso.value), error=float(siso.error))
        self._dump(yd, path)

    def dump_blanks(self, keys, refs):
        yd, path = self._get_yd('changeable')
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
                    blank['references'] = make_ref_list(refs)
                    iso['blank'] = blank

        self._dump(yd, path)

    def dump_icfactors(self, dkeys, fits, refs):
        yd, path = self._get_yd('changeable')

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
            icf['references'] = make_ref_list(refs)
            det['ic_factor'] = icf

            dets[dk] = det

        yd['detectors'] = dets
        self._dump(yd, path)

    def make_path(self, modifier):
        return self._analysis_path(modifier=modifier)

    # def get_commits(self, tag, path):
    #     from pychron.git_archive.utils import get_commits
    #     repo = Repo(os.path.join(paths.experiment_dataset_dir, self.experiment_id))
    #
    #     return get_commits(repo, repo.active_branch.name, path,
    #                        '--grep={}'.format(tag))
    #
    # def get_tag_commits(self, tag):
    #     path = self._analysis_path(modifier='tag')
    #     return self.get_commits(tag, path)
    #
    # def get_tag_diff(self):
    #     path = self._analysis_path(modifier='tag')

    # private
    # def _get_repo(self,):
    #     if not repo:
    #         repo = Repo(os.path.join(paths.experiment_dataset_dir, self.experiment_id))
    #         self._repo = repo
    #     return repo

    def _set_changeables(self, yd):
        isos = yd.get('isotopes')
        if not isos:
            return

        dets = yd.get('detectors')
        if not dets:
            return

        isotopes = self.isotopes
        for k, v in isos.iteritems():
            try:
                iso = isotopes[k]
            except KeyError, e:
                print e
                continue

            if iso:
                iso.set_fit(v.get('fit'))
                b = v.get('blank')
                if b:
                    iso.blank.value = b['value']
                    iso.blank.error = b['error']

                r = v.get('raw_intercept')
                if r:
                    iso.value = r['value']
                    iso.error = r['error']

                det = dets.get(iso.detector)
                if det:
                    bs = det['baseline']
                    if bs:
                        iso.baseline.value = bs['value']
                        iso.baseline.error = bs['error']
                        iso.baseline.set_fit(bs['fit'])

                    ic = det['ic_factor']
                    if ic:
                        self.set_ic_factor(iso.detector, ic['value'], ic['error'])

    def _get_yd(self, modifier):
        path = self._analysis_path(modifier=modifier)
        # path = analysis_path(self.record_id, self.experiment_id, modifier=modifier)
        with open(path, 'r') as rfile:
            yd = json.load(rfile)
        return yd, path

    def _set_isotopes(self, yd):
        isos = yd.get('isotopes')
        if not isos:
            return

        self.isotopes = {k: Isotope(k, v['detector']) for k, v in isos.iteritems()}
        # self.isotopes = {k: TIsotope(k, v['detector']) for k,v in isos.iteritems()}
        # nisos = {}
        # for k, v in isos.items():
        # bsc = v['baseline_corrected']
        # raw = v['raw_intercept']
        # detname = v['detector']
        # TIsotope(k, detname)
        # self.isotopes[k] = TIsotope(k, detname)
        # self.isotopes[k] = Isotope(name=k,
        #                            detector=detname)
        # _value=raw['value'],
        # _error=raw['error']
        # )
        # if detname not in self.deflections:
        # self.deflections[detname] = det['deflection']

    def _dump(self, obj, path=None, modifier=None):
        if path is None:
            path = self._analysis_path(modifier)

        with open(path, 'w') as wfile:
            json.dump(obj, wfile, indent=4)

    def _analysis_path(self, experiment_id=None, modifier=None, mode='r', extension='.json'):
        if experiment_id is None:
            experiment_id = self.experiment_id

        return analysis_path(self.record_id, experiment_id, modifier=modifier, mode=mode, extension=extension)

# ============= EOF =============================================
