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
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension

from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.dvc_persister import DVCPersister
from pychron.dvc.meta_repo import MetaRepo
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import ALPHAS

rfile = '''
J-Curve:
  - 24322,01
  - 24322,02
  - 24322,03
  - 24322,04
  - 24322,05
  - 24322,06
'''

rfile = '''
Ethiopia:
  - 61666,01
  - 61666,02
  - 61666,03
  - 61666,04
  - 61666,05
  - 61666,06
  - 61666,07
  - 61666,08
  - 61666,09
  - 61666,19
'''


class IsoDBTransfer(Loggable):
    """
    transfer analyses from an isotope_db database to a dvc database
    """
    meta_repo = Instance(MetaRepo)
    root = None

    def export_production(self, prodname, db=False):
        if db:
            pass

        self.root = os.path.join(os.path.expanduser('~'), 'Pychron_dev', 'data', '.dvc')
        self.meta_repo = MetaRepo(os.path.join(self.root, 'meta'))

        conn = dict(host='129.138.12.160', username='root', password='DBArgon', kind='mysql')
        # dest = DVCDatabase('/Users/ross/Sandbox/dvc/meta/testdb.sqlite')
        dest = DVCDatabase(name='pychronmeta', **conn)
        dest.connect()
        src = IsotopeAdapter(name='pychrondata', **conn)
        # src.trait_set()
        src.connect()
        with src.session_ctx():
            if not dest.get_production(prodname):
                dest.add_production(prodname)
                dest.flush()

                dbprod = src.get_irradiation_production(prodname)
                self.meta_repo.add_production(prodname, dbprod)
                self.meta_repo.commit('added production {}'.format(prodname))

    def do_export(self):
        self.root = os.path.join(os.path.expanduser('~'), 'Pychron_dev', 'data', '.dvc')
        self.meta_repo = MetaRepo(os.path.join(self.root, 'meta'))

        conn = dict(host='129.138.12.160', username='root', password='DBArgon', kind='mysql')
        # conn = dict(host='129.138.12.160', username='root', password='DBArgon', kind='mysql')
        # dest = DVCDatabase('/Users/ross/Sandbox/dvc/meta/testdb.sqlite')
        # dest = DVCDatabase(name='pychronmeta', **conn)
        self.dvc = DVC(bind=False)
        self.dvc.db.trait_set(name='pychronmeta', **conn)
        dest = self.dvc.db
        dest.connect()

        proc = IsotopeDatabaseManager(bind=False, connect=False)
        proc.db.trait_set(name='pychrondata', **conn)
        src= proc.db
        # src = IsotopeAdapter(name='pychrondata', **conn)
        # src.trait_set()
        src.connect()
        with src.session_ctx():
            # with open(p, '') as rfile:
            yd = yaml.load(rfile)

            for pr in yd:
                with dest.session_ctx():
                    repo = self._export_project(pr, src, dest)
                    self.dvc.project_repo=repo
                    for rec in yd[pr]:
                        self._export_analysis(proc, src, dest, repo, rec)

                    repo.commit('src import src= {}'.format(src.url))

    def _export_project(self, project, src, dest):
        proot = os.path.join(self.root, 'projects', project)
        # proot = os.path.join(paths.dvc_dir, 'projects', project)
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

        with dest.session_ctx():
            # save db irradiation
            if not dest.get_irradiation(irradname):
                dest.add_irradiation(irradname)
                dest.flush()

                self.meta_repo.add_irradiation(irradname)
                self.meta_repo.add_chronology(irradname, dbchron.get_doses())
                self.meta_repo.commit('added irradiation {}'.format(irradname))

            # save production name to db
            if not dest.get_production(prodname):
                dest.add_production(prodname)
                dest.flush()

                self.meta_repo.add_production(prodname, dblevel.production)
                self.meta_repo.commit('added production {}'.format(prodname))

            # save db level
            if not dest.get_irradiation_level(irradname, levelname):
                dest.add_irradiation_level(levelname, irradname, holder, prodname)
                dest.flush()

            # save db irradiation position
            if not dest.get_irradiation_position(irradname, levelname, pos):
                dbsam = dblab.sample
                project = dbsam.project.name
                sam = dest.get_sample(dbsam.name, project)
                if not sam:
                    mat = dbsam.material.name
                    if not dest.get_material(mat):
                        dest.add_material(mat)
                        dest.flush()

                    if not dest.get_project(project):
                        dest.add_project(project)
                        dest.flush()

                    sam = dest.add_sample(dbsam.name, project, mat)
                    dest.flush()

                dd = dest.add_irradiation_position(irradname, levelname, pos)
                dd.identifier = dblab.identifier
                dd.sample = sam

                dest.flush()

    def _export_analysis(self, proc, src, dest, repo, rec, overwrite=True):
        self.persister = DVCPersister(dvc=self.dvc)

        args = rec.split(',')
        if len(args) == 2:
            idn, aliquot = args
            step = None
        else:
            idn, aliquot, step = args

        # if dest.get_analysis_runid(idn, aliquot, step):
        #     return

        dban = src.get_analysis_runid(idn, aliquot, step)
        iv = IsotopeRecordView()
        iv.uuid = dban.uuid
        an = proc.make_analysis(iv, unpack=True)

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
        # isotopes = self._make_isotopes(dban)
        # detectors = self._make_detectors(dban)
        if step is None:
            inc = -1
        else:
            inc = ALPHAS.index(step)

        username = ''
        if dban.user:
            username = dban.user.name

        rs = AutomatedRunSpec(labnumber=idn,
                              username=username,
                              material=mat,
                              project=project,
                              sample=sample,
                              irradiation=irrad,
                              irradiation_level=level,
                              irradiation_position=irradpos,

                              mass_spectrometer=ms,
                              uuid=dban.uuid,
                              _step=inc,
                              comment=dban.comment,
                              aliquot=int(aliquot),

                              extract_device=extraction.extraction_device.name,
                              duration=extraction.extract_duration,
                              cleanup=extraction.cleanup_duration,
                              beam_diameter=extraction.beam_diameter,
                              extract_units=extraction.extract_units or '',
                              extract_value=extraction.extract_value,
                              pattern=extraction.pattern or '',
                              weight=extraction.weight,
                              ramp_duration=extraction.ramp_duration or 0,
                              ramp_rate=extraction.ramp_rate or 0,
                              timestamp=dban.analysis_timestamp,

                              collection_version='0.1:0.1',
                              queue_conditionals_name='',
                              tray='')

        ps = PersistenceSpec(run_spec=rs,
                             arar_age=an,
                             positions=[p.position for p in extraction.positions])
        self.persister.per_spec_save(ps)

        # self._save_an_to_db(dest, dban, obj)
        # # op = os.path.join(proot, add_extension(dban.record_id, '.yaml'))
        # with open(op, 'w') as wfile:
        #     yaml.dump(obj, wfile)
        #
        # repo.add(op, commit=False)

    def _save_an_to_db(self, dest, dban, obj):
        kw = {k: obj.get(k) for k in ('aliquot', 'uuid',
                                      'weight', 'comment',
                                      'timestamp', 'analysis_type',
                                      'mass_spectrometer', 'extract_device')}

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
            if dbiso.kind == 'signal':
                isod = self._make_isotope(dbiso)
                isos[dbiso.molecular_weight.name] = isod
        return isos

    def _make_detectors(self, dban):
        dets = {}
        for iso in dban.isotopes:
            det = iso.detector.name
            if det in dets:
                continue

            dets[det] = dict(ic_factor=dict(fit='default',
                                            value=1,
                                            error=0.001,
                                            references=[]),
                             baseline={'signal': '',
                                       'value': 0,
                                       'error': 0})

        return dets

    def _make_isotope(self, dbiso):

        d = dbiso.signal.data

        isod = dict(fit='', detector=dbiso.detector.name,
                    # baseline=self._pack_baseline(dbiso),
                    signal=base64.b64encode(d),
                    baseline_corrected=self._make_baseline_corrected(dbiso),
                    raw_intercept=self._make_raw_intercept(dbiso))
        return isod

    def _make_baseline_corrected(self, dbiso):
        return dict(value=0, error=0)

    def _make_raw_intercept(self, dbiso):
        try:
            r = dbiso.results[-1]
            v, e = r.signal, r.signal_err

        except BaseException:
            v, e = 0, 0

        return dict(value=v, error=e)

        # def _pack_baseline(self, dbiso):
        # xs, ys = [], []
        # return self._pack_data(xs, ys)
        #
        # def _pack_signal(self, dbiso):
        #     xs, ys = [], []
        #     return self._pack_data(xs, ys)

        # def _pack_data(self, xs, ys):
        #     return base64.b64encode(''.join((struct.pack('>ff', x, y) for x, y in zip(xs, ys))))


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    paths.build('_dev')
    logging_setup('de', root=os.path.join(os.path.expanduser('~'), 'Desktop', 'logs'))
    e = IsoDBTransfer()
    e.do_export()
    # e.export_production('Triga PR 275', db=False)
# ============= EOF =============================================
