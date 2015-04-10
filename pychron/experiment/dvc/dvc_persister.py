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
import hashlib
import os
import struct

from traits.api import List, Dict, Instance


# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import std_dev
from uncertainties import nominal_value
import yaml
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.loggable import Loggable
from pychron.paths import paths


class DVCDatabase(DatabaseAdapter):
    kind = 'sqlite'


def ydump(obj, p):
    with open(p, 'w') as wfile:
        yaml.dump(obj, wfile, default_flow_style=False)


class DVCPersister(Loggable):
    db = Instance(DVCDatabase)
    project_repo = Instance(GitRepoManager)
    meta_repo = Instance(GitRepoManager)

    run_spec = Instance('pychron.automated_run.automated_run_spec.AutomatedRunSpec')
    monitor = None

    save_enabled = False
    spec_dict = Dict
    defl_dict = Dict
    gains = Dict

    active_detectors = List

    def initialize(self):
        """
        setup git repo
        :return:
        """
        self.project_repo = GitRepoManager()
        self.project_repo.open_repo(os.path.join(paths.project_dir,
                                                 self.run_spec.project))

        self.meta_repo = GitRepoManager()
        self.meta_repo.open_repo(paths.meta_dir)

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
        self._save_analysis()

        spec_md5 = self._get_spectrometer_md5()
        p = self._make_path('.spectrometer', spec_md5)
        if not os.path.isfile(p):
            self._save_spectrometer_file(p)

        self._save_monitor()

        for p in (self._make_path(''),
                  self._make_path('.peakcenter'),
                  self._make_path('.extraction'),
                  self._make_path('.monitor'),):
            if os.path.isfile(p):
                self.project_repo.add(p)
            else:
                self.debug('not at valid file'.format(p))

        self.project_repo.commit('added analysis {}'.format(self.run_spec.runid))

    # private
    def _save_analysis(self):
        p = self._make_path('')
        rs = self.run_spec
        attrs = ('sample', 'aliquot', 'increment', 'irradiation', 'weight',
                 'comment', 'irradiation_level', 'mass_spectrometer', 'extract_device',
                 'username', 'tray', 'queue_conditionals_name', 'extract_value',
                 'extract_units', 'position', 'xyz_position', 'duration', 'cleanup',
                 'pattern', 'beam_diameter', 'ramp_duration', 'ramp_rate')
        obj = {k: getattr(rs, k) for k in attrs}
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
                                        'value': iso.blank.value,
                                        'error': iso.blank.error}}
            if iso.detector not in bs:
                bblob = ''
                bs[iso.detector] = {'signal': bblob,
                                    'fit': iso.baseline.fit,
                                    'value': iso.baseline.value,
                                    'error': iso.baseline.error}
        obj['isotopes'] = isos
        obj['baselines'] = bs

        ydump(obj, p)

    def _make_path(self, name, prefix=None, extension='.yaml'):
        if prefix is None:
            prefix = '{}'.format(self.runid)

        root = self.project_repo.path
        return os.path.join(root, '{}{}{}'.format(prefix, name, extension))

    def _get_spectrometer_md5(self):
        md5 = hashlib.md5()
        for k, v in self.spec_dict.items():
            md5.update(k)
            md5.update(str(v))
        return md5.hexdigest()

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



