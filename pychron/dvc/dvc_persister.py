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
import base64

from traits.api import Instance

# ============= standard library imports ========================
import hashlib
import os
import struct
# import yaml
import json

from datetime import datetime
from uncertainties import std_dev
from uncertainties import nominal_value
# ============= local library imports  ==========================
from pychron.dvc.dvc_analysis import META_ATTRS, EXTRACTION_ATTRS, analysis_path, PATH_MODIFIERS
from pychron.experiment.automated_run.persistence import BasePersister
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths


def jdump(obj, p):
    with open(p, 'w') as wfile:
        json.dump(obj, wfile, indent=4)


def format_project(project):
    return project.replace('/', '_').replace('\\', '_')


class DVCPersister(BasePersister):
    experiment_repo = Instance(GitRepoManager)
    dvc = Instance('pychron.dvc.dvc.DVC')

    # def __init__(self, *args, **kw):
    #     super(DVCPersister, self).__init__(*args, **kw)
    #     self.dvc = self.application.get_service('pychron.dvc.dvc.DVC')

    def per_spec_save(self, pr, commit=False, msg_prefix=None):
        self.per_spec = pr
        self.initialize(False)
        self.pre_extraction_save()
        self.pre_measurement_save()
        self.post_extraction_save('', '', None)
        self.post_measurement_save(commit=commit, msg_prefix=msg_prefix)

    def initialize(self, sync=True):
        """
        setup git repos.

        repositories are guaranteed to exist. The automated run factory clones the required projects
        on demand.

        synchronize the database
        :return:
        """
        if not self.experiment_repo:
            project = self.per_spec.run_spec.project
            project = format_project(project)
            self.experiment_repo = GitRepoManager()
            self.experiment_repo.open_repo(os.path.join(paths.experiment_dataset_dir, project))
            self.info('pulling changes from project repo: {}'.format(project))
            self.experiment_repo.pull()

            # if sync:
            #     self.info('synchronize dvc')
            # self.dvc.synchronize()
            # self.meta_repo = GitRepoManager()
            # self.meta_repo.open_repo(paths.meta_dir)
            # self.meta_repo.pull()

    def pre_extraction_save(self):
        pass

    def post_extraction_save(self, rblob, oblob, snapshots):
        p = self._make_path(modifier='extraction')
        obj = {'request': rblob,
               'response': oblob}

        for e in EXTRACTION_ATTRS:
            v = getattr(self.per_spec.run_spec, e)
            obj[e] = v

        ps = []
        for i, pp in enumerate(self.per_spec.positions):
            pos, x, y, z = None, None, None, None
            if isinstance(pp, tuple):
                if len(pp) == 2:
                    x, y = pp
                elif len(pp) == 3:
                    x, y, z = pp

            else:
                pos = pp
                try:
                    ep = self.per_spec.extraction_positions[i]
                    x = ep[0]
                    y = ep[1]
                    if len(ep) == 3:
                        z = ep[2]
                except IndexError:
                    self.debug('no extraction position for {}'.format(pp))
            pd = {'x': x, 'y': y, 'z': z, 'position': pos, 'is_degas': self.per_spec.run_spec.identifier == 'dg'}
            ps.append(pd)

        obj['positions'] = ps
        hexsha = self.dvc.get_meta_head()
        obj['commit'] = str(hexsha)

        jdump(obj, p)

    def pre_measurement_save(self):
        pass

    def save_peak_center_to_file(self, pc):
        p = self._make_path(modifier='peakcenter')
        xx, yy = pc.graph.get_data(), pc.graph.get_data(axis=1)

        xs, ys, _mx, _my = pc.result
        fmt = '>ff'
        obj = {'low_dac': xs[0],
               'center_dac': xs[1],
               'high_dac': xs[2],
               'low_signal': ys[0],
               'center_signal': ys[1],
               'high_signal': ys[2],
               'fmt': fmt,
               'data': ''.join([struct.pack(fmt, di) for di in zip(xx, yy)])}
        jdump(obj, p)

    def post_measurement_save(self, commit=True, msg_prefix='Collection'):
        """
        save
            - analysis.json
            - analysis.monitor.json

        check if unique spectrometer.json
        commit changes
        push changes
        :return:
        """
        # save spectrometer
        spec_sha = self._get_spectrometer_sha()
        spec_path = os.path.join(self.experiment_repo.path, '{}.json'.format(spec_sha))
        # spec_path = self._make_path('.spectrometer', spec_sha)
        if not os.path.isfile(spec_path):
            self._save_spectrometer_file(spec_path)

        # save analysis
        t = datetime.now()
        self._save_analysis(timestamp=t, spec_sha=spec_sha)

        self._save_analysis_db(t)

        # save monitor
        self._save_monitor()

        # stage files
        paths = [spec_path, ] + [self._make_path(modifier=m) for m in PATH_MODIFIERS]

        for p in paths:
            if os.path.isfile(p):
                self.experiment_repo.add(p, commit=commit, msg_prefix=msg_prefix)
            else:
                self.debug('not at valid file {}'.format(p))

        if commit:
            # commit files
            self.experiment_repo.commit('added analysis {}'.format(self.per_spec.run_spec.runid))
            self.dvc.meta_commit('repo updated for analysis {}'.format(self.per_spec.run_spec.runid))

            # push commit
            self.dvc.synchronize(pull=False)

    # private
    def _save_analysis_db(self, timestamp):
        rs = self.per_spec.run_spec
        d = {k: getattr(rs, k) for k in ('uuid', 'analysis_type', 'aliquot',
                                         'increment', 'mass_spectrometer',
                                         'extract_device', 'weight', 'comment',
                                         'cleanup', 'duration', 'extract_value', 'extract_units')}

        if not self.per_spec.timestamp:
            d['timestamp'] = timestamp
        else:
            d['timestamp'] = self.per_spec.timestamp

        db = self.dvc.db
        with db.session_ctx():
            an = db.add_analysis(**d)

            # all associations are handled by the ExperimentExecutor._retroactive_experiment_identifiers

            # # special associations are handled by the ExperimentExecutor._retroactive_experiment_identifiers
            # if not is_special(rs.runid):
            if self.per_spec.use_experiment_association:
                db.add_experiment_association(rs.experiment_id, an)

            pos = db.get_irradiation_position(rs.irradiation, rs.irradiation_level, rs.irradiation_position)

            an.irradiation_position = pos
            t = self.per_spec.tag
            if t:
                dbtag = db.get_tag(t)
                if not dbtag:
                    dbtag = db.add_tag(t)

            an.change.tag_item = dbtag
            # self._save_measured_positions()

    def _save_measured_positions(self):
        dvc = self.dvc

        load_name = self.per_spec.load_name
        for i, pp in enumerate(self.per_spec.positions):
            if isinstance(pp, tuple):
                if len(pp) > 1:
                    if len(pp) == 3:
                        dvc.add_measured_position('', load_name, x=pp[0], y=pp[1], z=pp[2])
                    else:
                        dvc.add_measured_position('', load_name, x=pp[0], y=pp[1])
                else:
                    dvc.add_measured_position(pp[0], load_name)

            else:
                dbpos = dvc.add_measured_position(pp, load_name)
                try:
                    ep = self.per_spec.extraction_positions[i]
                    dbpos.x = ep[0]
                    dbpos.y = ep[1]
                    if len(ep) == 3:
                        dbpos.z = ep[2]
                except IndexError:
                    self.debug('no extraction position for {}'.format(pp))

    def _make_analysis_dict(self, keys=None):
        rs = self.per_spec.run_spec
        # attrs = ('sample', 'aliquot', 'increment', 'irradiation', 'weight',
        # 'comment', 'irradiation_level', 'mass_spectrometer', 'extract_device',
        # 'username', 'tray', 'queue_conditionals_name', 'extract_value',
        # 'extract_units', 'position', 'xyz_position', 'duration', 'cleanup',
        # 'pattern', 'beam_diameter', 'ramp_duration', 'ramp_rate')
        # attrs = ANALYSIS_ATTRS
        # if exclude:
        #     attrs = (a for a in ANALYSIS_ATTRS if a not in exclude)
        if keys is None:
            keys = META_ATTRS

        d = {k: getattr(rs, k) for k in keys}
        return d

    def _save_analysis(self, timestamp, **kw):

        isos = {}
        dets = {}
        signals = []
        baselines = []
        sniffs = []
        cisos = {}
        cdets = {}
        endianness = '>'
        for iso in self.per_spec.arar_age.isotopes.values():

            sblob = base64.b64encode(iso.pack(endianness, as_hex=False))
            snblob = base64.b64encode(iso.sniff.pack(endianness, as_hex=False))
            signals.append({'isotope': iso.name, 'detector': iso.detector, 'blob': sblob})
            sniffs.append({'isotope': iso.name, 'detector': iso.detector, 'blob': snblob})

            isos[iso.name] = {'detector': iso.detector}

            if iso.detector not in dets:
                bblob = base64.b64encode(iso.baseline.pack(endianness, as_hex=False))
                baselines.append({'detector': iso.detector, 'blob': bblob})
                # baselines[iso.detector] = bblob
                dets[iso.detector] = {'deflection': self.per_spec.defl_dict.get(iso.detector),
                                      'gain': self.per_spec.gains.get(iso.detector),
                                      }
                cdets[iso.detector] = {'baseline': {'fit': iso.baseline.fit,
                                                    'value': float(iso.baseline.value),
                                                    'error': float(iso.baseline.error)},
                                       'ic_factor': {'value': float(nominal_value(iso.ic_factor)),
                                                     'error': float(std_dev(iso.ic_factor)),
                                                     'fit': 'default',
                                                     'references': []}}

            cisos[iso.name] = {'fit': iso.fit,
                               'raw_intercept': {'value': iso.value, 'error': iso.error},
                               'blank': {'fit': 'previous',
                                         'references': [{'runid': self.per_spec.previous_blank_runid,
                                                         'exclude': False}],
                                         'value': float(iso.blank.value),
                                         'error': float(iso.blank.error)}}

        obj = self._make_analysis_dict()

        from pychron.experiment import __version__ as eversion
        from pychron.dvc import __version__ as dversion

        if not self.per_spec.timestamp:
            obj['timestamp'] = timestamp.isoformat()
        else:
            obj['timestamp'] = self.per_spec.timestamp.isoformat()

        obj['collection_version'] = '{}:{}'.format(eversion, dversion)
        obj['detectors'] = dets
        obj['isotopes'] = isos
        obj.update(**kw)

        # save the scripts
        for si in ('measurement', 'extraction'):
            name = getattr(self.per_spec, '{}_name'.format(si))
            blob = getattr(self.per_spec, '{}_blob'.format(si))
            self.dvc.update_script(name, blob)

        # save experiment
        self.dvc.update_experiment_queue(self.per_spec.experiment_queue_name,
                                         self.per_spec.experiment_queue_blob)

        hexsha = str(self.dvc.get_meta_head())
        obj['commit'] = hexsha

        # dump runid.json
        p = self._make_path()
        jdump(obj, p)

        # dump runid.changeable.json
        p = self._make_path(modifier='changeable')
        jdump({'commit': hexsha, 'isotopes': cisos, 'detectors': cdets}, p)

        # dump runid.data.json
        p = self._make_path(modifier='.data')
        data = {'commit': hexsha,
                'encoding': 'base64',
                'format': '{}ff'.format(endianness),
                'signals': signals, 'baselines': baselines, 'sniffs': sniffs}
        jdump(data, p)

    def _make_path(self, modifier=None, extension='.json'):
        runid = self.per_spec.run_spec.runid
        experiment_id = self.per_spec.run_spec.experiment_id
        return analysis_path(runid, experiment_id, modifier, extension, mode='w')

        # if prefix is None:
        #     root = self.experiment_repo.path
        #     root = os.path.join(root, prefix[:3])
        #     if not os.path.isdir(root):
        #         os.mkdir(root)
        #     prefix = prefix[3:]
        #
        # else:
        #     root = self.experiment_repo.path
        #
        # return os.path.join(root, '{}{}{}'.format(prefix, name, extension))

    def _get_spectrometer_sha(self):
        """
        return a sha-1 hash.

        generate using spec_dict, defl_dict, and gains
        spec_dict: source parameters, cdd operating voltage
        defl_dict: detector deflections
        gains: detector gains

        make hash using
        for key,value in dictionary:
            sha1.update(key)
            sha1.update(value)

        to ensure consistence, dictionaries are sorted by key
        for key,value in sorted(dictionary)
        :return:
        """
        sha = hashlib.sha1()
        for d in (self.per_spec.spec_dict, self.per_spec.defl_dict, self.per_spec.gains):
            for k, v in sorted(d.items()):
                sha.update(k)
                sha.update(str(v))

        return sha.hexdigest()

    def _save_monitor(self):
        if self.per_spec.monitor:
            p = self._make_path(modifier='monitor')
            checks = []
            for ci in self.per_spec.monitor.checks:
                data = ''.join([struct.pack('>ff', x, y) for x, y in ci.data])
                params = dict(name=ci.name,
                              parameter=ci.parameter, criterion=ci.criterion,
                              comparator=ci.comparator, tripped=ci.tripped,
                              data=data)
                checks.append(params)

            jdump(checks, p)

    def _save_spectrometer_file(self, path):
        obj = dict(spectrometer=dict(self.per_spec.spec_dict),
                   gains=dict(self.per_spec.gains),
                   deflections=dict(self.per_spec.defl_dict))
        hexsha = self.dvc.get_meta_head()
        obj['commit'] = str(hexsha)

        jdump(obj, path)

# ============= EOF =============================================
