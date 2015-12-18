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
import json
import os
import time
from itertools import groupby

from datetime import timedelta
# ============= local library imports  ==========================
from numpy import array, array_split
from pychron.canvas.utils import make_geom
from pychron.core.helpers.datetime_tools import make_timef, bin_timestamps, get_datetime
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.dvc import dvc_dump
from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_persister import DVCPersister, format_experiment_identifier
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.utilities.identifier import make_runid, IDENTIFIER_REGEX, SPECIAL_IDENTIFIER_REGEX
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.github import Organization
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import ALPHAS

ORG = 'NMGRLData'


def create_github_repo(name):
    org = Organization(ORG)
    if not org.has_repo(name):
        usr = os.environ.get('GITHUB_USER')
        pwd = os.environ.get('GITHUB_PWD')
        org.create_repo(name, usr, pwd)


class IsoDBTransfer(Loggable):
    """
    transfer analyses from an isotope_db database to a dvc database
    """
    # meta_repo = Instance(MetaRepo)
    # root = None
    # repo_man = Instance(GitRepoManager)
    quiet = False

    def init(self):
        self._init_src_dest()

    def bulk_import_irradiations(self, creator, dry=True):
        src = self.processor.db
        # with src.session_ctx() as sess:
        #     irradnames = [i.name for i in src.get_irradiations()]

        # for i in xrange(251, 277):
        # for i in xrange(258, 259):
        # for i in (258, 259, 260, 261,):
        # for i in (262, 263, 264, 265):
        # for i in (266, 267, 268, 269):
        for i in (270, 271, 272, 273):
            irradname = 'NM-{}'.format(i)
            runs = self.bulk_import_irradiation(irradname, creator, dry=dry)
            # if runs:
            #     with open('/Users/ross/Sandbox/bulkimport/irradiation_runs.txt', 'a') as wfile:
            #         for o in runs:
            #             wfile.write('{}\n'.format(o))

    def get_irradiation_timestamps(self, irradname, tol_hrs=6):
        src = self.processor.db
        with src.session_ctx() as sess:
            sql = """SELECT ant.analysis_timestamp from meas_analysistable as ant
join gen_labtable as lt on lt.id = ant.lab_id
join gen_sampletable as st on lt.sample_id = st.id
join irrad_PositionTable as irp on lt.irradiation_id = irp.id
join irrad_leveltable as il on irp.level_id = il.id
join irrad_irradiationtable as ir on il.irradiation_id = ir.id

where ir.name = "{}" and st.name ="FC-2"
order by ant.analysis_timestamp ASC

""".format(irradname)
            result = sess.execute(sql)
            ts = array([make_timef(ri[0]) for ri in result.fetchall()])

            idxs = bin_timestamps(ts, tol_hrs=tol_hrs)
            return ts, idxs

    def import_date_range(self, low, high, spectrometer, experiment_id, creator):
        src = self.processor.db
        with src.session_ctx():
            runs = src.get_analyses_date_range(low, high, mass_spectrometers=spectrometer)

            ais = [ai.record_id for ai in runs]
        self.do_export(ais, experiment_id, creator)

    def bulk_import_irradiation(self, irradname, creator, dry=True):

        src = self.processor.db
        tol_hrs = 6
        self.debug('bulk import irradiation {}'.format(irradname))
        oruns = []
        ts, idxs = self.get_irradiation_timestamps(irradname, tol_hrs=tol_hrs)
        prev = None
        experiment_id = 'Irradiation-{}'.format(irradname)

        def filterfunc(x):
            a = x.labnumber.irradiation_position is None
            b = False
            if not a:
                b = x.labnumber.irradiation_position.level.irradiation.name == irradname

            d = False
            if x.extraction:
                ed = x.extraction.extraction_device
                if not ed:
                    d = True
                else:
                    d = ed.name == 'Fusions CO2'

            return (a or b) and d

        for ms in ('jan', 'obama'):
            for i, ais in enumerate(array_split(ts, idxs + 1)):
                if not ais.shape[0]:
                    self.debug('skipping {}'.format(i))
                    continue

                low = get_datetime(ais[0]) - timedelta(hours=tol_hrs / 2.)
                high = get_datetime(ais[-1]) + timedelta(hours=tol_hrs / 2.)
                with src.session_ctx():
                    ans = src.get_analyses_date_range(low, high,
                                                      mass_spectrometers=(ms,),
                                                      samples=('FC-2',
                                                               'blank_unknown', 'blank_air', 'blank_cocktail', 'air',
                                                               'cocktail'))

                    # runs = filter(lambda x: x.labnumber.irradiation_position is None or
                    #                         x.labnumber.irradiation_position.level.irradiation.name == irradname, ans)

                    runs = filter(filterfunc, ans)
                    if dry:
                        for ai in runs:
                            oruns.append(ai.record_id)
                            # print ms, ai.record_id
                    else:
                        self.debug('================= Do Export i: {} low: {} high: {}'.format(i, low, high))
                        self.debug('N runs: {}'.format(len(runs)))
                        self.do_export([ai.record_id for ai in runs], experiment_id, creator)

        return oruns

    def do_export(self, runs, experiment_id, creator, create_repo=False):

        # self._init_src_dest()
        src = self.processor.db
        dest = self.dvc.db

        with src.session_ctx():
            key = lambda x: x.split('-')[0]
            runs = sorted(runs, key=key)
            with dest.session_ctx():
                repo = self._add_experiment(dest, experiment_id, creator, create_repo)

            self.persister.experiment_repo = repo
            self.dvc.experiment_repo = repo

            total = len(runs)
            j = 0

            for ln, ans in groupby(runs, key=key):
                ans = list(ans)
                n = len(ans)
                for i, a in enumerate(ans):
                    with dest.session_ctx() as sess:
                        st = time.time()
                        try:
                            if self._transfer_analysis(a, experiment_id):
                                j += 1
                                self.debug('{}/{} transfer time {:0.3f}'.format(j, total, time.time() - st))
                        except BaseException, e:
                            import traceback
                            traceback.print_exc()
                            self.warning('failed transfering {}. {}'.format(a, e))

    def runlist_load(self, path):
        with open(path, 'r') as rfile:
            runs = [li.strip() for li in rfile]
            # runs = [line.strip() for line in rfile if line.strip()]
            return filter(None, runs)

    def runlist_loads(self, txt):
        runs = [li.strip() for li in txt.striplines()]
        return filter(None, runs)

    # private
    def _init_src_dest(self):
        conn = dict(host=os.environ.get('ARGONSERVER_HOST'),
                    username=os.environ.get('ARGONSERVER_DB_USER'),
                    password=os.environ.get('ARGONSERVER_DB_PWD'),
                    kind='mysql')

        self.dvc = DVC(bind=False,
                       organization='NMGRLData',
                       meta_repo_name='meta')

        use_local = True
        name = 'pychronmeta_test'

        if use_local:
            dest_conn = dict(host='localhost',
                             username=os.environ.get('LOCALHOST_DB_USER'),
                             password=os.environ.get('LOCALHOST_DB_PWD'),
                             kind='mysql',
                             name=name)
        else:
            dest_conn = conn.copy()
            dest_conn['name'] = name

        self.dvc.db.trait_set(**dest_conn)
        if not self.dvc.initialize():
            self.warning_dialog('Failed to initialize DVC')
            return

        self.dvc.meta_repo.smart_pull(quiet=self.quiet)
        self.persister = DVCPersister(dvc=self.dvc, stage_files=False)

        proc = IsotopeDatabaseManager(bind=False, connect=False)
        proc.db.trait_set(name='pychrondata', **conn)
        src = proc.db
        src.connect()
        self.processor = proc

    def _add_experiment(self, dest, experiment_id, creator, create_repo):
        experiment_id = format_experiment_identifier(experiment_id)

        # sys.exit()
        proot = os.path.join(paths.experiment_dataset_dir, experiment_id)
        if not os.path.isdir(proot):
            # create new local repo
            os.mkdir(proot)

            repo = GitRepoManager()
            repo.open_repo(proot)

            repo.add_ignore('.DS_Store')
            self.repo_man = repo
            if create_repo:
                # add repo to central location
                create_github_repo(experiment_id)

                url = 'https://github.com/{}/{}.git'.format(ORG, experiment_id)
                self.debug('Create repo at github. url={}'.format(url))
                repo.create_remote(url)
        else:
            repo = GitRepoManager()
            repo.open_repo(proot)

        dbexp = dest.get_experiment(experiment_id)
        if not dbexp:
            dest.add_experiment(experiment_id, creator)

        return repo

    def _transfer_meta(self, dest, dban):
        self.debug('transfer meta')

        dblab = dban.labnumber
        dbsam = dblab.sample
        project = dbsam.project.name
        project = project.replace('/', '_').replace('\\', '_')

        sam = dest.get_sample(dbsam.name, project)
        if not sam:
            mat = dbsam.material.name
            if not dest.get_material(mat):
                self.debug('add material {}'.format(mat))
                dest.add_material(mat)
                dest.flush()

            if not dest.get_project(project):
                self.debug('add project {}'.format(project))
                dest.add_project(project)
                dest.flush()

            self.debug('add sample {}'.format(dbsam.name))
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

            holder = dblevel.holder.name if dblevel.holder else ''
            geom = dblevel.holder.geometry if dblevel.holder else ''
            prod = dblevel.production
            prodname = dblevel.production.name if dblevel.production else ''
            pos = dbirradpos.position
            doses = dbchron.get_doses()

        meta_repo = self.dvc.meta_repo
        # save db irradiation
        if not dest.get_irradiation(irradname):
            self.debug('Add irradiation {}'.format(irradname))
            dest.add_irradiation(irradname)
            dest.flush()

            meta_repo.add_irradiation(irradname, add=False)
            meta_repo.add_chronology(irradname, doses, add=False)
            # meta_repo.commit('added irradiation {}'.format(irradname))

        # save production name to db
        if not dest.get_production(prodname):
            self.debug('Add production {}'.format(irradname))
            dest.add_production(prodname)
            dest.flush()

            # meta_repo.add_production(irradname, prodname, prod, add=False)
            # meta_repo.commit('added production {}'.format(prodname))

        # save db level
        if not dest.get_irradiation_level(irradname, levelname):
            self.debug('Add level irrad:{} level:{}'.format(irradname, levelname))
            dest.add_irradiation_level(levelname, irradname, holder, prodname)
            dest.flush()

            meta_repo.add_irradiation_holder(holder, geom, add=False)
            meta_repo.add_level(irradname, levelname, add=False)
            # meta_repo.commit('added empty level {}{}'.format(irradname, levelname))

        if pos is None:
            pos = self._get_irradpos(dest, irradname, levelname, identifier)

        # save db irradiation position
        if not dest.get_irradiation_position(irradname, levelname, pos):
            self.debug('Add position irrad:{} level:{} pos:{}'.format(irradname, levelname, pos))
            p = meta_repo.get_level_path(irradname, levelname)
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

            yd.append({'j': j, 'j_err': e, 'position': pos, 'decay_constants': {}})
            dvc_dump(yd, p)

    def _transfer_analysis(self, rec, exp, overwrite=True):
        dest = self.dvc.db
        proc = self.processor
        src = proc.db

        # args = rec.split('-')
        # idn = '-'.join(args[:-1])
        # t = args[-1]
        # try:
        #     aliquot = int(t)
        #     step = None
        # except ValueError:
        #     aliquot = int(t[:-1])
        #     step = t[-1]
        m = IDENTIFIER_REGEX.match(rec)
        if not m:
            m = SPECIAL_IDENTIFIER_REGEX.match(rec)

        if not m:
            self.warning('invalid runid {}'.format(rec))
            return
        else:
            idn = m.group('identifier')
            aliquot = m.group('aliquot')
            try:
                step = m.group('step') or None
            except IndexError:
                step = None

        if idn == '4359':
            idn = 'c-01-j'
        elif idn == '4358':
            idn = 'c-01-o'

        # check if analysis already exists. skip if it does
        if dest.get_analysis_runid(idn, aliquot, step):
            self.warning('{} already exists'.format(make_runid(idn, aliquot, step)))
            return

        dban = src.get_analysis_runid(idn, aliquot, step)
        iv = IsotopeRecordView()
        iv.uuid = dban.uuid

        self.debug('make analysis idn:{}, aliquot:{} step:{}'.format(idn, aliquot, step))
        try:
            an = proc.make_analysis(iv, unpack=True, use_cache=False)
        except:
            self.warning('Failed to make {}'.format(make_runid(idn, aliquot, step)))
            return

        self._transfer_meta(dest, dban)
        # return

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
        project = format_experiment_identifier(dbsam.project.name)
        extraction = dban.extraction
        ms = dban.measurement.mass_spectrometer.name
        if not dest.get_mass_spectrometer(ms):
            self.debug('adding mass spectrometer {}'.format(ms))
            dest.add_mass_spectrometer(ms)
            dest.flush()

        ed = extraction.extraction_device.name if extraction.extraction_device else ''
        if ed and not dest.get_extraction_device(ed):
            dest.add_extraction_device(ed)
            dest.flush()

        if step is None:
            inc = -1
        else:
            inc = ALPHAS.index(step)

        username = ''
        if dban.user:
            username = dban.user.name
            if not dest.get_user(username):
                self.debug('adding user. username:{}'.format(username))
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
                              experiment_identifier=exp,
                              mass_spectrometer=ms,
                              uuid=dban.uuid,
                              _step=inc,
                              comment=dban.comment or '',
                              aliquot=int(aliquot),
                              extract_device=ed,
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
                             tag=an.tag.name,
                             arar_age=an,
                             timestamp=dban.analysis_timestamp,
                             use_experiment_association=True,
                             positions=[p.position for p in extraction.positions])

        self.debug('transfer analysis with persister')
        self.persister.per_spec_save(ps, commit=False, msg_prefix='Database Transfer')
        return True

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


