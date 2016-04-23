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
import time

import datetime
from uncertainties import ufloat, std_dev, nominal_value

# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import make_timef
from pychron.core.helpers.filetools import add_extension, subdirize
from pychron.core.helpers.iterfuncs import partition
from pychron.dvc import dvc_dump, dvc_load
from pychron.experiment.utilities.identifier import make_aliquot_step, make_step
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
              'repository_identifier')

PATH_MODIFIERS = (
    None, '.data', 'blanks', 'intercepts', 'icfactors', 'baselines', 'tags', 'peakcenter', 'extraction', 'monitor')


class AnalysisNotAnvailableError(BaseException):
    def __init__(self, root, runid):
        self._root = root
        self._runid = runid

    def __str__(self):
        return 'Analysis Not Available. {} - {}'.format(self._root, self._runid)


def analysis_path(runid, repository, modifier=None, extension='.json', mode='r'):
    root = os.path.join(paths.repository_dataset_dir, repository)

    l = 3
    if runid.count('-') > 1:
        args = runid.split('-')[:-1]
        if len(args[0]) == 1:
            l = 4
        else:
            l = 5

    try:
        root, tail = subdirize(root, runid, l=l, mode=mode)
    except TypeError:
        raise AnalysisNotAnvailableError(root, runid)

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


