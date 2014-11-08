# ===============================================================================
# Copyright 2014 Jake Ross
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
from contextlib import contextmanager
from traits.api import HasTraits, Button, Str, Int, Bool
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
import shutil
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path2
from pychron.loggable import Loggable
from pychron.paths import paths


class AutoMFTable(Loggable):
    def do_auto_mftable(self, path=None):
        yd = self._load_config(path)
        if yd:
            with self.ctx():
                dets = yd['detectors']
                refiso = yd['reference_isotope']
                if self._construct_mftable(dets, yd['isotopes']):
                    self._backup_deflection(reset=True)

                    defls = yd['deflections']
                    self._construct_deflection(dets, defls, refiso)

        else:
            self.debug('Failed loading configuration')

    @contextmanager
    def ctx(self):
        #enter
        self._backup_mftable()

        yield

        #exit
        #return to original deflections
        self._set_config_deflections()

    def _set_config_deflections(self):
        self.debug('setting deflections to config values')

    def _do_peak_center(self, detector, isotope, save=True):
        return True

    def _construct_deflection(self, dets, defls, refiso):
        for di, defli in zip(dets, defls):
            if not isinstance(defli, tuple):
                defli = (defli, )

            for de in defli:
                if de == 0:
                    self._update_deflection_file_from_mftable(di, refiso)
                else:
                    self._set_deflection(di, de)
                    pc = self._do_peak_center(di, refiso, save=False)
                    if pc:
                        self._update_deflection(di, de, pc)

    def _construct_mftable(self, dets, isos):

        pc = self._do_peak_center(dets[0], isos[0])
        if not pc:
            self.warning('Failed reference peak center')
            return

        skipref = self._current_deflection(dets[0]) == 0
        for i, di in enumerate(dets):
            for j, iso in enumerate(isos):
                if i == 0 and j == 0 and skipref:
                    continue
                self._set_deflection(di, 0)
                self._do_peak_center(di, iso)

    def _current_deflection(self, det):
        return 0

    def _set_deflection(self, det, defl):
        self.debug('setting deflection. det={}, defl={}'.format(det, defl))

    def _update_deflection_file_from_mftable(self, di, refiso):
        dac = self.mftable.get_dac(di, refiso)
        self._update_deflection(di, 0, dac)

    def _update_deflection(self, di, defl, dac):
        self.debug('Update deflection det={},defl={} dac={}'.format(di, defl, dac))
        p = paths.deflection
        with open(p, 'r') as fp:
            yd = yaml.load(fp)

        dd = yd[di]

        defls = dd['deflections'].split(',')
        defls.append(defl)

        dacs = dd['dacs'].split(',')
        dacs.append(dac)

        yd['deflections'] = ','.join(defls)
        yd['dacs'] = ','.join(dacs)

        with open(p, 'w') as fp:
            yaml.dump(yd, fp, default_flow_style=False)

    def _backup_mftable(self):
        src = paths.mftable
        head, tail = os.path.split(src)
        dst = os.path.join(head, '~{}'.format(tail))
        self.debug('backing up {} to {}'.format(src, dst))
        shutil.copyfile(src, dst)

    def _backup_deflection(self, reset=False):
        src = paths.deflection
        if src:

            dst = unique_path2(paths.backup_deflection_dir)
            self.debug('backing up {} to {}'.format(src, dst))
            shutil.copyfile(src, dst)

            if reset:
                with open(src, 'r') as fp:
                    yd = yaml.load(fp)
                    nd = {}
                    for k in yd:
                        nd[k] = {'deflections': '', 'dacs': ''}

                with open(src, 'w') as fp:
                    yaml.dump(nd, fp, default_flow_style=False)

    def _load_config(self, path):
        with open(path, 'r') as fp:
            yd = yaml.load(fp)

        try:
            yd['detectors'] = [di.strip() for di in yd['detectors'].split(',')]
            yd['isotopes'] = [iso.strip() for iso in yd['isotopes'].split(',')]
            yd['deflections'] = eval(yd['deflections'])
        except BaseException, e:
            self.debug('failed parsing config file {}. exception={}'.format(path, e))
        return yd

# ============= EOF =============================================



