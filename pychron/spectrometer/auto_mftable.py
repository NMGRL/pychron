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
from traits.api import HasTraits, Button, Str, Int, Bool, Instance
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
import shutil
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.loggable import Loggable
from pychron.paths import paths


class AutoMFTable(Loggable):
    ion_optics_manager = Instance('pychron.spectrometer.ion_optics_manager.IonOpticsManager')
    el_manager = Instance('pychron.extraction_line.extraction_line_manager.ExtractionLineManager')
    pyscript_task = Instance('pychron.pyscript.tasks.pyscript_task.PyScriptTask')
    spectrometer_manager = Instance('pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager')

    def do_auto_mftable(self, path=None):
        yd = self._load_config(path)
        if yd:

            if not self._prepare(yd['extraction']):
                self.warning('Failed preparing system')
                return

            with self._ctx():
                dets = yd['detectors']
                refiso = yd['reference_isotope']
                if self._construct_mftable(dets, yd['isotopes']):
                    self._backup_deflection(reset=True)

                    defls = yd['deflections']
                    self._construct_deflection(dets, defls, refiso)

        else:
            self.debug('Failed loading configuration')

    def _set_config_deflections(self):
        self.debug('setting deflections to config values')

    def _do_peak_center(self, detector, isotope, save=True):
        ion = self.ion_optics_manager

        pc = ion.setup_peak_center(detector=[detector],
                                   isotope=isotope, new=True)
        ion.do_peak_center(new_thread=False, save=save, message='automated run peakcenter')
        pcr = ion.peak_center_result
        if pcr:
            pc.close_graph()
        return pcr

    def _construct_deflection(self, dets, defls, refiso):
        for di in dets:
            try:
                defli = defls[di]
                if not isinstance(defli, tuple):
                    defli = (defli,)
            except KeyError:
                self.warning('No deflection for {}. using 100 as default'.format(di))
                defli = (100,)

            for de in defli:
                if de == 0:
                    self._update_deflection_file_from_mftable(di, refiso)
                    self.info('Deflection=0. Using mftable value for {}'.format(di))
                else:
                    self.info('calculating peak center for {} on {}. deflection={}'.format(refiso,
                                                                                           di, de))
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
        self.debug('get deflection for {}'.format(det))
        return self.spectrometer_man.get_deflection(det)

    def _set_deflection(self, det, defl):
        self.debug('setting deflection. det={}, defl={}'.format(det, defl))
        self.spectrometer_man.set_deflection(det, defl)

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

    def _prepare(self, extraction_script):
        extraction_script = add_extension(extraction_script)
        task = self.pyscript_task
        root, name = os.path.split(extraction_script)
        ctx = {'analysis_type': 'blank' if 'blank' in name else 'unknown'}
        ret = task.execute_script(name, root, new_thread=False, context=ctx)
        self.info('Extraction script {} {}'.format(name, 'completed successfully' if ret else 'failed'))
        return ret

    @contextmanager
    def _ctx(self):
        # enter
        self._backup_mftable()

        yield

        # exit
        # return to original deflections
        self._set_config_deflections()

# ============= EOF =============================================



