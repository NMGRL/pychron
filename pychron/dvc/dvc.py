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

from __future__ import absolute_import
from __future__ import print_function
import os
import shutil
from operator import attrgetter

import time
from datetime import datetime
from itertools import groupby
from math import isnan
from git import Repo
from uncertainties import nominal_value, std_dev, ufloat

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance, Str, Set, List, provides

from pychron.core.helpers.filetools import remove_extension, list_subdirectories
from pychron.core.i_datastore import IDatastore
from pychron.core.progress import progress_loader, progress_iterator
from pychron.database.interpreted_age import InterpretedAge
from pychron.database.tasks.connection_preferences import ConnectionFavoriteItem
from pychron.dvc import dvc_dump, dvc_load, analysis_path, repository_path, AnalysisNotAnvailableError
from pychron.dvc.defaults import TRIGA, HOLDER_24_SPOKES, LASER221, LASER65
from pychron.dvc.dvc_analysis import DVCAnalysis, PATH_MODIFIERS
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.func import find_interpreted_age_path, GitSessionCTX, push_repositories
from pychron.dvc.meta_repo import MetaRepo, Production
from pychron.dvc.tasks.dvc_preferences import DVCConnectionItem
from pychron.envisage.browser.record_views import InterpretedAgeRecordView
from pychron.experiment.utilities.identifier import make_runid
from pychron.git.hosts import IGitHost, CredentialException
from pychron.git_archive.repo_manager import GitRepoManager, format_date, get_repository_branch
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.paths import paths, r_mkdir
from pychron.pychron_constants import RATIO_KEYS, INTERFERENCE_KEYS, NULL_STR
from pychron import json
import six

TESTSTR = {'blanks': 'auto update blanks', 'iso_evo': 'auto update iso_evo'}


class DVCException(BaseException):
    def __init__(self, attr):
        self._attr = attr

    def __repr__(self):
        return 'DVCException: neither DVCDatabase or MetaRepo have {}'.format(self._attr)

    def __str__(self):
        return self.__repr__()


class Tag(object):
    name = None
    path = None
    note = ''
    subgroup = ''

    @classmethod
    def from_analysis(cls, an, **kw):
        tag = cls()
        tag.name = an.tag
        tag.note = an.tag_note
        tag.record_id = an.record_id
        tag.repository_identifier = an.repository_identifier
        tag.path = analysis_path(an.record_id, an.repository_identifier, modifier='tags')
        tag.subgroup = an.subgroup

        for k, v in kw.items():
            setattr(tag, k, v)

        return tag

    def dump(self):
        obj = {'name': self.name,
               'note': self.note,
               'subgroup': self.subgroup}
        if not self.path:
            self.path = analysis_path(self.record_id, self.repository_identifier, modifier='tags', mode='w')

        dvc_dump(obj, self.path)


class DVCInterpretedAge(InterpretedAge):
    labnumber = None
    isotopes = None
    repository_identifier = None

    def load_tag(self, obj):
        self.tag = obj.get('name', '')
        self.tag_note = obj.get('note', '')

    def from_json(self, obj):
        for a in ('age', 'age_err', 'kca', 'kca_err', 'age_kind', 'kca_kind', 'mswd',
                  'sample', 'material', 'identifier', 'nanalyses', 'irradiation', 'name', 'project'
                                                                                          'uuid'):
            setattr(self, a, obj.get(a, NULL_STR))

        self.labnumber = self.identifier
        self.uage = ufloat(self.age, self.age_err)
        self._record_id = '{} {}'.format(self.identifier, self.name)

    def get_value(self, attr):
        try:
            return getattr(self, attr)
        except AttributeError:
            return ufloat(0, 0)

    @property
    def status(self):
        return 'X' if self.is_omitted() else ''


