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
from traits.api import List, Dict, Instance, Str
# ============= standard library imports ========================
import hashlib
import os
import struct
import yaml
from datetime import datetime
from uncertainties import std_dev
from uncertainties import nominal_value
# ============= local library imports  ==========================
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.loggable import Loggable
from pychron.paths import paths


def ydump(obj, p):
    with open(p, 'w') as wfile:
        yaml.dump(obj, wfile, default_flow_style=False)


class DVCPersister(Loggable):
    # db = Instance(DVCDatabase)
    project_repo = Instance(GitRepoManager)
    # meta_repo = Instance(GitRepoManager)
    dvc = Instance('pychron.dvc.dvc.DVC')

    run_spec = Instance('pychron.automated_run.automated_run_spec.AutomatedRunSpec')
    monitor = None

    save_enabled = False
    spec_dict = Dict
    defl_dict = Dict
    gains = Dict

    active_detectors = List
    previous_blank_runid = Str

    def __init__(self, *args, **kw):
        super(DVCPersister, self).__init__(*args, **kw)
        self.dvc = self.application.get_service('pychron.dvc.dvc.DVC')

    def initialize(self):
        """
        setup git repos.

        repositories are guaranteed to exist. The automated run factory clones the required projects
        on demand.

        synchronize the database
        :return:
        """
        project = self.run_spec.project
        self.project_repo = GitRepoManager()
        self.project_repo.open_repo(os.path.join(paths.project_dir, project))
        self.info('pulling changes from project repo: {}'.format(project))
        self.project_repo.pull()

        self.info('synchronize dvc')
        self.dvc.synchronize()
        # self.meta_repo = GitRepoManager()
        # self.meta_repo.open_repo(paths.meta_dir)
        # self.meta_repo.pull()

    def pre_extraction_save(self):
        pass

    def post_extraction_save(self, rblob, oblob, snapshots):
        p = self._make_path('.extraction')

        obj = {'request': rblob,
               'response': oblob}

        ydump(obj, p)

    def pre_measurement_save(self):
        pass

    def save_peak_center(self, pc):
        p = self._make_path('.peakcenter')
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
        ydump(obj, p)

    def post_measurement_save(self):
        """
        save
            - analysis.yaml
            - analysis.monitor.yaml

        check if unique spectrometer.yaml
        commit changes
        push changes
        :return:
        """
        # save meta repo

        # save analysis
        t = datetime.now()
        self._save_analysis(t)
        self._save_analysis_db(t)

        # save monitor
        self._save_monitor()

        # save spectrometer
        spec_sha = self._get_spectrometer_sha()
        spec_path = self._make_path('.spectrometer', spec_sha)
        if not os.path.isfile(spec_path):
            self._save_spectrometer_file(spec_path)

        # stage files
        for p in (spec_path, self._make_path(''),
                  self._make_path('.peakcenter'),
                  self._make_path('.extraction'),
                  self._make_path('.monitor')):
            if os.path.isfile(p):
                self.project_repo.add(p)
            else:
                self.debug('not at valid file'.format(p))

        # commit files
        self.project_repo.commit('added analysis {}'.format(self.run_spec.runid))

        # push commit
        # self.project_repo.push()
        self.dvc.synchronize(pull=False)

    # private
    def _save_analysis_db(self, timestamp):
        # db = self.db
        # db.path = paths.meta_db
        # db.connect()

        d = self._make_analysis_dict()
        d['timestamp'] = timestamp
        with self.dvc.db.session_ctx():
            self.dvc.db.add_analysis(**d)

    def _make_analysis_dict(self):
        rs = self.run_spec
        attrs = ('sample', 'aliquot', 'increment', 'irradiation', 'weight',
                 'comment', 'irradiation_level', 'mass_spectrometer', 'extract_device',
                 'username', 'tray', 'queue_conditionals_name', 'extract_value',
                 'extract_units', 'position', 'xyz_position', 'duration', 'cleanup',
                 'pattern', 'beam_diameter', 'ramp_duration', 'ramp_rate')
        d = {k: getattr(rs, k) for k in attrs}
        return d

    def _save_analysis(self, timestamp):
        p = self._make_path('')
        isos = {}
        bs = {}
        for iso in self.arar_age.isotopes.values():
            sblob = ''
            isos[iso.name] = {'detector': {'name': iso.detector,
                                           'icFactor': nominal_value(iso.ic_factor),
                                           'icFactorErr': std_dev(iso.ic_factor)},
                              'fit': iso.fit,
                              'signal': sblob,
                              'blank': {'kind': 'previous',
                                        'runids': [self.previous_blank_runid],
                                        'value': iso.blank.value,
                                        'error': iso.blank.error}}
            if iso.detector not in bs:
                bblob = ''
                bs[iso.detector] = {'signal': bblob,
                                    'fit': iso.baseline.fit,
                                    'value': iso.baseline.value,
                                    'error': iso.baseline.error}

        obj = self._make_analysis_dict()
        obj['isotopes'] = isos
        obj['baselines'] = bs
        obj['timestamp'] = timestamp.isoformat()

        # save the scripts
        for si in ('measurement', 'extraction'):
            # s = getattr(self.run_spec, si)
            name = getattr(self, '{}_name'.format(si))
            blob = getattr(self, '{}_blob'.format(si))
            self.dvc.update_scripts(name, blob)

        # save experiment
        self.dvc.update_experiment(self.experiment_queue_name, self.experiment_queue_blob)
        self.dvc.meta_commit('repo updated for analysis {}'.format(self.run_spec.runid))

        hexsha = self.dvc.get_meta_head()
        obj['commit'] = hexsha

        ydump(obj, p)

    def _make_path(self, name, prefix=None, extension='.yaml'):
        if prefix is None:
            prefix = '{}'.format(self.runid)

        root = self.project_repo.path
        return os.path.join(root, '{}{}{}'.format(prefix, name, extension))

    def _get_spectrometer_sha(self):
        """
        return a sha-1 hash.

        generate using spec_dict, defl_dict, and gains
        spec_dict: source parameters, cdd operating voltagae
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
        for d in (self.spec_dict, self.defl_dict, self.gains):
            for k, v in sorted(d.items()):
                sha.update(k)
                sha.update(str(v))

        return sha.hexdigest()

    def _save_monitor(self):
        if self.monitor:
            p = self._make_path('.monitor')
            checks = []
            for ci in self.monitor.checks:
                data = ''.join([struct.pack('>ff', x, y) for x, y in ci.data])
                params = dict(name=ci.name,
                              parameter=ci.parameter, criterion=ci.criterion,
                              comparator=ci.comparator, tripped=ci.tripped,
                              data=data)
                checks.append(params)

            ydump(checks, p)

    def _save_spectrometer_file(self, path):
        obj = dict(spectrometer=self.spec_dict,
                   gains=self.gains,
                   deflections=self.defl_dict)
        ydump(obj, path)


# ============= EOF =============================================