def experiment_id_modifier(root, expid):
    for r, ds, fs in os.walk(root, topdown=True):
        fs = [f for f in fs if not f[0] == '.']
        ds[:] = [d for d in ds if not d[0] == '.']

        # print 'fff',r, os.path.basename(r)
        if os.path.basename(r) in ('intercepts', 'blanks', '.git',
                                   'baselines', 'icfactors', 'extraction', 'tags', '.data', 'monitor', 'peakcenter'):
            continue
        # dcnt+=1
        for fi in fs:
            # if not fi.endswith('.py') or fi == '__init__.py':
            #     continue
            # cnt+=1
            p = os.path.join(r, fi)
            # if os.path.basename(os.path.dirname(p)) =
            print p
            write = False
            with open(p, 'r') as rfile:
                jd = json.load(rfile)
                if 'experiment_identifier' in jd:
                    jd['experiment_identifier'] = expid
                    write = True

            if write:
                dvc_dump(jd, p)


def load_path():
    # path = '/Users/ross/Sandbox/dvc_imports/NM-276.txt'
    # expid = 'Irradiation-NM-276'
    # creator = 'mcintosh'

    path = '/Users/ross/Sandbox/dvc_imports/chesner_unknowns.txt'
    expid = 'toba'
    creator = 'root'

    runs = e.runlist_load(path)
    return runs, expid, creator


