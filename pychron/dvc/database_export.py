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
import struct

from traits.api import Instance


# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.meta_repo import MetaRepo
from pychron.experiment.utilities.identifier import get_analysis_type
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import ALPHAS

input_txt = '''
Foo:
  - 5000,01
  - 5000,02

'''


class DatabaseExport(Loggable):
    meta_repo = Instance(MetaRepo)

    def do_export(self):
        self.meta_repo = MetaRepo()

        dest = DVCDatabase()

        src = IsotopeAdapter()
        src.trait_set(host='localhost', user='root', password='DBArgon', kind='mysql')
        src.connect()
        p = ''
        with src.session_ctx():
            with open(p, 'r') as rfile:
                yd = yaml.load(rfile)

                for pr in yd:
                    with dest.session_ctx():
                        repo = self._export_project(pr, src, dest)
                        for rec in yd[pr]:
                            self._export_analysis(src, dest, repo, rec)

                        repo.commit('src import src= {}'.format(src.url))

    def _export_project(self, project, src, dest):
        proot = os.path.join(paths.dvc_dir, 'projects', project)
        if not os.path.isdir(proot):
            os.mkdir(proot)
        repo = GitRepoManager()
        repo.open_repo(proot)

        if not dest.get_project(project):
            dest.add_project(project)

        return repo

    def _export_meta(self, dest, dban):
        dblab = dban.labnumber
        dbirradpos = dblab.irradiation_position
        dblevel = dbirradpos.level
        dbirrad = dblevel.irradiation
        dbchron = dbirrad.chronology

        irradname = dbirrad.name
        levelname = dblevel.name
        holder = dblevel.holder.name
        prodname = dblevel.production.name
        pos = dbirradpos.position

        # export irradiation to meta
        self.meta_repo.add_irradiation(irradname)
        # export chronology to irrad
        self.meta_repo.add_chronology(irradname, dbchron.get_doses())
        # export production
        self.meta_repo.add_production(prodname, dblevel.production)

        self.meta_repo.commit('added irradiation {}'.format(irradname))

        with dest.session_ctx():
            # save db irradiation
            if not dest.get_irradiation(irradname):
                dest.add_irradiation(irradname)
                dest.flush()

            # save production name to db
            if not dest.get_production(prodname):
                dest.add_production(prodname)
                dest.flush()

            # save db level
            if not dest.get_irradiation_level(irradname, levelname):
                dest.add_irradiation_level(levelname, irradname, holder, prodname)
                dest.flush()

            # save db irradiation position
            if not dest.get_irradiation_position(irradname, levelname, pos):
                dd = dest.add_irradiation_position(irradname, levelname, pos)
                dd.identifier = dblab.identifier
                dbsam = dblab.sample
                project = dbsam.project.name
                if not dest.get_sample(dbsam.name, project):
                    mat = dbsam.material.name
                    if not dest.get_material(mat):
                        dest.add_material(mat)
                        dest.flush()

                    if not dest.get_project(project):
                        dest.add_project(project)
                        dest.flush()

                    dest.add_sample(dbsam.name, project, mat)
                    dest.flush()
                dest.flush()

    def _export_analysis(self, src, dest, repo, rec, overwrite=True):

        args = rec.split(',')
        if len(args) == 2:
            idn, aliquot = args
            step = None
        else:
            idn, aliquot, step = args

        dban = src.get_analysis(idn, aliquot, step)
        op = os.path.join(repo.path, add_extension(dban.record_id, '.yaml'))
        if os.path.isfile(op) and not overwrite:
            self.debug('{} already exists. skipping'.format(op))
            return

        self._export_meta(dest, dban)

        dblab = dban.labnumber
        dbsam = dblab.sample

        irrad = dblab.irradiation_position.level.irradiation.name
        level = dblab.irradiation_position.level.name
        irradpos = dblab.irradiation_position.position
        sample = dbsam.name
        mat = dbsam.material.name
        project = dbsam.project.name
        extraction = dban.extraction
        ms = dban.measurement.mass_spectrometer.name

        isotopes = self._make_isotopes(dban)
        if step is None:
            inc = None
        else:
            inc = ALPHAS.index(step)

        obj = dict(identifier=idn, uuid=dban.uuid, aliquot=aliquot, isotopes=isotopes,
                   analysis_type=get_analysis_type(idn),
                   collection_version='0.1:0.1', comment='This is a comment', increment=inc, irradiation=irrad,
                   irradiation_level=level, irradiation_position=irradpos, project=project, mass_spectrometer=ms,
                   material=mat, duration=extraction.extract_duration, cleanup=extraction.cleanup_duration,
                   beam_diameter=extraction.beam_diameter, extract_device=extraction.extraction_device.name,
                   extract_units=extraction.extract_units, extract_value=extraction.extract_value,
                   pattern=extraction.pattern,
                   position=[{k: getattr(p, k) for k in ('x', 'y', 'z', 'position', 'is_degas')}
                             for p in extraction.positions], weight=extraction.weight,
                   ramp_duration=extraction.ramp_duration, ramp_rate=extraction.ramp_rate, queue_conditionals_name=None,
                   sample=sample, timestamp=dban.analysis_timestamp, tray=None, username=dban.user.name,
                   xyz_position=None)

        self._save_an_to_db(dest, dban, obj)
        # op = os.path.join(proot, add_extension(dban.record_id, '.yaml'))
        with open(op, 'w') as wfile:
            yaml.dump(obj, wfile)

        repo.add(op, commit=False)

    def _save_an_to_db(self, dest, dban, obj):
        kw = obj.fromkeys(('aliquot', 'uuid',
                           'weight', 'comment',
                           'timestamp', 'analysis_type',
                           'mass_spectrometer', 'extract_device'))

        an = dest.add_analysis(**kw)

        dblab = dban.labnumber
        irrad = dblab.irradiation_position.level.irradiation.name
        level = dblab.irradiation_position.level.name
        irradpos = dblab.irradiation_position.position
        pos = dest.get_irradiation_position(irrad, level, irradpos)
        an.irradiation_position = pos

    def _make_isotopes(self, dban):
        isos = {}
        for dbiso in dban.isotopes:
            isod = self._make_isotope(dbiso)
            isos[dbiso.molecular_weight.name] = isod
        return isos

    def _make_isotope(self, dbiso):
        isod = dict(fit='', detector=self._make_detector(dbiso),
                    baseline=self._pack_baseline(dbiso),
                    signal=self._pack_signal(dbiso),
                    baseline_corrected=self._make_baseline_corrected(dbiso),
                    raw_intercept=self._make_raw_intercept(dbiso))
        return isod

    def _make_detector(self, dbiso):
        return dict(deflection=0, gain=0, name=dbiso.detector.name)

    def _make_baseline_corrected(self, dbiso):
        return dict(value=0, error=0)

    def _make_raw_intercept(self, dbiso):
        return dict(value=0, error=0)

    def _pack_baseline(self, dbiso):
        xs, ys = [], []
        return self._pack_data(xs, ys)

    def _pack_signal(self, dbiso):
        xs, ys = [], []
        return self._pack_data(xs, ys)

    def _pack_data(self, xs, ys):
        return base64.b64encode(''.join((struct.pack('>ff', x, y) for x, y in zip(xs, ys))))

# ============= EOF =============================================