def repository_path(project):
    return os.path.join(paths.dvc_dir, 'repositories', project)


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
    icfactor_reviewed = False
    blank_reviewed = False

    def __init__(self, record_id, repository_identifier, *args, **kw):
        super(DVCAnalysis, self).__init__(*args, **kw)
        self.record_id = record_id
        path = analysis_path(record_id, repository_identifier)
        self.repository_identifier = repository_identifier
        self.rundate = datetime.datetime.now()
        root = os.path.dirname(path)
        bname = os.path.basename(path)
        head, ext = os.path.splitext(bname)

        jd = dvc_load(os.path.join(root, 'extraction', '{}.extr{}'.format(head, ext)))
        for attr in EXTRACTION_ATTRS:
            tag = attr
            if attr == 'cleanup_duration':
                if attr not in jd:
                    tag = 'cleanup'
            elif attr == 'extract_duration':
                if attr not in jd:
                    tag = 'duration'

            v = jd.get(tag)
            if v is not None:
                setattr(self, attr, v)

        pd = jd.get('positions')
        if pd:
            ps = sorted(pd.itervalues(), key=lambda x: x['position'])
            self.position = ','.join([pp['position'] for pp in ps])
            self.xyz_position = ';'.join(','.join([(pp['x'], pp['y'], pp['z']) for pp in ps]))

        if not self.extract_units:
            self.extract_units = 'W'

        jd = dvc_load(path)
        for attr in META_ATTRS:
            v = jd.get(attr)
            if v is not None:
                setattr(self, attr, v)

        if self.increment is not None:
            self.step = make_step(self.increment)

        try:
            self.rundate = datetime.datetime.strptime(jd['timestamp'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            self.rundate = datetime.datetime.strptime(jd['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')

        self.collection_version = jd['collection_version']
        self._set_isotopes(jd)

        self.timestamp = make_timef(self.rundate)
        self.aliquot_step_str = make_aliquot_step(self.aliquot, self.step)

        self.load_paths()
        self.load_spectrometer_parameters(jd['spec_sha'])

    def load_paths(self, modifiers=None):
        if modifiers is None:
            modifiers = ('intercepts', 'baselines', 'blanks', 'icfactors', 'tags')

        for modifier in modifiers:
            path = self._analysis_path(modifier=modifier)
            if path and os.path.isfile(path):
                jd = dvc_load(path)
                func = getattr(self, '_load_{}'.format(modifier))
                func(jd)

    def load_spectrometer_parameters(self, spec_sha):
        p = os.path.join(paths.repository_dataset_dir, self.repository_identifier, '{}.json'.format(spec_sha))
        sd = dvc_load(p)

        self.source_parameters = sd['spectrometer']
        self.gains = sd['gains']
        self.deflections = sd['deflections']

    def _load_tags(self, jd):
        self.set_tag(jd)

    def _load_blanks(self, jd):
        for key, v in jd.iteritems():
            if key in self.isotopes:
                i = self.isotopes[key]
                self._load_value_error(i.blank, v)
                # i.blank.value = v['value']
                # i.blank.error = v['error']
                i.blank.fit = v['fit']
            elif key == 'reviewed':
                self.blank_reviewed = v

    def _load_intercepts(self, jd):
        for iso, v in jd.iteritems():
            if iso in self.isotopes:
                i = self.isotopes[iso]
                self._load_value_error(i, v)

                i.set_fit(v['fit'], notify=False)
                i.set_filter_outliers_dict(filter_outliers=v.get('filter_outliers', False),
                                           iterations=v.get('iterations', 0),
                                           std_devs=v.get('std_devs', 0))

    def _load_value_error(self, item, obj):
        item.use_manual_value = obj.get('use_manual_value', False)
        item.use_manual_error = obj.get('use_manual_error', False)
        if item.use_manual_value:
            item.value = obj['manual_value']
        else:
            item.value = obj['value']

        if item.use_manual_error:
            item.error = obj['manual_error']
        else:
            item.error = obj['error']

    def _load_baselines(self, jd):
        for det, v in jd.iteritems():
            for iso in self.isotopes.itervalues():
                if iso.detector == det:
                    self._load_value_error(iso.baseline, v)

                    iso.baseline.set_fit(v['fit'], notify=False)
                    iso.baseline.set_filter_outliers_dict(filter_outliers=v.get('filter_outliers', False),
                                                          iterations=v.get('iterations', 0),
                                                          std_devs=v.get('std_devs', 0))

    def _load_icfactors(self, jd):
        for key, v in jd.iteritems():
            if isinstance(v, dict):
                self.set_ic_factor(key, v['value'], v['error'])
            elif key == 'reviewed':
                self.icfactor_reviewed = v

    def load_raw_data(self, keys=None):
        def format_blob(blob):
            return base64.b64decode(blob)

        path = self._analysis_path(modifier='.data')
        isotopes = self.isotopes

        jd = dvc_load(path)
        signals = jd['signals']
        baselines = jd['baselines']
        sniffs = jd['sniffs']

        for sd in signals:
            isok = sd['isotope']
            if keys and isok not in keys:
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
            if keys and isok not in keys:
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

    def set_fits(self, fitobjs):
        isos = self.isotopes
        for fi in fitobjs:
            try:
                iso = isos[fi.name]
            except KeyError:
                # name is a detector
                for i in isos.itervalues():
                    if i.detector == fi.name:
                        i.baseline.set_fit(fi)

                continue

            iso.set_fit(fi)

    def dump_fits(self, keys, reviewed=False):

        sisos = self.isotopes
        isoks, dks = map(tuple, partition(keys, lambda x: x in sisos))

        def update(d, i):
            fd = i.filter_outliers_dict
            d.update(fit=i.fit, value=float(i.value), error=float(i.error),
                     filter_outliers=fd.get('filter_outliers', False),
                     iterations=fd.get('iterations', 0),
                     std_devs=fd.get('std_devs', 0))

        # save intercepts
        if isoks:
            isos, path = self._get_json('intercepts')
            for k in isoks:
                try:
                    iso = isos[k]
                    siso = sisos[k]
                    update(iso, siso)
                except KeyError:
                    pass

            isos['reviewed'] = reviewed
            self._dump(isos, path)

        # save baselines
        if dks:
            baselines, path = self._get_json('baselines')
            for di in dks:
                try:
                    det = baselines[di]
                except KeyError:
                    det = {}
                    baselines[di] = det

                bs = next((iso.baseline for iso in sisos.itervalues() if iso.detector == di), None)
                update(det, bs)

            self._dump(baselines, path)

    def dump_blanks(self, keys, refs, reviewed=False):
        isos, path = self._get_json('blanks')
        sisos = self.isotopes

        for k in keys:
            if k in isos and k in sisos:
                blank = isos[k]
                siso = sisos[k]
                if siso.temporary_blank is not None:
                    blank['value'] = v = float(siso.temporary_blank.value)
                    blank['error'] = e = float(siso.temporary_blank.error)
                    blank['fit'] = f = siso.temporary_blank.fit
                    blank['references'] = make_ref_list(refs)
                    isos[k] = blank

                    siso.blank.value = v
                    siso.blank.error = e
                    siso.blank.fit = f

        isos['reviewed'] = reviewed
        self._dump(isos, path)

    def dump_icfactors(self, dkeys, fits, refs, reviewed=False):
        jd, path = self._get_json('icfactors')

        for dk, fi in zip(dkeys, fits):
            v = self.temporary_ic_factors.get(dk)
            if v is None:
                v, e = 1, 0
            else:
                v, e = nominal_value(v), std_dev(v)

            jd[dk] = {'value': float(v), 'error': float(e),
                      'fit': fi,
                      'references': make_ref_list(refs)}
        jd['reviewed'] = reviewed
        self._dump(jd, path)

    def make_path(self, modifier):
        return self._analysis_path(modifier=modifier)

    def _get_json(self, modifier):
        path = self._analysis_path(modifier=modifier)
        jd = dvc_load(path)
        return jd, path

    def _set_isotopes(self, jd):
        isos = jd.get('isotopes')
        if not isos:
            return

        isos = {k: Isotope(k, v['detector']) for k, v in isos.iteritems()}
        self.isotopes = isos

        # set mass
        path = os.path.join(paths.meta_root, 'molecular_weights.json')
        masses = dvc_load(path)
        for k, v in isos.items():
            v.mass = masses.get(k, 0)

    def _dump(self, obj, path=None, modifier=None):
        if path is None:
            path = self._analysis_path(modifier)

        dvc_dump(obj, path)

    def _analysis_path(self, repository_identifier=None, **kw):
        if repository_identifier is None:
            repository_identifier = self.repository_identifier

        return analysis_path(self.record_id, repository_identifier, **kw)

# ============= EOF ============================================