@provides(IDatastore)
class DVC(Loggable):
    """
    main interface to DVC backend. Delegates responsibility to DVCDatabase and MetaRepo
    """

    db = Instance('pychron.dvc.dvc_database.DVCDatabase')
    meta_repo = Instance('pychron.dvc.meta_repo.MetaRepo')

    meta_repo_name = Str
    meta_repo_dirname = Str
    organization = Str
    default_team = Str

    current_repository = Instance(GitRepoManager)
    auto_add = True
    pulled_repositories = Set
    selected_repositories = List

    data_sources = List
    data_source = Instance(DVCConnectionItem)
    favorites = List

    def __init__(self, bind=True, *args, **kw):
        super(DVC, self).__init__(*args, **kw)

        if bind:
            self._bind_preferences()
            # self.synchronize()
            # self._defaults()

    def initialize(self, inform=False):
        self.debug('Initialize DVC')

        if not self.meta_repo_name:
            self.warning_dialog('Need to specify Meta Repository name in Preferences')
            return
        try:
            self.open_meta_repo()
        except BaseException as e:
            self.warning('Error opening meta repo'.format(e))
            return

        # update meta repo.
        self.meta_pull()

        if self.db.connect():
            # self._defaults()
            return True

    def open_meta_repo(self):
        mrepo = self.meta_repo
        if self.meta_repo_name:
            name = self.meta_repo_name
            if self.meta_repo_dirname:
                name = self.meta_repo_dirname

            root = os.path.join(paths.dvc_dir, name)
            self.debug('open meta repo {}'.format(root))
            if os.path.isdir(os.path.join(root, '.git')):
                self.debug('Opening Meta Repo')
                mrepo.open_repo(root)
            else:
                url = self.make_url(self.meta_repo_name)
                self.debug('cloning meta repo url={}'.format(url))
                path = os.path.join(paths.dvc_dir, name)
                self.meta_repo.clone(url, path)
            return True

    def synchronize(self, pull=True):
        """
        pull meta_repo changes

        :return:
        """
        if pull:
            self.meta_repo.pull()
        else:
            self.meta_repo.push()

    def load_analysis_backend(self, ln, isotope_group):
        db = self.db
        with db.session_ctx():
            ip = db.get_identifier(ln)
            dblevel = ip.level
            irrad = dblevel.irradiation.name
            level = dblevel.name
            pos = ip.position

            fd = self.meta_repo.get_flux(irrad, level, pos)
            prodname, prod = self.meta_repo.get_production(irrad, level)
            cs = self.meta_repo.get_chronology(irrad)

            x = datetime.now()
            now = time.mktime(x.timetuple())
            if fd['lambda_k']:
                isotope_group.arar_constants.lambda_k = fd['lambda_k']

            isotope_group.trait_set(j=fd['j'],
                                    # lambda_k=lambda_k,
                                    production_ratios=prod.to_dict(RATIO_KEYS),
                                    interference_corrections=prod.to_dict(INTERFERENCE_KEYS),
                                    chron_segments=cs.get_chron_segments(x),
                                    irradiation_time=cs.irradiation_time,
                                    timestamp=now)
        return True

    # def sync_metadata(self, irradiation, level, dry_run=False):
    #     self.info('sync metadata {},{}'.format(irradiation, level))
    #     db = self.db
    #     with db.session_ctx():
    #         ans = db.get_analyses_by_level(irradiation, level)
    #
    #         def key(x):
    #             return x.repository_identifier
    #
    #         def ikey(x):
    #             return x.identifier
    #
    #         for reponame, ans in groupby(ans, key=key):
    #             repo = self._get_repository(reponame, as_current=False)
    #             ps = []
    #             for ln, anss in groupby(sorted(ans, key=ikey), key=ikey):
    #                 ip = db.get_identifier(ln)
    #                 dblevel = ip.level
    #                 irrad = dblevel.irradiation.name
    #                 level = dblevel.name
    #                 pos = ip.position
    #
    #                 for ai in ans:
    #                     p = analysis_path(ai.record_id, reponame)
    #
    #                     try:
    #                         obj = dvc_load(p)
    #                     except ValueError:
    #                         print('skipping {}'.format(p))
    #
    #                     sample = ip.sample.name
    #                     project = ip.sample.project.name
    #                     material = ip.sample.material.name
    #                     changed = False
    #                     for attr, v in (('sample', sample),
    #                                     ('project', project),
    #                                     ('material', material),
    #                                     ('irradiation', irrad),
    #                                     ('irradiation_level', level),
    #                                     ('irradiation_position', pos)):
    #                         ov = obj.get(attr)
    #                         if ov != v:
    #                             print('{:<20s} repo={} db={}'.format(attr, ov, v))
    #                             obj[attr] = v
    #                             changed = True
    #
    #                     if changed:
    #                         print('{}'.format(p))
    #                         ps.append(p)
    #                         if not dry_run:
    #                             dvc_dump(obj, p)
    #
    #             if ps and not dry_run:
    #                 repo.pull()
    #                 self.debug('edited paths')
    #                 for p in ps:
    #                     self.debug(p)
    #
    #                 repo.add_paths(ps)
    #                 repo.commit('<SYNC> Synced repository with database {}'.format(db.datasource_url))
    #                 repo.push()

    def repository_db_sync(self, reponame, dry_run=False):
        self.info('sync db with repo={} dry_run={}'.format(reponame, dry_run))
        repo = self._get_repository(reponame, as_current=False)
        ps = []
        db = self.db
        with db.session_ctx():
            ans = db.get_repository_analyses(reponame)

            def key(ai):
                return ai.identifier

            for ln, ans in groupby(sorted(ans, key=key), key=key):
                ip = db.get_identifier(ln)
                dblevel = ip.level
                irrad = dblevel.irradiation.name
                level = dblevel.name
                pos = ip.position
                for ai in ans:
                    p = analysis_path(ai.record_id, reponame)

                    try:
                        obj = dvc_load(p)
                    except ValueError:
                        print('skipping {}'.format(p))

                    sample = ip.sample.name
                    project = ip.sample.project.name
                    material = ip.sample.material.name
                    changed = False
                    for attr, v in (('sample', sample),
                                    ('project', project),
                                    ('material', material),
                                    ('irradiation', irrad),
                                    ('irradiation_level', level),
                                    ('irradiation_position', pos)):
                        ov = obj.get(attr)
                        if ov != v:
                            print('{:<20s} repo={} db={}'.format(attr, ov, v))
                            obj[attr] = v
                            changed = True

                    if changed:
                        print('{}'.format(p))
                        ps.append(p)
                        if not dry_run:
                            dvc_dump(obj, p)

        if ps and not dry_run:
            repo.pull()
            repo.add_paths(ps)
            repo.commit('<SYNC> Synced repository with database {}'.format(self.db.datasource_url))
            repo.push()
        self.info('finished db-repo sync for {}'.format(reponame))

    def repository_transfer(self, ans, dest):
        def key(x):
            return x.repository_identifier

        destrepo = self._get_repository(dest, as_current=False)
        for src, ais in groupby(sorted(ans, key=key), key=key):
            repo = self._get_repository(src, as_current=False)
            for ai in ais:
                ops, nps = self._transfer_analysis_to(dest, src, ai.runid)
                repo.add_paths(ops)
                destrepo.add_paths(nps)

                # update database
                dbai = self.db.get_analysis_uuid(ai.uuid)
                for ri in dbai.repository_associations:
                    if ri.repository == src:
                        ri.repository = dest

            # commit src changes
            repo.commit('Transferred analyses to {}'.format(dest))
            dest.commit('Transferred analyses from {}'.format(src))

    def _transfer_analysis_to(self, dest, src, rid):
        p = analysis_path(rid, src)
        np = analysis_path(rid, dest)

        obj = dvc_load(p)
        obj['repository_identifier'] = dest
        dvc_dump(obj, p)

        ops = [p]
        nps = [np]

        shutil.move(p, np)

        for modifier in ('baselines', 'blanks', 'extraction',
                         'intercepts', 'icfactors', 'peakcenter', '.data'):
            p = analysis_path(rid, src, modifier=modifier)
            np = analysis_path(rid, dest, modifier=modifier)
            shutil.move(p, np)
            ops.append(p)
            nps.append(np)

        return ops, nps

    def get_flux(self, irrad, level, pos):
        fd = self.meta_repo.get_flux(irrad, level, pos)
        return fd['j']

    def freeze_flux(self, ans):
        self.info('freeze flux')

        def ai_gen():
            key = lambda x: x.irradiation
            lkey = lambda x: x.level
            rkey = lambda x: x.repository_identifier

            for irrad, ais in groupby(sorted(ans, key=key), key=key):
                for level, ais in groupby(sorted(ais, key=lkey), key=lkey):
                    p = self.get_level_path(irrad, level)
                    obj = dvc_load(p)
                    if isinstance(obj, list):
                        positions = obj
                    else:
                        positions = obj['positions']

                    for repo, ais in groupby(sorted(ais, key=rkey), key=rkey):
                        yield repo, irrad, level, {ai.irradiation_position: positions[ai.irradiation_position] for ai in
                                                   ais}

        added = []

        def func(x, prog, i, n):
            repo, irrad, level, d = x
            if prog:
                prog.change_message('Freezing Flux {}{} Repository={}'.format(irrad, level, repo))

            root = os.path.join(paths.repository_dataset_dir, repo, 'flux', irrad)
            r_mkdir(root)

            p = os.path.join(root, level)
            if os.path.isfile(p):
                dd = dvc_load(p)
                dd.update(d)

            dvc_dump(d, p)
            added.append((repo, p))

        progress_loader(ai_gen(), func, threshold=1)

        self._commit_freeze(added, '<FLUX_FREEZE>')

    def freeze_production_ratios(self, ans):
        self.info('freeze production ratios')

        def ai_gen():
            key = lambda x: x.irradiation
            lkey = lambda x: x.level
            for irrad, ais in groupby(sorted(ans, key=key), key=key):
                for level, ais in groupby(sorted(ais, key=lkey), key=lkey):
                    pr = self.meta_repo.get_production(irrad, level)
                    for ai in ais:
                        yield pr, ai

        added = []

        def func(x, prog, i, n):
            pr, ai = x
            if prog:
                prog.change_message('Freezing Production {}'.format(ai.runid))

            p = analysis_path(ai.runid, ai.repository_identifier, 'productions', mode='w')
            pr.dump(path=p)
            added.append((ai.repository_identifier, p))

        progress_loader(ai_gen(), func, threshold=1)
        self._commit_freeze(added, '<PR_FREEZE>')

    def _commit_freeze(self, added, msg):
        key = lambda x: x[0]
        rr = sorted(added, key=key)
        for repo, ps in groupby(rr, key=key):
            rm = GitRepoManager()
            rm.open_repo(repo, paths.repository_dataset_dir)
            rm.add_paths(ps)
            rm.smart_pull()
            rm.commit(msg)

    # database
    # analysis manual edit
    # def manual_intercepts(self, runid, experiment_identifier, values, errors):
    #     return self._manual_edit(runid, experiment_identifier, values, errors, 'intercepts')
    #
    # def manual_blanks(self, runid, experiment_identifier, values, errors):
    #     return self._manual_edit(runid, experiment_identifier, values, errors, 'blanks')
    #
    # def manual_baselines(self, runid, experiment_identifier, values, errors):
    #     return self._manual_edit(runid, experiment_identifier, values, errors, 'baselines')
    #
    # def manual_baselines(self, runid, experiment_identifier, values, errors):
    #     return self._manual_edit(runid, experiment_identifier, values, errors, 'baselines')
    def analysis_metadata_edit(self, uuid, runid, repository_identifier, analysis_metadata, extraction_metadata,
                               identifier_metadata):
        ps = []
        if analysis_metadata:
            path = analysis_path(runid, repository_identifier)
            obj = dvc_load(path)
            obj.update(analysis_metadata)
            ps.append(path)
            dvc_dump(obj, path)

        if extraction_metadata:
            path = analysis_path(runid, repository_identifier, modifier='extraction')
            obj = dvc_load(path)
            obj.update(extraction_metadata)
            ps.append(path)
            dvc_dump(obj, path)

        if identifier_metadata:
            new_identifier = identifier_metadata.get('identifier')
            with self.db.session_ctx():
                a = self.db.get_analysis_uuid(uuid)
                if new_identifier:
                    ipid = self.db.get_irradiation_position(new_identifier)
                    if ipid is not None:
                        a.irradiation_positionID = ipid
                    else:
                        self.warning('New Identifier is invalid')

                a.aliquot = identifier_metadata.get('aliquot', a.aliquot)
                a.increment = identifier_metadata.get('increment', a.increment)

            path = analysis_path(runid, repository_identifier)
            obj = dvc_load(path)
            obj.update(identifier_metadata)
            new_runid = make_runid(obj['identifier'], obj['aliquot'], obj['increment'])
            new_path = analysis_path(new_runid, repository_identifier)
            dvc_dump(new_path, obj)
            os.remove(path)
            ps.append(path)
            ps.append(new_path)

            for mod in PATH_MODIFIERS:
                path = analysis_path(runid, repository_identifier, modifier=mod)
                new_path = analysis_path(new_runid, repository_identifier, modifier=mod)
                shutil.move(path, new_path)
                ps.append(path)
                ps.append(new_path)

        if ps:
            self.repository_add_paths(repository_identifier, ps)

    def manual_edit(self, runid, repository_identifier, values, errors, modifier):
        self.debug('manual edit {} {} {}'.format(runid, repository_identifier, modifier))
        self.debug('values {}'.format(values))
        self.debug('errors {}'.format(errors))
        path = analysis_path(runid, repository_identifier, modifier=modifier)
        obj = dvc_load(path)
        # with open(path, 'r') as rfile:
        #     obj = json.load(rfile)
        for k, v in values.items():
            o = obj[k]
            o['manual_value'] = v
            o['use_manual_value'] = True
        for k, v in errors.items():
            o = obj[k]
            o['manual_error'] = v
            o['use_manual_error'] = True

        dvc_dump(obj, path)
        return path

    def revert_manual_edits(self, runid, repository_identifier):
        ps = []
        for mod in ('intercepts', 'blanks', 'baselines', 'icfactors'):
            path = analysis_path(runid, repository_identifier, modifier=mod)
            with open(path, 'r') as rfile:
                obj = json.load(rfile)
                # for item in six.itervalues(obj):
                for item in obj.values():
                    if isinstance(item, dict):
                        item['use_manual_value'] = False
                        item['use_manual_error'] = False
            ps.append(path)
            dvc_dump(obj, path)

        msg = '<MANUAL> reverted to non manually edited'
        self.commit_manual_edits(repository_identifier, ps, msg)

    def commit_manual_edits(self, repository_identifier, ps, msg):
        if self.repository_add_paths(repository_identifier, ps):
            self.repository_commit(repository_identifier, msg)

    # analysis processing
    def analysis_has_review(self, ai, attr):
        return True
        # test_str = TESTSTR[attr]
        # repo = self._get_experiment_repo(ai.experiment_id)
        # for l in repo.get_log():
        #     if l.message.startswith(test_str):
        #         self.debug('{} {} reviewed'.format(ai, attr))
        #         return True
        # else:
        #     self.debug('{} {} not reviewed'.format(ai, attr))

    def update_analyses(self, ans, modifier, msg):
        key = lambda x: x.repository_identifier
        ans = sorted(ans, key=key)
        mod_repositories = []
        for expid, ais in groupby(ans, key=key):
            paths = [analysis_path(x.record_id, x.repository_identifier, modifier=modifier) for x in ais]
            # print expid, modifier, paths
            if self.repository_add_paths(expid, paths):
                self.repository_commit(expid, msg)
                mod_repositories.append(expid)

        # ais = map(analysis_path, ais)
        #     if self.experiment_add_analyses(exp, ais):
        #         self.experiment_commit(exp, msg)
        #         mod_experiments.append(exp)
        return mod_repositories

    def update_tag(self, an, **kw):
        tag = Tag.from_analysis(an, **kw)
        tag.dump()

        expid = an.repository_identifier
        return self.repository_add_paths(expid, tag.path)

    def save_icfactors(self, ai, dets, fits, refs):
        if fits and dets:
            self.info('Saving icfactors for {}'.format(ai))
            ai.dump_icfactors(dets, fits, refs, reviewed=True)

    def save_blanks(self, ai, keys, refs):
        if keys:
            self.info('Saving blanks for {}'.format(ai))
            ai.dump_blanks(keys, refs, reviewed=True)

    def save_fits(self, ai, keys):
        if keys:
            self.info('Saving fits for {}'.format(ai))
            ai.dump_fits(keys, reviewed=True)

    def save_flux(self, identifier, j, e):
        self.meta_pull()

        with self.session_ctx(use_parent_session=False):
            irp = self.get_identifier(identifier)
            if irp:
                level = irp.level
                irradiation = level.irradiation

                self.save_j(irradiation.name, level.name, irp.position, identifier, j, e, 0, 0, None, None)
                self.meta_commit('User manual edited flux')
        self.meta_push()

    def save_j(self, irradiation, level, pos, identifier, j, e, mj, me, decay, analyses, add=True):
        self.info('Saving j for {}{}:{} {}, j={} +/-{}'.format(irradiation, level,
                                                               pos, identifier, j, e))
        self.meta_repo.update_flux(irradiation, level, pos, identifier, j, e, mj, me, decay, analyses, add)

        with self.session_ctx(use_parent_session=False):
            ip = self.get_identifier(identifier)
            ip.j = j
            ip.j_err = e

    def remove_irradiation_position(self, irradiation, level, hole):
        db = self.db

        dbpos = db.get_irradiation_position(irradiation, level, hole)
        if dbpos:
            db.delete(dbpos)

        self.meta_repo.remove_irradiation_position(irradiation, level, hole)

    def find_interpreted_ages(self, identifiers, repositories):
        ias = [InterpretedAgeRecordView(idn, path, dvc_load(path))
               for idn in identifiers
               for path in find_interpreted_age_path(idn, repositories)]

        return ias

    def find_references_by_load(self, load, atypes, make_records=True, **kw):
        records = self.db.find_references_by_load(load, atypes, **kw)
        if records:
            if make_records:
                records = self.make_analyses(records)
            return records

    def find_references(self, times, atypes, hours, exclude=None, make_records=True, **kw):
        records = self.db.find_references(times, atypes, hours, exclude=exclude, **kw)

        if records:
            if make_records:
                records = self.make_analyses(records)
            return records

    def make_interpreted_ages(self, ias):
        def func(x, prog, i, n):
            if prog:
                prog.change_message('Making Interpreted age {}'.format(x.name))
            obj = dvc_load(x.path)
            ia = DVCInterpretedAge()
            ia.repository_identifier = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(x.path))))
            ia.from_json(obj)

            try:
                ta = analysis_path(ia.record_id, ia.repository_identifier, modifier='tags')
                if ta is not None:
                    ia.load_tag(dvc_load(ta))
            except AnalysisNotAnvailableError:
                pass

            return ia

        return progress_loader(ias, func, step=25)

    def get_analysis(self, uuid):
        an = self.db.get_analysis_uuid(uuid)
        if an:
            return self.make_analyses(an.record_views)

    def make_analysis(self, record, *args, **kw):
        a = self.make_analyses((record,), *args, **kw)
        if a:
            return a[0]

    def make_analyses(self, records, calculate_f_only=False):
        if not records:
            return []

        globalv.active_analyses = records

        # load repositories
        st = time.time()

        def func(xi, prog, i, n):
            if prog:
                prog.change_message('Syncing repository= {}'.format(xi))
            try:
                self.sync_repo(xi, use_progress=False)
            except BaseException:
                pass

        exps = {r.repository_identifier for r in records}
        progress_iterator(exps, func, threshold=1)

        # for ei in exps:
        branches = {ei: get_repository_branch(os.path.join(paths.repository_dataset_dir, ei)) for ei in exps}

        fluxes = {}
        productions = {}
        chronos = {}
        meta_repo = self.meta_repo
        for r in records:
            irrad = r.irradiation
            if irrad != 'NoIrradiation':
                level = r.irradiation_level
                flux_levels = fluxes.get(irrad, {})
                prod_levels = productions.get(irrad, {})

                if level not in flux_levels:
                    flux_levels[level] = meta_repo.get_flux_positions(irrad, level)
                if level not in prod_levels:
                    prod_levels[level] = meta_repo.get_production(irrad, level)
                if irrad not in chronos:
                    chronos[irrad] = meta_repo.get_chronology(irrad)
                fluxes[irrad] = flux_levels
                productions[irrad] = prod_levels

        make_record = self._make_record

        def func(*args):
            try:
                r = make_record(branches=branches, chronos=chronos, productions=productions,
                                fluxes=fluxes, calculate_f_only=calculate_f_only, *args)
                return r
            except BaseException:
                self.debug('make analysis exception')
                self.debug_exception()

        ret = progress_loader(records, func, threshold=1, step=25)
        et = time.time() - st

        n = len(records)

        self.debug('Make analysis time, total: {}, n: {}, average: {}'.format(et, n, et / float(n)))
        return ret

    # repositories
    def repository_add_paths(self, repository_identifier, paths):
        repo = self._get_repository(repository_identifier)
        return repo.add_paths(paths)

    def repository_commit(self, repository, msg):
        self.debug('Experiment commit: {} msg: {}'.format(repository, msg))
        repo = self._get_repository(repository)
        repo.commit(msg)

    def repository_push(self, repository, *args, **kw):
        self.debug('Pushing repository {}'.format(repository))
        repo = self._get_repository(repository)
        repo.push(*args, **kw)

    def remote_repositories(self):
        rs = []
        gs = self.application.get_services(IGitHost)
        if gs:
            for gi in gs:
                ri = gi.get_repos(self.organization)
                rs.extend(ri)
        else:
            self.warning_dialog('GitLab or GitHub plugin is required')
        return rs

    def remote_repository_names(self):
        rs = []
        gs = self.application.get_services(IGitHost)
        if gs:
            for gi in gs:
                self.debug('load repositories from {}'.format(self.organization))
                ri = gi.get_repository_names(self.organization)
                rs.extend(ri)
        else:
            self.warning_dialog('GitLab or GitHub plugin is required')
        return rs

    def check_githost_connection(self):
        git_service = self.application.get_service(IGitHost)
        return git_service.test_connection(self.organization)

    def make_url(self, name):
        git_service = self.application.get_service(IGitHost)
        return git_service.make_url(name, self.organization)

    def git_session_ctx(self, repository_identifier, message):
        return GitSessionCTX(self, repository_identifier, message)

    def sync_repo(self, name, use_progress=True):
        """
        pull or clone an repo

        """
        root = os.path.join(paths.repository_dataset_dir, name)
        exists = os.path.isdir(os.path.join(root, '.git'))
        self.debug('sync repository {}. exists={}'.format(name, exists))

        if exists:
            repo = self._get_repository(name)
            repo.pull(use_progress=use_progress)
            return True
        else:
            self.debug('getting repository from remote')
            names = self.remote_repository_names()
            service = self.application.get_service(IGitHost)
            if name in names:
                service.clone_from(name, root, self.organization)
                return True
            else:
                self.debug('name={} not in available repos from service={}, organization={}'.format(name,
                                                                                                    service.remote_url,
                                                                                                    self.organization))
                for ni in names:
                    self.debug('available repo== {}'.format(ni))

    def rollback_repository(self, expid):
        repo = self._get_repository(expid)

        cpaths = repo.get_local_changes()
        # cover changed paths to a list of analyses

        # select paths to revert
        rpaths = ('.',)
        repo.cmd('checkout', '--', ' '.join(rpaths))
        for p in rpaths:
            self.debug('revert changes for {}'.format(p))

        head = repo.get_head(hexsha=False)
        msg = 'Changes to {} reverted to Commit: {}\n' \
              'Date: {}\n' \
              'Message: {}'.format(expid, head.hexsha[:10],
                                   format_date(head.committed_date),
                                   head.message)
        self.information_dialog(msg)

    def pull_repository(self, repo):
        if isinstance(repo, (str, six.text_type)):
            r = GitRepoManager()
            r.open_repo(repo, root=paths.repository_dataset_dir)
            repo = r

        self.debug('pull repository {}'.format(repo))
        for gi in self.application.get_services(IGitHost):
            self.debug('pull to remote={}, url={}'.format(gi.default_remote_name, gi.remote_url))
            repo.smart_pull(remote=gi.default_remote_name)

    def push_repository(self, repo):
        if isinstance(repo, (str, six.text_type)):
            r = GitRepoManager()
            r.open_repo(repo, root=paths.repository_dataset_dir)
            repo = r

        self.debug('push repository {}'.format(repo))
        for gi in self.application.get_services(IGitHost):
            self.debug('pushing to remote={}, url={}'.format(gi.default_remote_name, gi.remote_url))
            repo.push(remote=gi.default_remote_name)

    def push_repositories(self, changes):
        for gi in self.application.get_services(IGitHost):
            push_repositories(changes, gi.default_remote_name, quiet=False)

    # IDatastore
    def get_greatest_aliquot(self, identifier):
        return self.db.get_greatest_aliquot(identifier)

    def get_greatest_step(self, identifier, aliquot):
        return self.db.get_greatest_step(identifier, aliquot)

    def is_connected(self):
        return self.db.connected

    def connect(self, *args, **kw):
        return self.db.connect(*args, **kw)

    # meta repo
    def update_flux(self, *args, **kw):
        self.meta_repo.update_flux(*args, **kw)

    def set_identifier(self, *args):
        self.meta_repo.set_identifier(*args)

    def update_chronology(self, name, doses):
        self.meta_repo.update_chronology(name, doses)
        self.meta_commit('updated chronology for {}'.format(name))

    def meta_pull(self, **kw):
        return self.meta_repo.smart_pull(**kw)

    def meta_push(self):
        self.meta_repo.push()

    def meta_add_all(self):
        self.meta_repo.add_unstaged(paths.meta_root, add_all=True)

    def meta_commit(self, msg):
        changes = self.meta_repo.has_staged()
        if changes:
            self.debug('meta repo has changes: {}'.format(changes))
            self.meta_repo.report_status()
            self.meta_repo.commit(msg)
            self.meta_repo.clear_cache = True
        else:
            self.debug('no changes to meta repo')

    def add_production(self, irrad, name, prod):
        self.meta_repo.add_production_to_irradiation(irrad, name, prod)

    def get_production(self, irrad, name):
        return self.meta_repo.get_production(irrad, name)

    # get
    def get_local_repositories(self):
        return list_subdirectories(paths.repository_dataset_dir)

    def get_repository(self, exp):
        return self._get_repository(exp)

    def get_meta_head(self):
        return self.meta_repo.get_head()

    def get_irradiation_geometry(self, irrad, level):
        dblevel = self.db.get_irradiation_level(irrad, level)
        return self.meta_repo.get_irradiation_holder_holes(dblevel.holder)

    def get_irradiation_names(self):
        irrads = self.db.get_irradiations()
        return [i.name for i in irrads]

    # add
    def add_interpreted_age(self, ia):

        a = ia.get_ma_scaled_age()
        mswd = ia.preferred_mswd

        if isnan(mswd):
            mswd = 0
        d = {attr: getattr(ia, attr) for attr in ('sample', 'material', 'project', 'identifier', 'nanalyses',
                                                  'irradiation',
                                                  'name', 'uuid', 'include_j_error_in_mean',
                                                  'include_j_error_in_plateau',
                                                  'include_j_error_in_individual_analyses')}
        d.update(age=float(nominal_value(a)),
                 age_err=float(std_dev(a)),
                 display_age_units=ia.age_units,
                 age_kind=ia.preferred_age_kind,
                 kca_kind=ia.preferred_kca_kind,
                 kca=float(ia.preferred_kca_value),
                 kca_err=float(ia.preferred_kca_error),
                 mswd=float(mswd),
                 arar_constants=ia.arar_constants.to_dict(),
                 analyses=[dict(uuid=ai.uuid,
                                record_id=ai.record_id,
                                tag=ai.tag, plateau_step=ia.get_is_plateau_step(ai)) for ai in
                           ia.all_analyses])

        if self.macrochron_enabled:
            d['macrochron'] = self._make_macrochron(ia)

        self._add_interpreted_age(ia, d)

    def add_repository_association(self, expid, runspec):
        db = self.db
        dban = db.get_analysis_uuid(runspec.uuid)
        if dban:
            for e in dban.repository_associations:
                if e.repository == expid:
                    break
            else:
                db.add_repository_association(expid, dban)

            src_expid = runspec.repository_identifier
            if src_expid != expid:
                repo = self._get_repository(expid)

                for m in PATH_MODIFIERS:
                    src = analysis_path(runspec.record_id, src_expid, modifier=m)
                    dest = analysis_path(runspec.record_id, expid, modifier=m, mode='w')

                    shutil.copyfile(src, dest)
                    repo.add(dest, commit=False)
                repo.commit('added repository association')
        else:
            self.warning('{} not in the database {}'.format(runspec.runid, self.db.name))

    def add_material(self, name, grainsize=None):
        db = self.db
        added = False
        if not db.get_material(name, grainsize):
            added = True
            db.add_material(name, grainsize)

        return added

    def add_project(self, name, principal_investigator=None, **kw):
        added = False
        db = self.db
        if not db.get_project(name, principal_investigator):
            added = True
            db.add_project(name, principal_investigator, **kw)
        return added

    def add_sample(self, name, project, pi, material, grainsize=None, note=None, **kw):
        added = False
        db = self.db
        if not db.get_sample(name, project, pi, material, grainsize):
            added = True
            db.add_sample(name, project, pi, material, grainsize, note=note, **kw)
        return added

    def add_principal_investigator(self, name, **kw):
        added = False
        db = self.db
        if not db.get_principal_investigator(name):
            db.add_principal_investigator(name, **kw)
            added = True
        return added

    def add_irradiation_position(self, irrad, level, pos, identifier=None, **kw):
        db = self.db
        added = False
        if not db.get_irradiation_position(irrad, level, pos):
            db.add_irradiation_position(irrad, level, pos, identifier, **kw)
            self.meta_repo.add_position(irrad, level, pos)
            added = True
        return added

    def add_irradiation_level(self, name, irradiation, holder, production_name, **kw):
        added = False
        dblevel = self.get_irradiation_level(irradiation, name)
        if dblevel is None:
            added = True
            self.db.add_irradiation_level(name, irradiation, holder, production_name, **kw)

        self.meta_repo.add_level(irradiation, name)
        self.meta_repo.update_level_production(irradiation, name, production_name)
        return added

    def clone_repository(self, identifier):
        root = os.path.join(paths.repository_dataset_dir, identifier)
        if not os.path.isdir(root):
            self.debug('cloning {}'.format(root))
            url = self.make_url(identifier)
            Repo.clone_from(url, root)
        else:
            self.debug('{} already exists'.format(identifier))

    def add_repository(self, identifier, principal_investigator, inform=True):
        self.debug('trying to add repository identifier={}, pi={}'.format(identifier, principal_investigator))

        root = os.path.join(paths.repository_dataset_dir, identifier)
        if os.path.isdir(root):
            self.debug('already a directory {}'.format(identifier))
            return True

        names = self.remote_repository_names()
        if identifier in names:
            # make sure also in the database
            self.db.add_repository(identifier, principal_investigator)

            if inform:
                self.warning_dialog('Repository "{}" already exists'.format(identifier))
            return True

        else:
            if os.path.isdir(root):
                self.db.add_repository(identifier, principal_investigator)
                if inform:
                    self.warning_dialog('{} already exists.'.format(root))
            else:
                gs = self.application.get_services(IGitHost)
                ret = False
                for i, gi in enumerate(gs):
                    self.info('Creating repository at {}. {}'.format(gi.name, identifier))

                    if gi.create_repo(identifier, organization=self.organization, auto_init=True):
                        ret = True
                        if self.default_team:
                            gi.set_team(self.default_team, self.organization, identifier,
                                        permission='push')

                        url = gi.make_url(identifier, self.organization)
                        if i == 0:
                            try:
                                repo = Repo.clone_from(url, root)
                            except BaseException as e:
                                self.debug('failed cloning repo. {}'.format(e))
                                ret = False

                            self.db.add_repository(identifier, principal_investigator)
                        else:
                            repo.create_remote(gi.default_remote_name or 'origin', url)

                return ret

    def add_irradiation(self, name, doses=None, add_repo=False, principal_investigator=None):
        if self.db.get_irradiation(name):
            self.warning('irradiation {} already exists'.format(name))
            return

        self.db.add_irradiation(name)

        self.meta_repo.add_irradiation(name)
        self.meta_repo.add_chronology(name, doses)

        root = os.path.join(paths.meta_root, name)
        p = os.path.join(root, 'productions')
        if not os.path.isdir(p):
            os.mkdir(p)
        with open(os.path.join(root, 'productions.json'), 'w') as wfile:
            json.dump({}, wfile)

        if add_repo and principal_investigator:
            self.add_repository('Irradiation-{}'.format(name), principal_investigator)

        return True

    def add_load_holder(self, name, path_or_txt):
        self.db.add_load_holder(name)
        self.meta_repo.add_load_holder(name, path_or_txt)

    def copy_production(self, pr):
        """

        @param pr: irrad_ProductionTable object
        @return:
        """
        pname = pr.name.replace(' ', '_')
        path = os.path.join(paths.meta_root, 'productions', '{}.json'.format(pname))
        if not os.path.isfile(path):
            obj = {}
            for attr in INTERFERENCE_KEYS + RATIO_KEYS:
                obj[attr] = [getattr(pr, attr), getattr(pr, '{}_err'.format(attr))]
            dvc_dump(obj, path)

    def save_tag_subgroup_items(self, items):
        key = attrgetter('repository_identifier')

        for expid, ans in groupby(sorted(items, key=key), key=key):
            self.sync_repo(expid)
            cs = []
            for it in ans:
                if self.update_tag(it):
                    cs.append(it)
            self._commit_tags(cs, expid, '<SUBGROUP>')

    def _commit_tags(self, cs, expid, msg):
        if cs:
            cc = [c.record_id for c in cs]
            if len(cc) > 1:
                cstr = '{} - {}'.format(cc[0], cc[-1])
            else:
                cstr = cc[0]

            self.repository_commit(expid, '{} {}'.format(msg, cstr))

            for ci in cs:
                ci.refresh_view()

    def tag_items(self, tag, items, note=''):
        key = attrgetter('repository_identifier')
        with self.db.session_ctx() as sess:
            for expid, ans in groupby(sorted(items, key=key), key=key):
                self.sync_repo(expid)

                cs = []
                for it in ans:
                    if not isinstance(it, (InterpretedAge, DVCAnalysis)):
                        it = self.make_analysis(it)

                    self.debug('setting {} tag= {}'.format(it.record_id, tag))
                    if not isinstance(it, InterpretedAge):
                        self.set_analysis_tag(it.uuid, tag)

                    it.set_tag({'name': tag, 'note': note or ''})
                    if self.update_tag(it):
                        cs.append(it)
                        # it.refresh_view()
                sess.commit()

                self._commit_tags(cs, expid, '<TAG> {:<6s}'.format(tag))
                # if cs:
                #     cc = [c.record_id for c in cs]
                #     if len(cc) > 1:
                #         cstr = '{} - {}'.format(cc[0], cc[-1])
                #     else:
                #         cstr = cc[0]
                #
                #     self.repository_commit(expid, '<TAG> {:<6s} {}'.format(tag, cstr))
                #
                #     for ci in cs:
                #         ci.refresh_view()

    # private
    def _make_macrochron(self, ia):
        m = {'material': ia.material,
             'lithology': ia.lithology,
             'reference': ia.reference,
             'rlocation': ia.rlocation}
        return m

    def _add_interpreted_age(self, ia, d):
        rid = ia.repository_identifier
        p = analysis_path(ia.identifier, rid, modifier='ia', mode='w')

        i = 0
        while os.path.isfile(p):
            p = analysis_path('{}_{:05d}'.format(ia.identifier, i), rid, modifier='ia', mode='w')
            i += 1

        self.debug('saving interpreted age. {}'.format(p))
        dvc_dump(d, p)
        if self.repository_add_paths(rid, p):
            self.repository_commit(rid, '<IA> added interpreted age {}'.format(ia.name))

    def _load_repository(self, expid, prog, i, n):
        if prog:
            prog.change_message('Loading repository {}. {}/{}'.format(expid, i, n))
        self.sync_repo(expid)

    def _make_record(self, record, prog, i, n, productions=None, chronos=None, branches=None, fluxes=None,
                     calculate_f_only=False):
        meta_repo = self.meta_repo
        if prog:
            # this accounts for ~85% of the time!!!
            prog.change_message('Loading analysis {}. {}/{}'.format(record.record_id, i, n))

        expid = record.repository_identifier
        if not expid:
            exps = record.repository_ids
            self.debug('Analysis {} is associated multiple repositories '
                       '{}'.format(record.record_id, ','.join(exps)))
            expid = None
            if self.selected_repositories:
                rr = [si for si in self.selected_repositories if si in exps]
                if rr:
                    if len(rr) > 1:
                        expid = self._get_requested_experiment_id(rr)
                    else:
                        expid = rr[0]

            if expid is None:
                expid = self._get_requested_experiment_id(exps)

        if isinstance(record, DVCAnalysis):
            a = record
        else:
            # self.debug('use_repo_suffix={} record_id={}'.format(record.use_repository_suffix, record.record_id))
            try:
                rid = record.record_id
                if record.use_repository_suffix:
                    rid = '-'.join(rid.split('-')[:-1])
                a = DVCAnalysis(rid, expid)
                a.group_id = record.group_id
            except AnalysisNotAnvailableError:
                self.info('Analysis {} not available. Trying to clone repository "{}"'.format(rid, expid))
                try:
                    self.sync_repo(expid)
                except (CredentialException, BaseException):
                    self.warning_dialog('Invalid credentials for GitHub/GitLab')
                    return

                try:
                    a = DVCAnalysis(rid, expid)

                except AnalysisNotAnvailableError:
                    self.warning_dialog('Analysis {} not in repository {}'.format(rid, expid))
                    return

            a.loadname = record.loadname
            # get repository branch
            a.branch = branches.get(expid, '')
            # a.branch = get_repository_branch(os.path.join(paths.repository_dataset_dir, expid))
            # print 'asdfdffff {}'.format(time.time() - st)
            # a.set_tag(record.tag)
            # load irradiation
            if a.irradiation and a.irradiation not in ('NoIrradiation',):
                # self.debug('Irradiation {}'.format(a.irradiation))
                if chronos:
                    chronology = chronos[a.irradiation]
                else:
                    chronology = meta_repo.get_chronology(a.irradiation)
                a.set_chronology(chronology)

                frozen_production = self._get_frozen_production(rid, a.repository_identifier)
                if frozen_production:
                    pname, prod = frozen_production.name, frozen_production
                else:
                    if productions:
                        pname, prod = productions[a.irradiation][a.irradiation_level]
                    else:
                        pname, prod = meta_repo.get_production(a.irradiation, a.irradiation_level)

                a.set_production(pname, prod)

                if fluxes:
                    level_flux = fluxes[a.irradiation][a.irradiation_level]
                    fd = meta_repo.get_flux_from_positions(record.irradiation_position_position, level_flux)
                else:
                    fd = meta_repo.get_flux(record.irradiation,
                                            record.irradiation_level,
                                            record.irradiation_position_position)
                a.j = fd['j']
                if fd['lambda_k']:
                    a.arar_constants.lambda_k = fd['lambda_k']

                a.standard_age = fd['standard_age']
                a.standard_name = fd['standard_name']
                a.standard_material = fd['standard_material']

                if calculate_f_only:
                    a.calculate_F()
                else:
                    a.calculate_age()
        return a

    def _get_frozen_production(self, rid, repo):
        path = analysis_path(rid, repo, 'productions')
        if path:
            return Production(path)

    def _get_repository(self, repository_identifier, as_current=True):
        repo = None
        if as_current:
            repo = self.current_repository

        path = repository_path(repository_identifier)

        if repo is None or repo.path != path:
            self.debug('make new repomanager for {}'.format(path))
            repo = GitRepoManager()
            repo.path = path
            repo.open_repo(path)
            if as_current:
                self.current_repository = repo

        return repo

    def _bind_preferences(self):

        # prefid = 'pychron.dvc'
        # for attr in ('meta_repo_dirname', 'meta_repo_name', 'organization', 'default_team'):
        #     bind_preference(self, attr, '{}.{}'.format(prefid, attr))

        prefid = 'pychron.dvc.connection'
        bind_preference(self, 'favorites', '{}.favorites'.format(prefid))
        self._favorites_changed(self.favorites)
        self._set_meta_repo_name()

    def _favorites_changed(self, items):
        try:
            ds = [DVCConnectionItem(attrs=f, load_names=False) for f in items]
            self.data_sources = [d for d in ds if d.enabled]

        except BaseException:
            pass

        if self.data_sources:
            self.data_source = next((d for d in self.data_sources if d.default and d.enabled), None)

    def _data_source_changed(self, old, new):
        self.debug('data source changed. {}, db={}'.format(new, id(self.db)))
        if new is not None:
            for attr in ('username', 'password', 'host', 'kind', 'path'):
                setattr(self.db, attr, getattr(new, attr))

            self.db.name = new.dbname
            self.organization = new.organization
            self.meta_repo_name = new.meta_repo_name
            self.meta_repo_dirname = new.meta_repo_dir
            self.db.reset_connection()
            if old:
                self.db.connect()
                self.db.create_session()

    def _meta_repo_dirname_changed(self):
        self._set_meta_repo_name()

    def _meta_repo_name_changed(self):
        self._set_meta_repo_name()

    def _set_meta_repo_name(self):
        name = self.meta_repo_name
        if self.meta_repo_dirname:
            name = self.meta_repo_dirname

        paths.meta_root = os.path.join(paths.dvc_dir, name)

    def _defaults(self):
        self.debug('writing defaults')
        # self.db.create_all(Base.metadata)
        self.db.add_save_user()
        for tag, func in (('irradiation holders', self._add_default_irradiation_holders),
                          ('productions', self._add_default_irradiation_productions),
                          ('load holders', self._add_default_load_holders)):

            d = os.path.join(self.meta_repo.path, tag.replace(' ', '_'))
            if not os.path.isdir(d):
                os.mkdir(d)

            if self.auto_add:
                func()
            elif self.confirmation_dialog('You have no {}. Would you like to add some defaults?'.format(tag)):
                func()

    def _add_default_irradiation_productions(self):
        ds = (('TRIGA.txt', TRIGA),)
        self._add_defaults(ds, 'productions')

    def _add_default_irradiation_holders(self):
        ds = (('24Spokes.txt', HOLDER_24_SPOKES),)
        self._add_defaults(ds, 'irradiation_holders', )

    def _add_default_load_holders(self):
        ds = (('221.txt', LASER221),
              ('65.txt', LASER65))
        self._add_defaults(ds, 'load_holders', self.db.add_load_holder)

    def _add_defaults(self, defaults, root, dbfunc=None):
        commit = False
        repo = self.meta_repo
        for name, txt in defaults:
            p = os.path.join(repo.path, root, name)
            if not os.path.isfile(p):
                with open(p, 'w') as wfile:
                    wfile.write(txt)
                repo.add(p, commit=False)
                commit = True
                if dbfunc:
                    name = remove_extension(name)
                    dbfunc(name)

        if commit:
            repo.commit('added default {}'.format(root.replace('_', ' ')))

    def __getattr__(self, item):
        try:
            return getattr(self.db, item)
        except AttributeError:
            try:
                return getattr(self.meta_repo, item)
            except AttributeError as e:
                print(e, item)
                # raise DVCException(item)

    # defaults
    def _db_default(self):
        return DVCDatabase(kind='mysql',
                           username='root',
                           password='Argon',
                           host='localhost',
                           name='pychronmeta')

    def _meta_repo_default(self):
        return MetaRepo()


if __name__ == '__main__':
    paths.build('_dev')
    idn = '24138'
    exps = ['Irradiation-NM-272']
    print(find_interpreted_age_path(idn, exps))
    # d = DVC(bind=False)
    # with open('/Users/ross/Programming/githubauth.txt') as rfile:
    #     usr = rfile.readline().strip()
    #     pwd = rfile.readline().strip()
    # d.github_user = usr
    # d.github_password = pwd
    # d.organization = 'NMGRLData'
    # d.add_experiment('Irradiation-NM-273')
# ============= EOF =============================================
