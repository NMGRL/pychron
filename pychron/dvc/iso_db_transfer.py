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
from traits.api import Instance
# ============= standard library imports ========================
from itertools import groupby
import time
import os
import json
# ============= local library imports  ==========================
# import yaml
from pychron.canvas.utils import make_geom

from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.dvc import jdump
from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.dvc_persister import DVCPersister, format_project
from pychron.dvc.meta_repo import MetaRepo
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.utilities.identifier import make_runid
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.github import Organization
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

# rfile = '''
# Ethiopia:
#   - 61666,01
#   - 61666,02
#   - 61666,03
#   - 61666,04
#   - 61666,05
#   - 61666,06
#   - 61666,07
#   - 61666,08
#   - 61666,09
#   - 61666,19
# '''
ORG = 'NMGRLData'


def create_github_repo(name):
    org = Organization(ORG)
    if not org.has_repo(name):
        with open('/Users/ross/Programming/githubauth.txt') as rfile:
            usr = rfile.readline().strip()
            pwd = rfile.readline().strip()

        org.create_repo(name, usr, pwd)


class IsoDBTransfer(Loggable):
    """
    transfer analyses from an isotope_db database to a dvc database
    """
    meta_repo = Instance(MetaRepo)
    root = None
    repo_man = Instance(GitRepoManager)

    def export_production(self, prodname, db=False):
        if db:
            pass

        # self.root = os.path.join(os.path.expanduser('~'), 'Pychron_dev', 'data', '.dvc')
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

    def do_export(self, create_repo=False):
        self.root = os.path.join(os.path.expanduser('~'), 'Pychron_dev', 'data', '.dvc')
        self.meta_repo = MetaRepo()
        self.meta_repo.open_repo(os.path.join(self.root, 'meta'))

        conn = dict(host='129.138.12.160', username='root', password='DBArgon', kind='mysql')
        # conn = dict(host='129.138.12.160', username='root', password='DBArgon', kind='mysql')
        # dest = DVCDatabase('/Users/ross/Sandbox/dvc/meta/testdb.sqlite')
        # dest = DVCDatabase(name='pychronmeta', **conn)
        self.dvc = DVC(bind=False,
                       meta_repo_name='meta')
        self.dvc.db.trait_set(name='pychronmeta', username='root',
                              password='Argon', kind='mysql', host='localhost')
        if not self.dvc.initialize():
            self.warning_dialog('Failed to initialize DVC')
            return

        self.persister = DVCPersister(dvc=self.dvc)

        dest = self.dvc.db

        proc = IsotopeDatabaseManager(bind=False, connect=False)
        proc.db.trait_set(name='pychrondata', **conn)
        src = proc.db
        # src = IsotopeAdapter(name='pychrondata', **conn)
        # src.trait_set()
        src.connect()
        with src.session_ctx():
            # for pr in yd:
            p = '/Users/ross/Sandbox/bustoswell_transfer.txt'
            experiment_id = 'J-Curve'
            experiment_id = 'Bustoswell'

            with open(p, 'r') as rfile:
                runs = [line.strip() for line in rfile if line.strip()]

            key = lambda x: x.split('-')[0]
            runs = sorted(runs, key=key)

            repo = self._add_experiment(dest, experiment_id, create_repo)
            self.persister.experiment_repo = repo
            self.dvc.experiment_repo = repo
            commit = False
            for ln, ans in groupby(runs, key=key):
                # print ln, len(list(ans))
                # # try:
                # #     int(ln)
                # # except ValueError:
                # #     self.debug('skipping {}'.format(ln))
                # #     continue
                # #
                if ln in ('4359',):
                    continue
                #
                # if ln not in ('bu', 'a', 'ba', 'c'):
                #     continue

                with dest.session_ctx():

                    for a in ans:
                        st = time.time()
                        if self._transfer_analysis(proc, src, dest, a, exp=experiment_id):
                            commit = True
                            print 'transfer time {:0.3f}'.format(time.time() - st)
                            # break
            if commit:
                repo.commit('<IMPORT> src= {}'.format(src.public_url))

    def transfer_holder(self, name):
        self.root = os.path.join(os.path.expanduser('~'), 'Pychron_dev', 'data', '.dvc')

        conn = dict(host='129.138.12.160', username='root', password='DBArgon', kind='mysql')
        # conn = dict(host='129.138.12.160', username='root', password='DBArgon', kind='mysql')
        # dest = DVCDatabase('/Users/ross/Sandbox/dvc/meta/testdb.sqlite')
        # dest = DVCDatabase(name='pychronmeta', **conn)
        # self.dvc = DVC(bind=False)
        # self.dvc.db.trait_set(name='pychronmeta', username='root',
        #                       password='Argon', kind='mysql', host='localhost')

        self.meta_repo = MetaRepo()
        self.meta_repo.open_repo(os.path.join(self.root, 'meta'))
        proc = IsotopeDatabaseManager(bind=False, connect=False)
        proc.db.trait_set(name='pychrondata', **conn)
        src = proc.db
        # src = IsotopeAdapter(name='pychrondata', **conn)
        # src.trait_set()
        src.connect()
        with src.session_ctx():
            holder = src.get_irradiation_holder(name)

            self.meta_repo.add_irradiation_holder(name, holder.geometry)

    def _add_experiment(self, dest, experiment_id, create_repo):
        experiment_id = format_project(experiment_id)

        proot = os.path.join(paths.experiment_dataset_dir, experiment_id)
        if not os.path.isdir(proot):
            os.mkdir(proot)

        if self.repo_man is None or self.repo_man.path != proot:
            repo = GitRepoManager()
            repo.open_repo(proot)

            repo.add_ignore('.DS_Store')
            self.repo_man = repo
            if create_repo:
                create_github_repo(experiment_id)

            url = 'https://github.com/{}/{}.git'.format(ORG, experiment_id)
            repo.create_remote(url)

        if not dest.get_experiment(experiment_id):
            dest.add_experiment(name=experiment_id)
            dest.flush()

        return self.repo_man
        # def _transfer_labnumber(self, ln, src, dest, exp=None, create_repo=False):
        # if exp is None:
        #     dbln = src.get_labnumber(ln)
        #     exp = dbln.sample.project.name
        #     # if exp in ('Chevron', 'J-Curve'):
        #     if exp in ('Chevron',):  # 'J-Curve'):
        #         return
        #

        # if not dest.get_experiment(exp):
        #     dest.add_experiment(name=exp)
        #     dest.flush()
        # if not dest.get_project(project):
        #     dest.add_project(project)

        # return self.repo_man

    # def _export_project(self, project, src, dest):
    #     proot = os.path.join(self.root, 'projects', project)
    #     # proot = os.path.join(paths.dvc_dir, 'projects', project)
    #     if not os.path.isdir(proot):
    #         os.mkdir(proot)
    #     repo = GitRepoManager()
    #     repo.open_repo(proot)
    #
    #     if not dest.get_project(project):
    #         dest.add_project(project)
    #
    #     return repo

    def _transfer_meta(self, dest, dban):
        # with dest.session_ctx():
        dblab = dban.labnumber
        dbsam = dblab.sample
        project = dbsam.project.name
        project = project.replace('/', '_').replace('\\', '_')

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

        dbirradpos = dblab.irradiation_position
        if not dbirradpos:
            irradname = 'NoIrradiation'
            levelname = 'A'
            holder = 'Grid'
            pos = None
            identifier = dblab.identifier
            doses = []
            prod = None
            prodname = 'NoIrradiation'

            geom = make_geom([(0, 0, 0.0175),
                              (1, 0, 0.0175),
                              (2, 0, 0.0175),
                              (3, 0, 0.0175),
                              (4, 0, 0.0175),

                              (0, 1, 0.0175),
                              (1, 1, 0.0175),
                              (2, 1, 0.0175),
                              (3, 1, 0.0175),
                              (4, 1, 0.0175),

                              (0, 2, 0.0175),
                              (1, 2, 0.0175),
                              (2, 2, 0.0175),
                              (3, 2, 0.0175),
                              (4, 2, 0.0175),

                              (0, 3, 0.0175),
                              (1, 3, 0.0175),
                              (2, 3, 0.0175),
                              (3, 3, 0.0175),
                              (4, 3, 0.0175),

                              (0, 4, 0.0175),
                              (1, 4, 0.0175),
                              (2, 4, 0.0175),
                              (3, 4, 0.0175),
                              (4, 4, 0.0175)
                              ])
        else:
            dblevel = dbirradpos.level
            dbirrad = dblevel.irradiation
            dbchron = dbirrad.chronology

            irradname = dbirrad.name
            levelname = dblevel.name
            holder = dblevel.holder.name
            prodname = dblevel.production.name
            pos = dbirradpos.position
            doses = dbchron.get_doses()
            prod = dblevel.production
            geom = dblevel.holder.geometry

        # save db irradiation
        if not dest.get_irradiation(irradname):
            dest.add_irradiation(irradname)
            dest.flush()

            self.meta_repo.add_irradiation(irradname)
            self.meta_repo.add_chronology(irradname, doses)
            self.meta_repo.commit('added irradiation {}'.format(irradname))

        # save production name to db
        if not dest.get_production(prodname):
            dest.add_production(prodname)
            dest.flush()

            self.meta_repo.add_production(prodname, prod)
            self.meta_repo.commit('added production {}'.format(prodname))

        # save db level
        if not dest.get_irradiation_level(irradname, levelname):
            dest.add_irradiation_level(levelname, irradname, holder, prodname)
            dest.flush()

            self.meta_repo.add_irradiation_holder(holder, geom)
            self.meta_repo.add_level(irradname, levelname)
            self.meta_repo.commit('added empty level {}{}'.format(irradname, levelname))

        if pos is None:
            pos = self._get_irradpos(dest, irradname, levelname, identifier)

        # save db irradiation position
        if not dest.get_irradiation_position(irradname, levelname, pos):
            p = self.meta_repo.get_level_path(irradname, levelname)
            with open(p, 'r') as rfile:
                yd = json.load(rfile)

            dd = dest.add_irradiation_position(irradname, levelname, pos)
            dd.identifier = dblab.identifier
            dd.sample = sam

            dest.flush()
            try:
                f = dban.labnumber.selected_flux_history.flux
                j, e = f.j, f.j_err
            except AttributeError:
                j, e = 0, 0

            yd.append({'j': j, 'j_err': e, 'position': pos})
            jdump(yd, p)
            # with open(p, 'w') as wfile:
            #     json.dump(yd, wfile, indent=4)

    def _transfer_analysis(self, proc, src, dest, rec, exp=None, overwrite=True):
        # args = rec.split(',')
        # if len(args) == 2:
        #     idn, aliquot = args
        #     step = None
        # else:
        #     idn, aliquot, step = args
        args = rec.split('-')
        idn = '-'.join(args[:-1])
        t = args[-1]
        try:
            aliquot = int(t)
            step = None
        except ValueError:
            aliquot = int(t[:-1])
            step = t[-1]

        if dest.get_analysis_runid(idn, aliquot, step):
            self.warning('{} already exists'.format(make_runid(idn, aliquot, step)))
            return
        # st = time.time()
        dban = src.get_analysis_runid(idn, aliquot, step)
        iv = IsotopeRecordView()
        iv.uuid = dban.uuid
        an = proc.make_analysis(iv, unpack=True, use_cache=False)
        # print 'make analysis time {:0.5f}'.format(time.time() - st)

        # op = os.path.join(repo.path, add_extension(dban.record_id, '.yaml'))
        # if os.path.isfile(op) and not overwrite:
        #     self.debug('{} already exists. skipping'.format(op))
        #     return

        # st = time.time()
        self._transfer_meta(dest, dban)
        # print 'transfer meta {:0.5f}'.format(time.time() - st)

        dblab = dban.labnumber
        dbsam = dblab.sample

        if dblab.irradiation_position:
            irrad = dblab.irradiation_position.level.irradiation.name
            level = dblab.irradiation_position.level.name
            irradpos = dblab.irradiation_position.position
        else:
            irrad = 'NoIrradiation'
            level = 'A'
            irradpos = self._get_irradpos(dest, irrad, level, dblab.identifier)
            # irrad, level, irradpos = '', '', 0

        sample = dbsam.name
        mat = dbsam.material.name
        project = format_project(dbsam.project.name)
        extraction = dban.extraction
        ms = dban.measurement.mass_spectrometer.name
        if not dest.get_mass_spectrometer(ms):
            dest.add_mass_spectrometer(ms, )

        # isotopes = self._make_isotopes(dban)
        # detectors = self._make_detectors(dban)
        if step is None:
            inc = -1
        else:
            inc = ALPHAS.index(step)

        username = ''
        if dban.user:
            username = dban.user.name
            if not dest.get_user(username):
                dest.add_user(username)
                dest.flush()

        rs = AutomatedRunSpec(labnumber=idn,
                              username=username,
                              material=mat,
                              project=project,
                              sample=sample,
                              irradiation=irrad,
                              irradiation_level=level,
                              irradiation_position=irradpos,
                              experiment_id=exp or project,
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

                              collection_version='0.1:0.1',
                              queue_conditionals_name='',
                              tray='')

        ps = PersistenceSpec(run_spec=rs,
                             tag=an.tag,
                             arar_age=an,
                             timestamp=dban.analysis_timestamp,
                             use_experiment_association=True,
                             positions=[p.position for p in extraction.positions])

        self.persister.per_spec_save(ps, commit=False, msg_prefix='Database Transfer')
        return True
        # self._save_an_to_db(dest, dban, obj)
        # # op = os.path.join(proot, add_extension(dban.record_id, '.yaml'))
        # with open(op, 'w') as wfile:
        #     yaml.dump(obj, wfile)
        #
        # repo.add(op, commit=False)

        # def _save_an_to_db(self, dest, dban, obj):
        #     kw = {k: obj.get(k) for k in ('aliquot', 'uuid',
        #                                   'weight', 'comment',
        #                                   'timestamp', 'analysis_type',
        #                                   'mass_spectrometer', 'extract_device',
        #                                   )}
        #
        #     an = dest.add_analysis(**kw)
        #
        #     dblab = dban.labnumber
        #     irrad = dblab.irradiation_position.level.irradiation.name
        #     level = dblab.irradiation_position.level.name
        #     irradpos = dblab.irradiation_position.position
        #
        #     pos = dest.get_irradiation_position(irrad, level, irradpos)
        #     an.irradiation_position = pos

        # def _make_isotopes(self, dban):
        #     isos = {}
        #     for dbiso in dban.isotopes:
        #         if dbiso.kind == 'signal':
        #             isod = self._make_isotope(dbiso)
        #             isos[dbiso.molecular_weight.name] = isod
        #     return isos
        #
        # def _make_detectors(self, dban):
        #     dets = {}
        #     for iso in dban.isotopes:
        #         det = iso.detector.name
        #         if det in dets:
        #             continue
        #
        #         dets[det] = dict(ic_factor=dict(fit='default',
        #                                         value=1,
        #                                         error=0.001,
        #                                         references=[]),
        #                          baseline={'signal': '',
        #                                    'value': 0,
        #                                    'error': 0})
        #
        #     return dets
        #
        # def _make_isotope(self, dbiso):
        #
        #     d = dbiso.signal.data
        #
        #     isod = dict(fit='', detector=dbiso.detector.name,
        #                 # baseline=self._pack_baseline(dbiso),
        #                 signal=base64.b64encode(d),
        #                 baseline_corrected=self._make_baseline_corrected(dbiso),
        #                 raw_intercept=self._make_raw_intercept(dbiso))
        #     return isod
        #
        # def _make_baseline_corrected(self, dbiso):
        #     return dict(value=0, error=0)
        #
        # def _make_raw_intercept(self, dbiso):
        #     try:
        #         r = dbiso.results[-1]
        #         v, e = r.signal, r.signal_err
        #
        #     except BaseException:
        #         v, e = 0, 0
        #
        #     return dict(value=v, error=e)
        #
        #     # def _pack_baseline(self, dbiso):
        #     # xs, ys = [], []
        #     # return self._pack_data(xs, ys)
        #     #
        #     # def _pack_signal(self, dbiso):
        #     #     xs, ys = [], []
        #     #     return self._pack_data(xs, ys)
        #
        #     # def _pack_data(self, xs, ys):
        #     #     return base64.b64encode(''.join((struct.pack('>ff', x, y) for x, y in zip(xs, ys))))

    def _get_irradpos(self, dest, irradname, levelname, identifier):
        dl = dest.get_irradiation_level(irradname, levelname)
        pos = 1
        if dl.positions:
            for p in dl.positions:
                if p.identifier == identifier:
                    pos = p.position
                    break
            else:
                pos = dl.positions[-1].position + 1

        return pos


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build('_dev')
    logging_setup('de', root=os.path.join(os.path.expanduser('~'), 'Desktop', 'logs'))
    # exp = 'J-Curve'
    # url = 'https://github.com/{}/{}.git'.format(org.name, exp)
    e = IsoDBTransfer()
    # e.transfer_holder('40_no_spokes')
    # e.transfer_holder('40_hole')
    # e.transfer_holder('24_hole')
    e.do_export(create_repo=False)
    # e.export_production('Triga PR 275', db=False)
# ============= EOF =============================================
