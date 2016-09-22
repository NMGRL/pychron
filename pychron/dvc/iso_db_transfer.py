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
import json
import os
import time
from datetime import timedelta
from itertools import groupby

from numpy import array_split
from traits.api import Instance

from pychron.canvas.utils import make_geom
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.dvc import dvc_dump
from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_persister import DVCPersister, format_repository_identifier
from pychron.dvc.pychrondata_transfer_helpers import get_irradiation_timestamps, get_project_timestamps, \
    set_spectrometer_files
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.utilities.identifier import make_runid, IDENTIFIER_REGEX, SPECIAL_IDENTIFIER_REGEX
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.github import Organization
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import ALPHAS, QTEGRA_SOURCE_KEYS

ORG = 'NMGRLData'


def create_github_repo(name):
    org = Organization(ORG)
    if not org.has_repo(name):
        usr = os.environ.get('GITHUB_USER')
        pwd = os.environ.get('GITHUB_PASSWORD')
        org.create_repo(name, usr, pwd)


class IsoDBTransfer(Loggable):
    """
    transfer analyses from an isotope_db database to a dvc database
    """
    dvc = Instance(DVC)
    processor = Instance(IsotopeDatabaseManager)
    persister = Instance(DVCPersister)

    quiet = False

    def init(self):
        conn = dict(host=os.environ.get('ARGONSERVER_HOST'),
                    username=os.environ.get('ARGONSERVER_DB_USER'),
                    password=os.environ.get('ARGONSERVER_DB_PWD'),
                    kind='mysql')

        self.dvc = DVC(bind=False,
                       organization='NMGRLData',
                       meta_repo_name='MetaData')
        paths.meta_root = os.path.join(paths.dvc_dir, self.dvc.meta_repo_name)

        use_local = True
        if use_local:
            dest_conn = dict(host='localhost',
                             username=os.environ.get('LOCALHOST_DB_USER'),
                             password=os.environ.get('LOCALHOST_DB_PWD'),
                             kind='mysql',
                             # echo=True,
                             name='pychrondvc_dev')
        else:
            dest_conn = conn.copy()
            dest_conn['name'] = 'pychrondvc'

        self.dvc.db.trait_set(**dest_conn)
        if not self.dvc.initialize():
            self.warning_dialog('Failed to initialize DVC')
            return

        self.dvc.meta_repo.smart_pull(quiet=self.quiet)
        self.persister = DVCPersister(dvc=self.dvc, stage_files=False)

        proc = IsotopeDatabaseManager(bind=False, connect=False)

        use_local_src = True
        if use_local_src:
            conn = dict(host='localhost',
                        username=os.environ.get('LOCALHOST_DB_USER'),
                        password=os.environ.get('LOCALHOST_DB_PWD'),
                        kind='mysql',
                        # echo=True,
                        name='pychrondata')
        else:
            conn['name'] = 'pychrondata'

        proc.db.trait_set(**conn)
        src = proc.db
        src.connect()
        self.processor = proc

    def copy_productions(self):
        src = self.processor.db
        dvc = self.dvc
        dest = dvc.db
        with src.session_ctx():
            pr = src.get_irradiation_productions()
            for p in pr:
                # copy to database
                pname = p.name.replace(' ', '_')
                if not dest.get_production(pname):
                    dest.add_production(pname)

                # copy to meta
                dvc.copy_production(p)

    def set_spectrometer_files(self, repository):
        set_spectrometer_files(self.processor.db,
                               self.dvc.db,
                               repository,
                               os.path.join(paths.repository_dataset_dir, repository))

    def bulk_import_irradiations(self, irradiations, creator, dry=True):

        # for i in xrange(251, 277):
        # for i in xrange(258, 259):
        # for i in (258, 259, 260, 261,):
        # for i in (262, 263, 264, 265):
        # for i in (266, 267, 268, 269):
        # for i in (270, 271, 272, 273):
        for i in irradiations:
            irradname = 'NM-{}'.format(i)
            runs = self.bulk_import_irradiation(irradname, creator, dry=dry)
            # if runs:
            #     with open('/Users/ross/Sandbox/bulkimport/irradiation_runs.txt', 'a') as wfile:
            #         for o in runs:
            #             wfile.write('{}\n'.format(o))

    def bulk_import_irradiation(self, irradname, creator, dry=True):

        src = self.processor.db
        tol_hrs = 6
        self.debug('bulk import irradiation {}'.format(irradname))
        oruns = []
        ts, idxs = self._get_irradiation_timestamps(irradname, tol_hrs=tol_hrs)
        print ts
        repository_identifier = 'Irradiation-{}'.format(irradname)

        # add project
        with self.dvc.db.session_ctx():
            self.dvc.db.add_project(repository_identifier, creator)

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

        # for ms in ('jan', 'obama'):

        # monitors not run on obama
        for ms in ('jan',):
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
                            print ms, ai.record_id
                    else:
                        self.debug('================= Do Export i: {} low: {} high: {}'.format(i, low, high))
                        self.debug('N runs: {}'.format(len(runs)))
                        self.do_export([ai.record_id for ai in runs],
                                       repository_identifier, creator,
                                       monitor_mapping=('FC-2', 'Sanidine', repository_identifier))

        return oruns

    def bulk_import_project(self, project, principal_investigator, dry=True):
        src = self.processor.db
        tol_hrs = 6
        self.debug('bulk import project={}, pi={}'.format(project, principal_investigator))
        oruns = []

        repository_identifier = project

        # def filterfunc(x):
        #     a = x.labnumber.irradiation_position is None
        #     b = False
        #     if not a:
        #         b = x.labnumber.irradiation_position.level.irradiation.name == irradname
        #
        #     d = False
        #     if x.extraction:
        #         ed = x.extraction.extraction_device
        #         if not ed:
        #             d = True
        #         else:
        #             d = ed.name == 'Fusions CO2'
        #
        #     return (a or b) and d
        #
        for ms in ('jan', 'obama'):
            ts, idxs = self._get_project_timestamps(project, ms, tol_hrs=tol_hrs)
            for i, ais in enumerate(array_split(ts, idxs + 1)):
                if not ais.shape[0]:
                    self.debug('skipping {}'.format(i))
                    continue

                low = get_datetime(ais[0]) - timedelta(hours=tol_hrs / 2.)
                high = get_datetime(ais[-1]) + timedelta(hours=tol_hrs / 2.)

                print '========{}, {}, {}'.format(ms, low, high)
                with src.session_ctx():
                    runs = src.get_analyses_date_range(low, high,
                                                       projects=('REFERENCES', project),
                                                       mass_spectrometers=(ms,))

                    if dry:
                        for ai in runs:
                            oruns.append(ai.record_id)
                            print ai.measurement.mass_spectrometer.name, ai.record_id, ai.labnumber.sample.name, \
                                ai.analysis_timestamp
                    else:
                        self.debug('================= Do Export i: {} low: {} high: {}'.format(i, low, high))
                        self.debug('N runs: {}'.format(len(runs)))
                        self.do_export([ai.record_id for ai in runs], repository_identifier, principal_investigator)

        return oruns

    def find_project_overlaps(self, projects):
        tol_hrs = 6
        src = self.processor.db

        pdict = {}
        for p in projects:
            for ms in ('jan', 'obama'):
                ts, idxs = self._get_project_timestamps(p, ms, tol_hrs=tol_hrs)
                for i, ais in enumerate(array_split(ts, idxs + 1)):
                    if not ais.shape[0]:
                        self.debug('skipping {}'.format(i))
                        continue

                    low = get_datetime(ais[0]) - timedelta(hours=tol_hrs / 2.)
                    high = get_datetime(ais[-1]) + timedelta(hours=tol_hrs / 2.)

                    print '========{}, {}, {}'.format(ms, low, high)
                    with src.session_ctx():
                        runs = src.get_analyses_date_range(low, high,
                                                           projects=('REFERENCES',),
                                                           mass_spectrometers=(ms,))

                        pdict[p] = [ai.record_id for ai in runs]

        for p in projects:
            for o in projects:
                if p == o:
                    continue
                pruns = pdict[p]
                oruns = pdict[o]
                for ai in pruns:
                    if ai in oruns:
                        print p, o, ai

    def import_date_range(self, low, high, spectrometer, repository_identifier, creator):
        src = self.processor.db
        with src.session_ctx():
            runs = src.get_analyses_date_range(low, high, mass_spectrometers=spectrometer)

            ais = [ai.record_id for ai in runs]
        self.do_export(ais, repository_identifier, creator)

    def do_export(self, runs, repository_identifier, creator, create_repo=False, monitor_mapping=None):

        # self._init_src_dest()
        src = self.processor.db
        dest = self.dvc.db

        with src.session_ctx():
            key = lambda x: x.split('-')[0]
            runs = sorted(runs, key=key)
            with dest.session_ctx():
                repo = self._add_repository(dest, repository_identifier, creator, create_repo)

            self.persister.active_repository = repo
            self.dvc.current_repository = repo

            total = len(runs)
            j = 0

            for ln, ans in groupby(runs, key=key):
                ans = list(ans)
                n = len(ans)
                for i, a in enumerate(ans):
                    with dest.session_ctx() as sess:
                        st = time.time()
                        try:
                            if self._transfer_analysis(a, repository_identifier, monitor_mapping=monitor_mapping):
                                j += 1
                                self.debug('{}/{} transfer time {:0.3f}'.format(j, total, time.time() - st))
                        except BaseException, e:
                            import traceback
                            traceback.print_exc()
                            self.warning('failed transfering {}. {}'.format(a, e))

    # private
    def _get_project_timestamps(self, project, mass_spectrometer, tol_hrs=6):
        src = self.processor.db
        return get_project_timestamps(src, project, mass_spectrometer, tol_hrs)

    def _get_irradiation_timestamps(self, irradname, tol_hrs=6):
        src = self.processor.db
        return get_irradiation_timestamps(src, irradname, tol_hrs)

    def _add_repository(self, dest, repository_identifier, creator, create_repo):
        repository_identifier = format_repository_identifier(repository_identifier)

        # sys.exit()
        proot = os.path.join(paths.repository_dataset_dir, repository_identifier)
        if not os.path.isdir(proot):
            # create new local repo
            os.mkdir(proot)

            repo = GitRepoManager()
            repo.open_repo(proot)

            repo.add_ignore('.DS_Store')
            self.repo_man = repo
            if create_repo:
                # add repo to central location
                create_github_repo(repository_identifier)

                url = 'https://github.com/{}/{}.git'.format(ORG, repository_identifier)
                self.debug('Create repo at github. url={}'.format(url))
                repo.create_remote(url)
        else:
            repo = GitRepoManager()
            repo.open_repo(proot)

        dbexp = dest.get_repository(repository_identifier)
        if not dbexp:
            dest.add_repository(repository_identifier, creator)

        return repo

    def _transfer_meta(self, dest, dban, monitor_mapping):
        self.debug('transfer meta {}'.format(monitor_mapping))

        dblab = dban.labnumber
        if monitor_mapping is None:
            dbsam = dblab.sample
            project = dbsam.project.name
            project_name = project.replace('/', '_').replace('\\', '_')
            sample_name = dbsam.name
            material_name = dbsam.material.name
        else:
            sample_name, material, project = monitor_mapping

        sam = dest.get_sample(sample_name, project_name, material_name)
        if not sam:
            if not dest.get_material(material_name):
                self.debug('add material {}'.format(material_name))
                dest.add_material(material_name)
                dest.flush()

            if not dest.get_project(project_name):
                self.debug('add project {}'.format(project_name))
                dest.add_project(project_name)
                dest.flush()

            self.debug('add sample {}'.format(sample_name))
            sam = dest.add_sample(sample_name, project_name, material_name)
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
            prodname = dblevel.production.name if dblevel.production else ''
            prodname = prodname.replace(' ', '_')
            pos = dbirradpos.position
            doses = dbchron.get_doses()

        meta_repo = self.dvc.meta_repo
        # save db irradiation
        if not dest.get_irradiation(irradname):
            self.debug('Add irradiation {}'.format(irradname))

            self.dvc.add_irradiation(irradname, doses)
            dest.flush()
            # meta_repo.add_irradiation(irradname)
            # meta_repo.add_chronology(irradname, doses, add=False)
            # meta_repo.commit('added irradiation {}'.format(irradname))

        # save production name to db
        if not dest.get_production(prodname):
            self.debug('Add production {}'.format(prodname))
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
            meta_repo.update_level_production(irradname, levelname, prodname)

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

        dest.commit()

    def _transfer_analysis(self, rec, exp, overwrite=True, monitor_mapping=None):
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
            an = proc.make_analysis(iv, unpack=True, use_cache=False, use_progress=False)
        except:
            self.warning('Failed to make {}'.format(make_runid(idn, aliquot, step)))
            return

        self._transfer_meta(dest, dban, monitor_mapping)
        # return

        dblab = dban.labnumber

        if dblab.irradiation_position:
            irrad = dblab.irradiation_position.level.irradiation.name
            level = dblab.irradiation_position.level.name
            irradpos = dblab.irradiation_position.position
        else:
            irrad = 'NoIrradiation'
            level = 'A'
            irradpos = self._get_irradpos(dest, irrad, level, dblab.identifier)
            # irrad, level, irradpos = '', '', 0

        extraction = dban.extraction
        ms = dban.measurement.mass_spectrometer.name
        if not dest.get_mass_spectrometer(ms):
            self.debug('adding mass spectrometer {}'.format(ms))
            dest.add_mass_spectrometer(ms)
            dest.commit()

        ed = extraction.extraction_device.name if extraction.extraction_device else None
        if not ed:
            ed = 'No Extract Device'

        if not dest.get_extraction_device(ed):
            self.debug('adding extract device {}'.format(ed))
            dest.add_extraction_device(ed)
            dest.commit()

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
                dest.commit()

        if monitor_mapping:
            sample_name, material_name, project_name = monitor_mapping
        else:
            dbsam = dblab.sample
            sample_name = dbsam.name
            material_name = dbsam.material.name
            project_name = format_repository_identifier(dbsam.project.name)

        rs = AutomatedRunSpec(labnumber=idn,
                              username=username,
                              material=material_name,
                              project=project_name,
                              sample=sample_name,
                              irradiation=irrad,
                              irradiation_level=level,
                              irradiation_position=irradpos,
                              repository_identifier=exp,
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

        meas = dban.measurement
        # get spectrometer parameters
        # gains
        gains = {}
        gain_history = dban.gain_history
        if gain_history:
            gains = {d.detector.name: d.value for d in gain_history.gains}

        # deflections
        deflections = {d.detector.name: d.deflection for d in meas.deflections}

        # source
        src = {k: getattr(meas.spectrometer_parameters, k) for k in QTEGRA_SOURCE_KEYS}

        ps = PersistenceSpec(run_spec=rs,
                             tag=an.tag.name,
                             arar_age=an,
                             timestamp=dban.analysis_timestamp,
                             defl_dict=deflections,
                             gains=gains,
                             spec_dict=src,
                             use_repository_association=True,
                             positions=[p.position for p in extraction.positions])

        self.debug('transfer analysis with persister')
        self.persister.per_spec_save(ps, commit=False, commit_tag='Database Transfer')
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


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build('_dev')
    logging_setup('de', root=os.path.join(os.path.expanduser('~'), 'Desktop', 'logs'))

    e = IsoDBTransfer()
    e.quiet = True
    e.init()

    # runs, expid, creator = load_path()
    # runs, expid, creator = load_import_request()
    # irrads = ('NM-264', 'NM-266', 'NM-267', 'NM-269', 'NM-274', 'NM-278')
    # for i in irrads:
    #     project = 'Irradiation-{}'.format(i)
    #     create_repo_for_existing_local(project, paths.repository_dataset_dir)
    #     commit_initial_import(project, paths.repository_dataset_dir)
    e.bulk_import_irradiation('NM-281', 'NMGRL', dry=False)

    # e.bulk_import_project('Cascades', 'Templeton', dry=False)
    # fix_a_steps(e.dvc.db, 'Toba', paths.repository_dataset_dir)
    # fix_a_steps(e.dvc.db, 'Lucero', paths.repository_dataset_dir)
    # create_repo_for_existing_local('Cascades', paths.repository_dataset_dir)
    # commit_initial_import('Cascades', paths.repository_dataset_dir)

    # import_j(e.processor.db, e.dvc.db, e.dvc.meta_repo, 'Toba')
    # ps = ('Valles',
    #       'RatonClayton',
    #       'ZuniBandera',
    #       'ValleyOfFire',
    #       'Potrillo',
    #       'RedHillQuemado',
    #       'ZeroAge',
    #       'Animas',
    #       'BrazosCones',
    #       'Jornada',
    #       'Lucero',
    #       'CatHills',
    #       'SanFrancisco',
    #       'AlbuquerqueVolcanoes',
    #       'Irradiation-NM-264',
    #       'Irradiation-NM-266',
    #       'Irradiation-NM-267',
    #       'Irradiation-NM-269',
    #       'Irradiation-NM-270',
    #       'Irradiation-NM-271',
    #       'Irradiation-NM-272',
    #       'Irradiation-NM-273',
    #       'Irradiation-NM-274',
    #       'Irradiation-NM-278',
    #       'Irradiation-NM-281')
    # for p in ps:
    #     fix_import_commit(p, paths.repository_dataset_dir)

        #
        # e.find_project_overlaps(ps)

    # for project in ps:
    # print 'project={}'.format(project)
    # fix_a_steps(e.dvc.db, project, paths.repository_dataset_dir)
    # commit_initial_import(project, paths.repository_dataset_dir)
    #     create_repo_for_existing_local(project, paths.repository_dataset_dir)
    # e.bulk_import_project(project, 'Zimmerer', dry=False)
    # e.copy_productions()
    # e.set_spectrometer_files('Irradiation-NM-273')

    # e.bulk_import_irradiation('NM-274', 'root', dry=False)
    # e.import_date_range('2015-12-07 12:00:43', '2015-12-09 13:45:51', 'jan',
    #                     'MATT_AGU', 'root')
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