def load_import_request():
    import pymysql.cursors
    # Connect to the database
    connection = pymysql.connect(host='localhost',
                                 user=os.environ.get('DB_USER'),
                                 passwd=os.environ.get('DB_PWD'),
                                 db='labspy',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        # connection is not autocommit by default. So you must commit to save
        # your changes.
        # connection.commit()

        with connection.cursor() as cursor:
            # Read a single record
            # sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
            # cursor.execute(sql, ('webmaster@python.org',))
            sql = '''SELECT * FROM importer_importrequest'''
            cursor.execute(sql)
            result = cursor.fetchone()

            runs = result['runlist_blob']
            expid = result['experiment_identifier']
            creator = result['requestor_name']

            return runs, expid, creator
    finally:
        connection.close()


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build('_dev')
    logging_setup('de', root=os.path.join(os.path.expanduser('~'), 'Desktop', 'logs'))

    e = IsoDBTransfer()
    e.quiet = True
    e.init()

    # runs, expid, creator = load_path()
    # runs, expid, creator = load_import_request()
    # e.bulk_import_irradiations('root', dry=False)
    # e.bulk_import_irradiation('NM-274', 'root', dry=False)
    e.import_date_range('2015-12-07 12:00:43', '2015-12-09 13:45:51', 'jan',
                        'MATT_AGU', 'root')
    # e.do_export(runs, expid, creator, create_repo=False)

    # experiment_id_modifier('/Users/ross/Pychron_dev/data/.dvc/experiments/Irradiation-NM-274', 'Irradiation-NM-276')

    # create_github_repo('Irradiation-NM-272')
    # exp = 'J-Curve'
    # url = 'https://github.com/{}/{}.git'.format(org.name, exp)
    # # e.transfer_holder('40_no_spokes')
    # # e.transfer_holder('40_hole')
    # # e.transfer_holder('24_hole')
    #
    # path = '/Users/ross/Sandbox/dvc_imports/NM-275.txt'
    # expid = 'Irradiation-NM-275'
    # creator = 'mcintosh'
    # e.do_export(path, expid, creator, create_repo=False)

    # e.do_export_monitors(path, expid, creator, create_repo=False)
    # e.check_experiment(path, expid)
    # e.do_export(path, expid, creator, create_repo=False)
    # e.export_production('Triga PR 275', db=False)
    # ============= EOF =============================================
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
    # def transfer_holder(self, name):
    #     self.root = os.path.join(os.path.expanduser('~'), 'Pychron_dev', 'data', '.dvc')
    #
    #     conn = dict(host=os.environ.get('HOST'), username='root', password='', kind='mysql')
    #     # conn = dict(host=os.environ.get('HOST'), username='root', password='', kind='mysql')
    #     # dest = DVCDatabase('/Users/ross/Sandbox/dvc/meta/testdb.sqlite')
    #     # dest = DVCDatabase(name='pychronmeta', **conn)
    #     # self.dvc = DVC(bind=False)
    #     # self.dvc.db.trait_set(name='pychronmeta', username='root',
    #     #                       password='Argon', kind='mysql', host='localhost')
    #
    #     self.meta_repo = MetaRepo()
    #     self.meta_repo.open_repo(os.path.join(self.root, 'meta'))
    #     proc = IsotopeDatabaseManager(bind=False, connect=False)
    #     proc.db.trait_set(name='pychrondata', **conn)
    #     src = proc.db
    #     # src = IsotopeAdapter(name='pychrondata', **conn)
    #     # src.trait_set()
    #     src.connect()
    #     with src.session_ctx():
    #         holder = src.get_irradiation_holder(name)
    #         self.meta_repo.add_irradiation_holder(name, holder.geometry)

    # def export_production(self, prodname, db=False):
    #     if db:
    #         pass
    #
    #     # self.root = os.path.join(os.path.expanduser('~'), 'Pychron_dev', 'data', '.dvc')
    #     self.meta_repo = MetaRepo(os.path.join(self.root, 'meta'))
    #
    #     conn = dict(host=os.environ.get('HOST'), username='root', password='', kind='mysql')
    #     dest = DVCDatabase('/Users/ross/Sandbox/dvc/meta/testdb.sqlite')
    #     # dest = DVCDatabase(name='pychronmeta', **conn)
    #     dest.connect()
    #     src = IsotopeAdapter(name='pychrondata', **conn)
    #     # src.trait_set()
    #     src.connect()
    #     with src.session_ctx():
    #         if not dest.get_production(prodname):
    #             dest.add_production(prodname)
    #             dest.flush()
    #
    #             dbprod = src.get_irradiation_production(prodname)
    #             self.meta_repo.add_production(prodname, dbprod)
    #             self.meta_repo.commit('added production {}'.format(prodname))
    # def do_export_monitors(self, path, experiment_id, creator, create_repo=False):
    #     self.root = os.path.join(os.path.expanduser('~'), 'Pychron_dev', 'data', '.dvc')
    #     self.meta_repo = MetaRepo()
    #     self.meta_repo.open_repo(os.path.join(self.root, 'meta'))
    #
    #     conn = dict(host=os.environ.get('HOST'), username='root', password='', kind='mysql')
    #     # conn = dict(host=os.environ.get('HOST'), username='root', password='', kind='mysql')
    #     # dest = DVCDatabase('/Users/ross/Sandbox/dvc/meta/testdb.sqlite')
    #     # dest = DVCDatabase(name='pychronmeta', **conn)
    #     self.dvc = DVC(bind=False,
    #                    meta_repo_name='meta')
    #     self.dvc.db.trait_set(name='pychronmeta', username='root',
    #                           password='Argon', kind='mysql', host='localhost')
    #     if not self.dvc.initialize():
    #         self.warning_dialog('Failed to initialize DVC')
    #         return
    #
    #     self.persister = DVCPersister(dvc=self.dvc)
    #
    #     dest = self.dvc.db
    #
    #     proc = IsotopeDatabaseManager(bind=False, connect=False)
    #     proc.db.trait_set(name='pychrondata', **conn)
    #     src = proc.db
    #     # src = IsotopeAdapter(name='pychrondata', **conn)
    #     # src.trait_set()
    #     src.connect()
    #     with src.session_ctx():
    #         with open(path, 'r') as rfile:
    #             runs = [line.strip() for line in rfile if line.strip()]
    #
    #         key = lambda x: x.split('-')[0]
    #         runs = sorted(runs, key=key)
    #
    #         for r in runs:
    #             args = r.split('-')
    #             idn = '-'.join(args[:-1])
    #             t = args[-1]
    #             try:
    #                 aliquot = int(t)
    #                 step = None
    #             except ValueError:
    #                 aliquot = int(t[:-1])
    #                 step = t[-1]
    #             try:
    #                 int(idn)
    #             except:
    #                 continue
    #             dban = src.get_analysis_runid(idn, aliquot, step)
    #             if dban:
    #                 print idn, dban.labnumber.irradiation_position.level.irradiation.name
    #                 # runs = proc.make_analyses(runs)
    #                 # iv = IsotopeRecordView()
    #                 # iv.uuid = dban.uuid
    #                 # an = proc.make_analysis(iv, unpack=True, use_cache=False)
    #
    #                 # key = lambda x: x.irradiation
    #                 # runs = sorted(runs, key=key)
    #                 # for irrad, ais in groupby(runs, key=key):
    #                 #     print irrad, len(list(ais))
