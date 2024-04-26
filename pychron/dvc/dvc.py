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

import os
import shutil
import time
from datetime import datetime
from itertools import groupby
from operator import itemgetter

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from git import Repo, GitCommandError, NoSuchPathError, Actor
from traits.api import Instance, Str, Set, List, provides, Bool, Int
from uncertainties import ufloat, std_dev, nominal_value

from pychron import json
from pychron.core.helpers.filetools import (
    remove_extension,
    list_subdirectories,
    list_directory,
    add_extension,
)
from pychron.core.helpers.iterfuncs import groupby_key, groupby_repo
from pychron.core.i_datastore import IDatastore
from pychron.core.progress import progress_loader, progress_iterator, open_progress
from pychron.dvc import (
    dvc_dump,
    dvc_load,
    analysis_path,
    repository_path,
    AnalysisNotAnvailableError,
    PATH_MODIFIERS,
    USE_GIT_TAGGING,
)
from pychron.dvc.cache import DVCCache
from pychron.dvc.defaults import TRIGA, HOLDER_24_SPOKES, LASER221, LASER65
from pychron.dvc.dvc_analysis import DVCAnalysis
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.func import (
    find_interpreted_age_path,
    GitSessionCTX,
    push_repositories,
    make_interpreted_age_dict,
)
from pychron.dvc.meta_repo import MetaRepo, get_frozen_flux, get_frozen_productions
from pychron.dvc.tasks.dvc_preferences import DVCConnectionItem
from pychron.dvc.util import Tag, DVCInterpretedAge
from pychron.envisage.browser.record_views import InterpretedAgeRecordView
from pychron.experiment.utilities.runid import make_increment, make_runid
from pychron.git.hosts import IGitHost
from pychron.git.hosts.local import LocalGitHostService
from pychron.git_archive.author_view import GitCommitAuthorView
from pychron.git_archive.repo_manager import (
    GitRepoManager,
    format_date,
    get_repository_branch,
)
from pychron.git_archive.views import StatusView
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.paths import paths, r_mkdir
from pychron.processing.interpreted_age import InterpretedAge
from pychron.pychron_constants import (
    RATIO_KEYS,
    INTERFERENCE_KEYS,
    STARTUP_MESSAGE_POSITION,
    DATE_FORMAT,
)
from pychron.user.user import User

HOST_WARNING_MESSAGE = "GitLab or GitHub or LocalGit plugin is required"


@provides(IDatastore)
class DVC(Loggable):
    """
    main interface to DVC backend. Delegates responsibility to DVCDatabase and MetaRepo
    """

    db = Instance("pychron.dvc.dvc_database.DVCDatabase")
    meta_repo = Instance("pychron.dvc.meta_repo.MetaRepo")

    meta_repo_name = Str
    meta_repo_dirname = Str
    organization = Str
    default_team = Str

    current_repository = Instance(GitRepoManager)
    auto_add = True
    use_auto_pull = Bool(True)
    use_auto_push = Bool(False)
    use_default_commit_author = Bool(False)

    pulled_repositories = Set
    selected_repositories = List

    data_sources = List
    data_source = Instance(DVCConnectionItem)
    favorites = List

    update_currents_enabled = Bool
    use_cocktail_irradiation = Str
    use_cache = Bool
    max_cache_size = Int
    irradiation_prefix = Str
    irradiation_project_prefix = Str

    git_service = None
    _cache = None
    _uuid_runid_cache = None
    _pull_cache = None
    _author = None

    def __init__(self, bind=True, *args, **kw):
        super(DVC, self).__init__(*args, **kw)
        self._uuid_runid_cache = {}
        self._pull_cache = {}
        if bind:
            self._bind_preferences()

    def initialize(self, inform=False):
        self.debug("Initialize DVC")

        if not self.meta_repo_name:
            self.warning_dialog(
                "Need to specify Meta Repository name in Preferences",
                position=STARTUP_MESSAGE_POSITION,
            )
            return
        try:
            self.open_meta_repo()
        except BaseException as e:
            self.warning("Error opening meta repo {}".format(e))
            return

        # update meta repo.
        self.meta_pull()

        if self.db.connect():
            return True

    def get_data_reduction_loads(self):
        return self.meta_repo.get_data_reduction_loads()

    def save_data_reduction_manifest(self, manifest):
        self.meta_repo.save_data_reduction_manifest(manifest)

    def save_data_reduction_loads(self, objs):
        self.meta_repo.save_data_reduction_loads(objs)

    def backup_data_reduction_loads(self):
        self.meta_repo.backup_data_reduction_loads()

    def share_data_reduction_loads(self):
        self.meta_repo.share_data_reduction_loads()

    def fix_identifier(
        self,
        src_uuid,
        src_id,
        dest_id,
        repo_identifier,
        dest_identifier,
        dest_aliquot,
        dest_step,
    ):
        self.info("converting {} to {}".format(src_id, dest_id))
        err = self.db.map_runid(src_id, dest_id)

        if err:
            self.warning_dialog(err)
            return []

        # fix git files
        root = paths.repository_dataset_dir

        # get via uuid  if it exists then no need to make a new dest
        sp = analysis_path(src_uuid, repo_identifier, root=root)
        dp = None
        temps = []
        if sp is None:
            sp = analysis_path(src_id, repo_identifier, root=root)
            dp = analysis_path(
                dest_id, repo_identifier, root=root, mode="w", is_temp=True
            )
            temps = [dp]

        if not sp or not os.path.isfile(sp):
            self.info("not a file. {}".format(sp))
            return

        jd = dvc_load(sp)
        jd["identifier"] = dest_identifier

        dbip = self.db.get_identifier(dest_identifier)

        jd["irradiation"] = dbip.level.irradiation.name
        jd["irradiation_level"] = dbip.level.name
        jd["irradiation_position"] = dbip.position

        if dest_aliquot:
            jd["aliquot"] = dest_aliquot
        if dest_step:
            jd["increment"] = make_increment(dest_step)

        self.debug("{}>>{}".format(sp, dp))

        if dp is None:
            dvc_dump(jd, sp)
        else:
            dvc_dump(jd, dp)
            os.remove(sp)

            for modifier in (
                "baselines",
                "blanks",
                "extraction",
                "intercepts",
                "icfactors",
                "peakcenter",
                ".data",
            ):
                sp = analysis_path(
                    src_id, repo_identifier, modifier=modifier, root=root
                )

                dp = analysis_path(
                    dest_id,
                    repo_identifier,
                    modifier=modifier,
                    root=root,
                    mode="w",
                    is_temp=True,
                )

                if sp and os.path.isfile(sp):
                    self.debug("{}>>{}".format(sp, dp))
                    shutil.move(sp, dp)
                    temps.append(dp)

        return temps

    def generate_currents(self):
        if not self.update_currents_enabled:
            self.information_dialog(
                'You must enable "Current Values" in Preferences/DVC'
            )
            return

        if not self.confirmation_dialog(
            "Are you sure you want to generate current values for the entire database? "
            "This could take a while!"
        ):
            return

        self.info("Generate currents started")
        # group by repository
        db = self.db
        db.create_session()
        ocoa = db.commit_on_add
        db.commit_on_add = False

        def chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i : i + n]

        def func(ai, prog, i, n):
            if prog:
                if not i % 10:
                    prog.change_message(
                        "Updating Currents {} {}/{}".format(ai.record_id, i, n)
                    )
                else:
                    prog.increment()

            ai.load_raw_data()
            dban = db.get_analysis_uuid(ai.uuid)
            if ai.analysis_type in ("unknown", "cocktail"):
                try:
                    self._update_current_age(ai, dban=dban, force=True)
                except BaseException as e:
                    self.warning(
                        "Failed making current age for {}: {}".format(ai.record_id, e)
                    )

            if not ai.analysis_type.lower().startswith("blank"):
                try:
                    self._update_current_blanks(
                        ai, dban=dban, force=True, update_age=False, commit=False
                    )
                except BaseException as e:
                    self.warning(
                        "Failed making current blanks for {}: {}".format(
                            ai.record_id, e
                        )
                    )
            try:
                self._update_current(
                    ai, dban=dban, force=True, update_age=False, commit=False
                )
            except BaseException as e:
                self.warning(
                    "Failed making intensities for {}: {}".format(ai.record_id, e)
                )

            # if not i % 100:
            #     db.commit()
            #     db.flush()

        with db.session_ctx():
            for repo in db.get_repositories():
                if repo.name in (
                    "JIRSandbox",
                    "REEFenite",
                    "Henry01184",
                    "FractionatedRes",
                    "PowerZPattern",
                ):
                    continue
                self.debug("Updating currents for {}".format(repo.name))
                try:
                    st = time.time()
                    tans = db.get_repository_analysis_count(repo.name)

                    ans = db.get_analyses_no_current(repo.name)
                    self.debug(
                        "Total repo analyses={}, filtered={}".format(tans, len(ans))
                    )

                    if not ans:
                        continue

                    # if not self.confirmation_dialog('Updated currents for {}'.format(repo.name)):
                    #     if self.confirmation_dialog('Stop update'):
                    #         break
                    #     else:
                    #         continue

                    for chunk in chunks(ans, 200):
                        chunk = self.make_analyses(chunk)
                        if chunk:
                            progress_iterator(chunk, func)
                        db.commit()
                        db.flush()

                    self.info(
                        "Elapsed time {}: n={}, "
                        "{:0.2f} min".format(repo.name, len(ans), (time.time() - st))
                        / 60.0
                    )
                    db.commit()
                    db.flush()
                except BaseException as e:
                    self.warning(
                        "Failed making analyses for {}: {}".format(repo.name, e)
                    )

        db.commit_on_add = ocoa
        db.close_session()
        self.info("Generate currents finished")

    def convert_uuid_runids(self, uuids):
        with self.db.session_ctx():
            ans = self.db.get_analyses_uuid(uuids)
            return [an.record_id for an in ans]

        # if uuid in self._uuid_runid_cache:
        #     r = self._uuid_runid_cache[uuid]
        # else:
        #     with self.db.session_ctx():
        #         an = self.db.get_analysis_uuid(uuid)
        #         r = an.record_id
        #         self._uuid_runid_cache[uuid] = r
        # return r

    def find_record(self, r):
        def update_record(jobj):
            r.record_id = make_runid(
                jobj["identifier"], jobj["aliquot"], jobj["increment"]
            )
            r.irradiation = jobj["irradiation"]
            r.irradiation_level = jobj["irradiation_level"]
            r.irradiation_position = jobj["irradiation_position"]

        path = analysis_path(
            (r.uuid, r.record_id), r.repository_identifier, root=r.repository_root
        )
        if path:
            with open(path, "r") as rfile:
                jobj = json.load(rfile)
                update_record(jobj)
            return [jobj]
        elif r.uuid:
            # analysis may have been saved using record_id as the path instead of the uuid
            # search for a match
            root = os.path.join(r.repository_root, r.repository_identifier)
            potential = []
            for cd in os.listdir(root):
                if cd.startswith("."):
                    continue
                cd = os.path.join(root, cd)
                if os.path.isdir(cd):
                    for f in os.listdir(cd):
                        if f.startswith("."):
                            continue

                        p = os.path.join(cd, f)
                        if p.endswith(".json"):
                            with open(p, "r") as rfile:
                                jobj = json.load(rfile)
                                juuid = jobj.get("uuid", "")
                                if r.uuid == juuid[: len(r.uuid)]:
                                    potential.append(jobj)
                                    update_record(jobj)
                                    # return True
            return potential

    def find_reference_repos(self, repo):
        irradiations = self.db.get_repository_irradiations(repo)
        low, high = self.db.get_repository_analyses_date_range(repo)
        mss = self.db.get_repository_mass_spectrometers(repo)
        mss = [mi.capitalize() for mi in mss]

        self.debug("{} {}".format(low, high))
        repos = []
        if low.month <= 6:
            year = low.year
            year = str(year)[-2:]
            repos.extend(["{}_air{}0".format(mi, year) for mi in mss])
            repos.extend(["{}_blank{}0".format(mi, year) for mi in mss])
            repos.extend(["{}_cocktail{}0".format(mi, year) for mi in mss])

        if high.month >= 6 or low.month >= 6:
            year = high.year
            year = str(year)[-2:]
            repos.extend(["{}_air{}1".format(mi, year) for mi in mss])
            repos.extend(["{}_blank{}1".format(mi, year) for mi in mss])
            repos.extend(["{}_cocktail{}1".format(mi, year) for mi in mss])

        irradiation_project_prefix = self.irradiation_project_prefix
        repos.extend(
            ["{}{}".format(irradiation_project_prefix, ir) for ir in irradiations]
        )
        self.debug("reference repos {}".format(repos))
        return list(set(repos))

    def find_associated_identifiers(self, samples):
        from pychron.dvc.associated_identifiers import AssociatedIdentifiersView

        av = AssociatedIdentifiersView()
        for s in samples:
            dbids = self.db.get_irradiation_position_by_sample(
                s.name, s.material, s.grainsize, s.principal_investigator, s.project
            )
            av.add_items(dbids)

        av.edit_traits(kind="modal")

    def open_meta_repo(self):
        mrepo = self.meta_repo
        if self.meta_repo_name:
            name = self.meta_repo_name
            if self.meta_repo_dirname:
                name = self.meta_repo_dirname

            root = os.path.join(paths.dvc_dir, name)
            self.debug("open meta repo {}".format(root))
            if os.path.isdir(os.path.join(root, ".git")):
                self.debug("Opening Meta Repo")
                mrepo.open_repo(root)
            else:
                url = self.make_url(self.meta_repo_name)
                if url:
                    self.debug("cloning meta repo url={}".format(url))
                    path = os.path.join(paths.dvc_dir, name)
                    self.meta_repo.clone(url, path)
                else:
                    self.debug(
                        "no url returned for MetaData repository. You need to clone your MetaData repository "
                        "manually"
                    )
                    return False

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
            if ip is not None:
                dblevel = ip.level
                irrad = dblevel.irradiation.name
                level = dblevel.name
                pos = ip.position

                fd = self.meta_repo.get_flux(irrad, level, pos)
                _, prod = self.meta_repo.get_production(irrad, level, allow_null=True)
                cs = self.meta_repo.get_chronology(irrad, allow_null=True)

                x = datetime.now()
                now = time.mktime(x.timetuple())
                if fd["lambda_k"]:
                    isotope_group.arar_constants.lambda_k = fd["lambda_k"]

                try:
                    pr = prod.to_dict(RATIO_KEYS)
                except BaseException as e:
                    self.debug("invalid production. error={}".format(e))
                    pr = {}

                try:
                    ic = prod.to_dict(INTERFERENCE_KEYS)
                except BaseException as e:
                    self.debug("invalid production. error={}".format(e))
                    ic = {}

                isotope_group.trait_set(
                    j=fd["j"],
                    # lambda_k=lambda_k,
                    production_ratios=pr,
                    interference_corrections=ic,
                    chron_segments=cs.get_chron_segments(x),
                    irradiation_time=cs.irradiation_time,
                    timestamp=now,
                )
        return True

    def analyses_db_sync(self, ln, ais, reponame):
        self.info("sync db with analyses")
        return self._sync_info(ln, ais, reponame)

    def repository_db_sync(self, reponame, dry_run=False):
        self.info("sync db with repo={} dry_run={}".format(reponame, dry_run))
        repo = self._get_repository(reponame, as_current=False)
        db = self.db
        repo.pull()
        ps = []
        with db.session_ctx():
            ans = db.get_repository_analyses(reponame)
            groups = [(g[0], list(g[1])) for g in groupby_key(ans, "identifier")]
            progress = open_progress(len(groups))

            for ln, ais in groups:
                progress.change_message("Syncing identifier: {}".format(ln))
                pss = self._sync_info(ln, ais, reponame, dry_run)
                ps.extend(pss)

            progress.close()

        if ps and not dry_run:
            # repo.pull()
            repo.add_paths(ps)
            repo.commit(
                "<SYNC> Synced repository with database {}".format(
                    self.db.public_datasource_url
                )
            )
            repo.push()
        self.info("finished db-repo sync for {}".format(reponame))

    def _sync_info(self, ln, ais, reponame, dry_run=False):
        db = self.db
        ip = db.get_identifier(ln)
        dblevel = ip.level
        irrad = dblevel.irradiation.name
        level = dblevel.name
        pos = ip.position
        ps = []

        for ai in ais:
            p = analysis_path(ai, reponame)
            if p and os.path.isfile(p):
                try:
                    obj = dvc_load(p)
                except ValueError:
                    self.warning("Skipping {}. invalid file".format(p))
                    continue
            else:
                self.warning("Skipping {}. no file".format(ai.record_id))
                continue

            sample = ip.sample.name
            project = ip.sample.project.name
            material = ip.sample.material.name
            changed = False
            for attr, v in (
                ("sample", sample),
                ("project", project),
                ("material", material),
                ("irradiation", irrad),
                ("irradiation_level", level),
                ("irradiation_position", pos),
            ):
                ov = obj.get(attr)
                if ov != v:
                    self.info("{:<20s} repo={} db={}".format(attr, ov, v))
                    obj[attr] = v
                    changed = True

            if changed:
                self.debug("{}".format(p))
                ps.append(p)
                if not dry_run:
                    dvc_dump(obj, p)
        return ps

    def repository_transfer(self, ans, dest):
        destrepo = self._get_repository(dest, as_current=False)
        for src, ais in groupby_repo(ans):
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
            repo.commit("Transferred analyses to {}".format(dest))
            dest.commit("Transferred analyses from {}".format(src))

    def get_flux(self, irrad, level, pos):
        fd = self.meta_repo.get_flux(irrad, level, pos)
        return fd["j"]

    def freeze_flux(self, ans):
        self.info("freeze flux")

        def ai_gen():
            for irrad, ais in groupby_key(ans, "irradiation"):
                for level, ais in groupby_key(ais, "level"):
                    p = self.get_level_path(irrad, level)
                    obj = dvc_load(p)
                    if isinstance(obj, list):
                        positions = obj
                    else:
                        positions = obj["positions"]

                    for repo, ais in groupby_repo(ais):
                        yield repo, irrad, level, {
                            ai.irradiation_position: positions[ai.irradiation_position]
                            for ai in ais
                        }

        added = []

        def func(x, prog, i, n):
            repo, irrad, level, d = x
            if prog:
                prog.change_message(
                    "Freezing Flux {}{} Repository={}".format(irrad, level, repo)
                )

            root = repository_path(repo, "flux", irrad)
            r_mkdir(root)

            p = os.path.join(root, level)
            if os.path.isfile(p):
                dd = dvc_load(p)
                dd.update(d)

            dvc_dump(d, p)
            added.append((repo, p))

        progress_loader(ai_gen(), func, threshold=1)

        self._commit_freeze(added, "<FLUX_FREEZE>")

    def freeze_production_ratios(self, ans):
        self.info("freeze production ratios")

        def ai_gen():
            for irrad, ais in groupby_key(ans, "irradiation"):
                for level, ais in groupby_key(ais, "level"):
                    pr = self.meta_repo.get_production(irrad, level)
                    for ai in ais:
                        yield pr, ai

        added = []

        def func(x, prog, i, n):
            pr, ai = x
            if prog:
                prog.change_message("Freezing Production {}".format(ai.runid))

            p = analysis_path(ai, ai.repository_identifier, "productions", mode="w")
            pr.dump(path=p)
            added.append((ai.repository_identifier, p))

        progress_loader(ai_gen(), func, threshold=1)
        self._commit_freeze(added, "<PR_FREEZE>")

    def rollback_to_collection(self, analyses, reponame):
        repo = self.get_repository(reponame)
        for analysis in analyses:
            repo_id = analysis.repository_identifier
            for mod, g in (
                ("intercepts", "<ISOEVO> default collection fits"),
                ("icfactors", "<ICFactor> default"),
                ("baselines", "<ISOEVO> default collection fits"),
                ("blanks", "<BLANKS> preceding"),
            ):
                sp = analysis_path(analysis, repo_id, modifier=mod)
                cs = repo.get_commits_from_log(greps=(g,), path=sp)
                print(sp, cs)
                if sp and cs:
                    repo.checkout(cs[-1].hexsha, "--", sp)

    def edit_comment(self, runid, repository_identifier, comment):
        self.debug(f"edit comment {runid} {repository_identifier} {comment}")
        path = analysis_path(runid, repository_identifier)
        obj = dvc_load(path)
        obj["comment"] = comment
        dvc_dump(obj, path)
        return path

    def manual_edit(self, runid, repository_identifier, values, errors, modifier):
        self.debug(
            "manual edit {} {} {}".format(runid, repository_identifier, modifier)
        )
        self.debug("values {}".format(values))
        self.debug("errors {}".format(errors))
        path = analysis_path(runid, repository_identifier, modifier=modifier)
        obj = dvc_load(path)

        for k, v in values.items():
            o = obj[k]
            o["manual_value"] = v
            o["use_manual_value"] = True
        for k, v in errors.items():
            o = obj[k]
            o["manual_error"] = v
            o["use_manual_error"] = True

        dvc_dump(obj, path)
        return path

    def revert_manual_edits(self, analysis, repository_identifier):
        ps = []
        for mod in ("intercepts", "blanks", "baselines", "icfactors"):
            path = analysis_path(analysis, repository_identifier, modifier=mod)
            with open(path, "r") as rfile:
                obj = json.load(rfile)
                for item in obj.values():
                    if isinstance(item, dict):
                        item["use_manual_value"] = False
                        item["use_manual_error"] = False
            ps.append(path)
            dvc_dump(obj, path)

        msg = "<MANUAL> reverted to non manually edited"
        self.commit_manual_edits(repository_identifier, ps, msg)

    def commit_manual_edits(self, repository_identifier, ps, msg):
        if self.repository_add_paths(repository_identifier, ps):
            self.repository_commit(repository_identifier, msg)

    def status_view(self, repo):
        repo = self._get_repository(repo, as_current=False)
        v = StatusView(status=repo.status())
        v.edit_traits()

    def add_bookmark(self, repo, name, message=None, hexsha=None):
        if not message:
            message = "No message provided"
        repo = self._get_repository(repo, as_current=False)
        repo.add_tag(name, message, hexsha)

    def update_analysis_paths(self, items, msg, author=None):
        """
        items is a list of (analysis, path) tuples
        :param items:
        :param msg:
        :return:
        """
        mod_repositories = []

        def key(x):
            return x[0].repository_identifier

        author = self.get_author(author)
        for expid, ais in groupby(sorted(items, key=key), key=key):
            ps = [p for _, p in ais]
            if self.repository_add_paths(expid, ps):
                self.repository_commit(expid, msg, author)
                mod_repositories.append(expid)

        return mod_repositories

    def update_analyses(self, ans, modifiers, msg, author=None):
        author = self.get_author(author)

        if not isinstance(modifiers, (list, tuple)):
            modifiers = (modifiers,)

        mod_repositories = []
        for expid, ais in groupby_repo(ans):
            ps = [
                analysis_path(x, x.repository_identifier, modifier=modifier)
                for x in ais
                for modifier in modifiers
            ]
            if self.repository_add_paths(expid, ps):
                if self.repository_commit(expid, msg, author):
                    mod_repositories.append(expid)
                else:
                    self.warning_dialog(
                        "There is an issue with your repository. {}. Please fix it before "
                        "trying to save any changes".format(expid)
                    )
        return mod_repositories

    def update_tag(self, an, add=True, **kw):
        tag = Tag.from_analysis(an, **kw)
        tag.dump()

        expid = an.repository_identifier
        if add:
            return self.repository_add_paths(expid, tag.path)
        else:
            return tag.path

    def delete_existing_icfactors(self, ai, dets):
        # remove all icfactors not in dets
        if dets:
            self.info("Delete existing icfactors for {}".format(ai))
            ai.delete_icfactors(dets)
            if self._cache:
                self._cache.remove(ai.uiid)

            self._update_current_age(ai)

    def save_icfactors(
        self,
        ai,
        dets,
        fits,
        refs,
        use_source_correction,
        standard_ratios,
        reference_data,
    ):
        if use_source_correction:
            ai.dump_source_correction_icfactors(refs)
        else:
            if fits and dets:
                self.info("Saving icfactors for {}".format(ai))
                ai.dump_icfactors(
                    dets,
                    fits,
                    refs,
                    reviewed=True,
                    standard_ratios=standard_ratios,
                    reference_data=reference_data,
                )

        if self._cache:
            self._cache.remove(ai.uiid)
        self._update_current_age(ai)

    def save_blanks(self, ai, keys, refs):
        if keys:
            self.info("Saving blanks for {}".format(ai))
            ai.dump_blanks(keys, refs, reviewed=True)
            if self._cache:
                self._cache.remove(ai.uiid)

            self._update_current_blanks(ai, keys)

    def save_defined_equilibration(self, ai, keys):
        if keys:
            self.info("Saving equilibration for {}".format(ai))
            if self._cache:
                self._cache.remove(ai.uiid)

            self._update_current(ai, keys)
            return ai.dump_equilibration(keys, reviewed=True)

    def save_fits(self, ai, keys):
        if keys:
            self.info("Saving fits for {}".format(ai))
            ai.dump_fits(keys, reviewed=True)
            if self._cache:
                self._cache.remove(ai.uiid)

            self._update_current(ai, keys)

    def save_flux(self, identifier, j, e):
        """
        user manually edit flux via the automated run factory
        :param identifier:
        :param j:
        :param e:
        :return:
        """
        self.meta_pull()

        with self.session_ctx(use_parent_session=False):
            irp = self.get_identifier(identifier)
            if irp:
                level = irp.level
                irradiation = level.irradiation
                self._save_j(
                    irradiation.name,
                    level.name,
                    irp.position,
                    identifier,
                    j,
                    e,
                    0,
                    0,
                    0,
                    None,
                    None,
                    None,
                    False,
                )

                self.meta_commit("User manual edited flux")
        self.meta_push()

    # def save_flux_position(self, flux_position, options, decay_constants, add=False, save_predicted=True):
    #     """
    #     save flux called from FluxPersistNode
    #
    #     :param flux_position:
    #     :param options:
    #     :param decay_constants:
    #     :param add:
    #     :return:
    #     """
    #
    #     irradiation = flux_position.irradiation
    #     level = flux_position.level
    #     pos = flux_position.hole_id
    #     identifier = flux_position.identifier
    #     j = flux_position.j
    #     e = flux_position.jerr
    #     mj = flux_position.mean_j
    #     me = flux_position.mean_jerr
    #     analyses = flux_position.analyses
    #     position_jerr = flux_position.position_jerr
    #
    #     # self._save_j(irradiation, level, pos, identifier, j, e, mj, me, position_jerr, decay_constants, analyses,
    #     #              options, add, save_predicted)
    #     self.info('Saving j for {}{}:{} {}, j={} +/-{}'.format(irradiation, level,
    #                                                            pos, identifier, j, e))
    #
    #     self.meta_repo.update_flux(irradiation, level, pos, identifier, j, e, mj, me,
    #                                decay=decay_constants,
    #                                analyses=analyses,
    #                                options=options, add=add,
    #                                position_jerr=position_jerr,
    #                                save_predicted=save_predicted)

    # if self.update_currents_enabled:
    #     ans, _ = self.db.get_labnumber_analyses([identifier])
    #     for ai in self.make_analyses(ans):
    #         self._update_current_age(ai)

    def save_csv_dataset(self, name, repository, lines, local_path=False):
        if local_path:
            p = add_extension(local_path, ".csv")
        else:
            repo = self.get_repository(repository)
            root = os.path.join(repo.path, "csv")
            p = os.path.join(root, add_extension(name, ".csv"))

            if repo.smart_pull(quiet=False):
                if not os.path.isdir(root):
                    os.mkdir(root)
            else:
                self.warning_dialog(
                    'Failed to update repository. Not saving CSV file "{}"'.format(p)
                )
                return

        self.debug("writing dataset to {}".format(p))
        exists = os.path.isfile(p)
        with open(p, "w") as wfile:
            wfile.writelines(lines)

        if not local_path:
            if repo.add_paths(p):
                repo.commit(
                    '<CSV> {} dataset "{}"'.format(
                        "Modified" if exists else "Added", name
                    )
                )

        return p

    def save_cosmogenic_correction(self, ai):
        ai.dump_cosmogenic()

    def remove_irradiation_position(self, irradiation, level, hole):
        db = self.db

        dbpos = db.get_irradiation_position(irradiation, level, hole)
        if dbpos:
            db.delete(dbpos)

        self.meta_repo.remove_irradiation_position(irradiation, level, hole)

    def find_interpreted_ages(self, identifiers, repositories):
        self.debug("find interpreted ages {}, {}".format(identifiers, repositories))
        ias = [
            InterpretedAgeRecordView(idn, path, dvc_load(path))
            for idn in identifiers
            for path in find_interpreted_age_path(idn, repositories)
        ]

        return ias

    def find_flux_monitors(self, irradiation, levels, sample, make_records=True):
        db = self.db
        with db.session_ctx():
            ans = db.get_flux_monitor_analyses(irradiation, levels, sample)
            for a in ans:
                a.bind()

            if make_records:
                ans = self.make_analyses(ans)
            return ans

    def find_references_by_load(self, load, atypes, make_records=True, **kw):
        records = self.db.find_references_by_load(load, atypes, **kw)
        if records:
            for r in records:
                r.bind()

            if make_records:
                records = self.make_analyses(records)
            return records

    def find_references(
        self, times, atypes, hours, exclude=None, make_records=True, **kw
    ):
        records = self.db.find_references(times, atypes, hours, exclude=exclude, **kw)

        if records:
            for r in records:
                r.bind()

            if make_records:
                records = self.make_analyses(records)
            return records

    def make_interpreted_ages(self, ias):
        self.debug("making interpreted ages {}".format(ias))
        if not isinstance(ias, (tuple, list)):
            ias = (ias,)

        def func(x, prog, i, n):
            if prog:
                prog.change_message("Making Interpreted age {}".format(x.name))

            obj = dvc_load(x.path)
            print("asdfasdf", x.path, obj)
            ia = DVCInterpretedAge()
            ia.repository_identifier = os.path.basename(
                os.path.dirname(os.path.dirname(os.path.dirname(x.path)))
            )
            ia.from_json(obj)

            try:
                ta = analysis_path(ia, ia.repository_identifier, modifier="tags")
                if ta is not None:
                    ia.load_tag(dvc_load(ta))
            except AnalysisNotAnvailableError:
                pass

            return ia

        return progress_loader(ias, func, step=25)

    def get_adjacent_analysis(self, uuid, ts, spectrometer, previous=True):
        an = self.db.get_adjacent_analysis(uuid, ts, spectrometer, previous)
        if an:
            return self.make_analysis(an)

    def get_analysis(self, uuid):
        an = self.db.get_analysis_uuid(uuid)
        if an:
            return self.make_analysis(an)

    def make_analysis(self, record, *args, **kw):
        a = self.make_analyses((record,), *args, **kw)
        if a:
            return a[0]

    def make_analyses(
        self,
        records,
        calculate_f_only=False,
        reload=False,
        quick=False,
        use_progress=True,
        pull_frequency=None,
        use_cached=True,
        sync_repo=True,
        use_flux_histories=True,
        warn=True,
    ):
        if not records:
            return []

        globalv.active_analyses = records

        # load repositories
        st = time.time()

        if self.use_cache and use_cached:
            cached_records = []
            nrecords = []
            cache = self._cache

            # get items from the cache
            for ri in records:
                r = cache.get(ri.uuid)
                if r is not None:
                    cached_records.append(r)
                else:
                    nrecords.append(ri)

            records = nrecords

        def func(xi, prog, i, n):
            if prog:
                prog.change_message("Syncing repository= {}".format(xi))
            try:
                self.sync_repo(xi, use_progress=False, pull_frequency=pull_frequency)
            except BaseException as e:
                print("sync repo", e)
                pass

        bad_records = [r for r in records if r.repository_identifier is None]
        if bad_records:
            if warn:
                self.warning_dialog(
                    "Missing Repository Associations. Contact an expert!"
                    'Cannot load analyses "{}"'.format(
                        ",".join([r.record_id for r in bad_records])
                    )
                )
            records = [r for r in records if r.repository_identifier is not None]

        if not records:
            if self.use_cache and use_cached:
                cache.clean()
                return cached_records
            else:
                return []

        exps = {r.repository_identifier for r in records}

        if sync_repo:
            if use_progress:
                progress_iterator(exps, func, threshold=1)
            else:
                for ei in exps:
                    self.sync_repo(ei, use_progress=False)
        try:
            branches = {ei: get_repository_branch(repository_path(ei)) for ei in exps}
        except NoSuchPathError as e:
            print("e", e)
            return []

        flux_histories = {}
        fluxes = {}
        productions = {}
        chronos = {}
        sens = {}
        frozen_fluxes = {}
        frozen_productions = {}
        sample_prep = {}
        meta_repo = self.meta_repo
        use_cocktail_irradiation = self.use_cocktail_irradiation
        if not quick:
            for exp in exps:
                ps = get_frozen_productions(exp)
                frozen_productions.update(ps)

            for r in records:
                # get sample notes

                # dbsam = r.irradiation_position.sample
                # sample_id = dbsam.id
                # if sample_id not in sample_prep:
                #     sample_prep[sample_id] = ','.join([p.comment or '' for p in dbsam.preps])

                irrad = r.irradiation
                if irrad != "NoIrradiation":
                    if irrad not in frozen_fluxes:
                        frozen_fluxes[irrad] = get_frozen_flux(
                            r.repository_identifier, r.irradiation
                        )

                    level = r.irradiation_level
                    if irrad in fluxes:
                        flux_levels = fluxes[irrad]
                        prod_levels = productions[irrad]
                    else:
                        flux_levels = {}
                        prod_levels = {}

                    if level not in flux_levels:
                        flux_levels[level] = meta_repo.get_flux_positions(irrad, level)
                        prod_levels[level] = meta_repo.get_production(irrad, level)

                    if irrad not in chronos:
                        chronos[irrad] = meta_repo.get_chronology(irrad)

                    if irrad not in fluxes:
                        fluxes[irrad] = flux_levels
                        productions[irrad] = prod_levels

                    if use_flux_histories:
                        key = "{}{}".format(irrad, level)
                        if key not in flux_histories:
                            c = meta_repo.get_flux_history(irrad, level, max_count=1)
                            v = None
                            if c:
                                c = c[0]
                                v = "{} ({})".format(
                                    c.date.strftime(DATE_FORMAT), c.author
                                )
                            flux_histories[key] = v

                if (
                    use_cocktail_irradiation
                    and r.analysis_type == "cocktail"
                    and "cocktail" not in chronos
                ):
                    cirr = meta_repo.get_cocktail_irradiation()
                    chronos["cocktail"] = cirr.get("chronology")
                    fluxes["cocktail"] = cirr.get("flux")

            sens = meta_repo.get_sensitivities()

        def func(*args):
            try:
                return self._make_record(
                    branches=branches,
                    chronos=chronos,
                    productions=productions,
                    fluxes=fluxes,
                    calculate_f_only=calculate_f_only,
                    sens=sens,
                    frozen_fluxes=frozen_fluxes,
                    frozen_productions=frozen_productions,
                    flux_histories=flux_histories,
                    sample_prep=sample_prep,
                    quick=quick,
                    reload=reload,
                    warn=warn,
                    *args,
                )
            except BaseException:
                record = args[0]
                self.warning(
                    "make analysis exception: repo={}, record_id={}".format(
                        record.repository_identifier, record.record_id
                    )
                )
                self.debug_exception()

        if use_progress:
            ret = progress_loader(records, func, threshold=1, step=25)
        else:
            ret = [func(r, None, 0, 0) for r in records]

        et = time.time() - st

        n = len(ret)
        if n:
            self.debug(
                "Make analysis time, total: {}, n: {}, average: {}".format(
                    et, n, et / float(n)
                )
            )

        nn = len(records)
        if len(records) != n:
            if warn and not self.confirmation_dialog(
                "Failed making {} of {} analyses. "
                "Are you sure you want to continue?".format(nn - n, nn)
            ):
                return

        if self.use_cache:
            cache.clean()
            ret = cached_records + ret

        return ret

    # repositories
    def find_changes(self, names, remote, branch):
        gs = self.application.get_services(IGitHost)
        for gi in gs:
            gi.new_session()

        def func(item, prog, i, n):
            name = item.name
            if prog:
                prog.change_message("Examining: {}({}/{})".format(name, i, n))
            self.debug("examining {}".format(name))

            r = Repo(repository_path(name))
            if branch in [b.name for b in r.branches]:
                try:
                    lc = r.commit(branch).hexsha
                except BaseException as e:
                    self.warning("skipping {}. {}".format(name, e))
                    return

                for gi in gs:
                    outdated, sha = gi.up_to_date(self.organization, name, lc, branch)
                    if outdated:
                        try:
                            fsha = r.commit("FETCH_HEAD").hexsha
                        except BaseException:
                            fsha = None

                        try:
                            if fsha != sha:
                                self.debug("fetching {}".format(name))
                                r.git.fetch()

                            item.dirty = True
                            item.update(fetch=False)
                        except GitCommandError as e:
                            self.warning("error examining {}. {}".format(name, e))
                    else:
                        item.update(fetch=False)

        progress_loader(names, func, threshold=1)
        for gi in gs:
            gi.close_session()

    def repository_add_paths(self, repository_identifier, paths):
        repo = self._get_repository(repository_identifier)
        return repo.add_paths(paths)

    def get_author(self, author=None):
        if not self.use_default_commit_author:
            if self._author:
                author = self._author
            elif author is None:
                db = self.db
                with db.session_ctx():
                    authors = [User(r) for r in db.get_users()]

                    g = GitCommitAuthorView(authors=authors)

                    info = g.edit_traits()
                    if info.result:
                        author = Actor(g.author, g.email)
                        if not self.db.get_user(g.author):
                            self.db.add_user(g.author, email=g.email)

                        if g.remember_choice:
                            self._author = author
        return author

    def repository_commit(self, repository, msg, author=None):
        self.debug("Repository commit: {} msg: {}".format(repository, msg))
        repo = self._get_repository(repository)
        author = self.get_author(author)
        return repo.commit(msg, author=author)

    def remote_repositories(self):
        rs = []
        gs = self.application.get_services(IGitHost)
        if gs:
            for gi in gs:
                ri = gi.get_repos(self.organization)
                rs.extend(ri)
        else:
            self.warning_dialog(HOST_WARNING_MESSAGE)
        return rs

    def remote_repository_names(self):
        rs = []
        gs = self.application.get_services(IGitHost)
        if gs:
            for gi in gs:
                self.debug("load repositories from {}".format(self.organization))
                ri = gi.get_repository_names(self.organization)
                rs.extend(ri)
        else:
            self.warning_dialog(HOST_WARNING_MESSAGE)
        return rs

    def check_githost_connection(self):
        git_service = self.application.get_service(IGitHost)
        return git_service.test_connection(self.organization)

    def make_url(self, name, **kw):
        git_service = self.application.get_service(IGitHost)
        return git_service.make_url(name, self.organization, **kw)

    def git_session_ctx(self, repository_identifier, message):
        return GitSessionCTX(self, repository_identifier, message)

    def clear_pull_cache(self):
        self._pull_cache = {}

    def sync_repo(self, name, use_progress=True, pull_frequency=None):
        """
        pull or clone an repo

        """
        root = repository_path(name)
        exists = os.path.isdir(os.path.join(root, ".git"))
        self.debug(
            "sync repository {}. exists={} pull_frequency={}".format(
                name, exists, pull_frequency
            )
        )

        if exists:
            if pull_frequency:
                now = datetime.now()
                last_pull = self._pull_cache.get(name)
                self._pull_cache[name] = now
                args = (
                    last_pull,
                    (datetime.now() - last_pull).seconds,
                    (datetime.now() - last_pull).seconds < pull_frequency,
                )

                self.debug(" ".join([str(a) for a in args]))

                if last_pull and (datetime.now() - last_pull).seconds < pull_frequency:
                    return True

            repo = self._get_repository(name)
            repo.pull(use_progress=use_progress, use_auto_pull=self.use_auto_pull)

            self._merge_data_collection(repo)

            return True
        else:
            self.debug("getting repository from remote")

            service = self.git_service
            if not service:
                service = self.application.get_service(IGitHost)

            if not service:
                return True
            else:
                if isinstance(service, LocalGitHostService):
                    service.create_empty_repo(name)

                    return True
                elif service.clone_from(name, root, self.organization):
                    repo = self._get_repository(name)
                    self._merge_data_collection(repo)
                    # repo.merge("origin/data_collection", inform=False)

                    return True
                else:
                    self.warning_dialog(
                        "name={} not in available repos "
                        "from service={}, organization={}".format(
                            name, service.remote_url, self.organization
                        )
                    )
                    names = self.remote_repository_names()
                    for ni in names:
                        self.debug("available repo== {}".format(ni))

                # names = self.remote_repository_names()
                # if name in names:
                #     service.clone_from(name, root, self.organization)
                #     return True

    def _merge_data_collection(self, repo):
        # merge any new commits on the data_collection branch to this branch
        # get all branches like data_collection
        # branches = repo.active_repo.git.branch('-a').split('\n')
        # branches = [b.strip() for b in branches]
        # branches = [b for b in branches if 'data_collection' in b]
        branches = ["origin/data_collection"]
        for b in branches:
            if b.startswith("remotes"):
                b = b.replace("remotes/", "")

            try:
                # repo.active_repo.git.checkout('origin/data_collection', '.')
                # repo.active_repo.git.add('.')
                # repo.active_repo.git.commit('-m', 'Merge origin/data_collection branch')
                # repo.merge("origin/data_collection", inform=False)
                # if repo.name == 'Henry<GitRepo>' and b == 'origin/data_collection':
                #     continue
                repo.merge(b, inform=False)

            except BaseException:
                self.debug_exception()
                self.debug(
                    f"merge with {b} failed. This is not an issue if you are only using local "
                    "repos"
                )

    def rollback_repository(self, expid):
        repo = self._get_repository(expid)

        cpaths = repo.get_local_changes()
        # cover changed paths to a list of analyses

        # select paths to revert
        rpaths = (".",)
        repo.cmd("checkout", "--", " ".join(rpaths))
        for p in rpaths:
            self.debug("revert changes for {}".format(p))

        head = repo.get_head(hexsha=False)
        msg = (
            "Changes to {} reverted to Commit: {}\n"
            "Date: {}\n"
            "Message: {}".format(
                expid, head.hexsha[:10], format_date(head.committed_date), head.message
            )
        )
        self.information_dialog(msg)

    def pull_repository(self, repo):
        repo = self._get_repository(repo)
        self.debug("pull repository {}".format(repo))
        for gi in self.application.get_services(IGitHost):
            self.debug(
                "pull to remote={}, url={}".format(
                    gi.default_remote_name, gi.remote_url
                )
            )
            repo.smart_pull(remote=gi.default_remote_name)

    def push_repository(self, repo, **kw):
        repo = self._get_repository(repo)
        self.debug("push repository {}".format(repo))
        for gi in self.application.get_services(IGitHost):
            self.debug(
                "pushing to remote={}, url={}".format(
                    gi.default_remote_name, gi.remote_url
                )
            )
            repo.push(remote=gi.default_remote_name, **kw)

    def push_repositories(self, changes):
        if self.use_auto_push or self.confirmation_dialog(
            "Would you like to push (share) your changes?"
        ):
            for gi in self.application.get_services(IGitHost):
                push_repositories(changes, gi, quiet=False)

    def delete_local_commits(self, repo, **kw):
        r = self._get_repository(repo)
        r.delete_local_commits(**kw)

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

    def set_identifier(self, irradiation, level, position, identifier):
        dbpos = self.db.get_irradiation_position(irradiation, level, position)
        if dbpos:
            dbpos.identifier = identifier
            self.db.commit()

        self.meta_repo.set_identifier(irradiation, level, position, identifier)

    def add_production_to_irradiation(self, irrad, reactor, params, msg=None):
        self.meta_repo.add_production_to_irradiation(irrad, reactor, params)

        if msg is None:
            msg = "updated default production. {}".format(reactor)

        self.meta_commit(msg)

    def update_chronology(self, name, doses):
        self.meta_repo.update_chronology(name, doses)
        self.meta_commit("updated chronology for {}".format(name))

    def meta_pull(self, **kw):
        return self.meta_repo.smart_pull(**kw)

    def meta_push(self, *args, **kw):
        self.meta_repo.push(*args, **kw)

    def meta_add_all(self):
        self.meta_repo.add_unstaged(paths.meta_root, add_all=True)

    def meta_commit(self, msg):
        changes = self.meta_repo.has_staged()
        if changes:
            self.debug("meta repo has changes: {}".format(changes))
            self.meta_repo.report_local_changes()
            self.meta_repo.commit(msg)
            self.meta_repo.clear_cache = True
        else:
            self.debug("no changes to meta repo")

    def add_production(self, irrad, name, prod):
        self.meta_repo.add_production_to_irradiation(irrad, name, prod)

    def get_production(self, irrad, name):
        return self.meta_repo.get_production(irrad, name)

    # get
    def get_csv_datasets(self, repo):
        repo = self.get_repository(repo)
        return list_directory(
            os.path.join(repo.path, "csv"), extension=".csv", remove_extension=True
        )

    def get_local_repositories(self):
        return list_subdirectories(paths.repository_dataset_dir)

    def get_repository(self, exp):
        return self._get_repository(exp)

    def get_version(self):
        bd = str(self.application.preferences.get("pychron.update.build_repo"))
        self.debug("get version {}".format(bd))
        if os.path.isdir(bd):
            repo = Repo(bd)
            return repo.head.commit.hexsha

    def get_meta_head(self):
        return self.meta_repo.get_head()

    def get_irradiation_geometry(self, irrad, level):
        dblevel = self.db.get_irradiation_level(irrad, level)

        return (
            self.meta_repo.get_irradiation_holder_holes(dblevel.holder),
            dblevel.holder,
        )

    def get_irradiation_names(self):
        irrads = self.db.get_irradiations()
        return [i.name for i in irrads]

    def get_irradiations(self, *args, **kw):
        sort_name_key = self.irradiation_prefix
        return self.db.get_irradiations(sort_name_key=sort_name_key, *args, **kw)

    # add
    def add_interpreted_ages(self, rid, iass):
        ps = []
        ialabels = []
        for ia in iass:
            d = make_interpreted_age_dict(ia)
            rid, p = self._add_interpreted_age(ia, d)
            ps.append(p)
            ialabels.append("{} {} {}".format(ia.name, ia.identifier, ia.sample))

        if self.repository_add_paths(rid, ps):
            sparrow = self.application.get_service(
                "pychron.sparrow.sparrow_client.SparrowClient"
            )
            if sparrow and self.confirmation_dialog("Add to Sparrow?"):
                if sparrow.login():
                    for p in ps:
                        sparrow.insert_ia(p)

                    self.information_dialog("IA files successfully added")
                else:
                    self.warning("Connection failed. Cannot add IAs to Sparrow")

            self.repository_commit(
                rid, "<IA> added interpreted ages {}".format(",".join(ialabels))
            )
            return True

    def add_interpreted_age(self, ia):
        d = make_interpreted_age_dict(ia)
        rid, p = self._add_interpreted_age(ia, d)
        if self.repository_add_paths(rid, p):
            self.repository_commit(
                rid,
                "<IA> added interpreted age "
                "{} identifier={} sample={}".format(ia.name, ia.identifier, ia.sample),
            )

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
                    src = analysis_path(runspec, src_expid, modifier=m)
                    dest = analysis_path(runspec, expid, modifier=m, mode="w")

                    shutil.copyfile(src, dest)
                    repo.add(dest, commit=False)
                repo.commit("added repository association")
        else:
            self.warning(
                "{} not in the database {}".format(runspec.runid, self.db.name)
            )

    def add_material(self, name, grainsize=None):
        db = self.db
        mat = db.get_material(name, grainsize)
        if not mat:
            mat = db.add_material(name, grainsize)

        return mat

    def add_project(self, name, principal_investigator=None, **kw):
        added = False
        db = self.db
        if not db.get_project(name, principal_investigator):
            added = True
            db.add_project(name, principal_investigator, **kw)
        return added

    def add_sample(self, name, project, pi, material, grainsize=None, note=None, **kw):
        db = self.db
        sam = db.get_sample(name, project, pi, material, grainsize)
        if not sam:
            sam = db.add_sample(name, project, pi, material, grainsize, note=note, **kw)
        return sam

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
            self.db.add_irradiation_level(
                name, irradiation, holder, production_name, **kw
            )

        self.meta_repo.add_level(irradiation, name)
        self.meta_repo.update_level_production(irradiation, name, production_name)
        return added

    def clone_repository(self, identifier, url=None):
        root = repository_path(identifier)
        if not os.path.isdir(root):
            self.debug("cloning {}".format(root))
            if not url:
                url = self.make_url(identifier)
            Repo.clone_from(url, root)
        else:
            self.debug("{} already exists".format(identifier))

    def check_remote_repository_exists(self, name):
        gs = self.application.get_services(IGitHost)
        if gs:
            for gi in gs:
                if gi.remote_exists(self.organization, name):
                    return True
        else:
            self.warning_dialog(HOST_WARNING_MESSAGE)

    def add_readme(self, identifier, content=""):
        self.debug("adding readme to repository identifier={}".format(identifier))
        root = repository_path(identifier)
        if os.path.isdir(root):
            p = os.path.join(root, "README.md")
            if not os.path.isfile(p):
                with open(p, "w") as wfile:
                    wfile.write("{}\n###############\n{}".format(identifier, content))
                repo = self._get_repository(identifier, as_current=False)
                repo.add(p)
                repo.commit("initial commit")
                repo.push()
            else:
                self.debug("readme already exists")
        else:
            self.critical("Repository does not exist {}. {}".format(identifier, root))

    def branch_repo(self, repo, branch):
        repo = self._get_repository(repo)
        repo.create_branch(branch, inform=False)

    def add_repository(
        self,
        identifier,
        principal_investigator,
        inform=True,
        license_template=None,
        private=True,
    ):
        self.debug(
            "trying to add repository identifier={}, pi={}".format(
                identifier, principal_investigator
            )
        )

        root = repository_path(identifier)
        if os.path.isdir(root):
            self.db.add_repository(identifier, principal_investigator)
            self.debug("already a directory {}".format(identifier))
            if inform:
                self.warning_dialog("{} already exists.".format(root))
            return True

        # names = self.remote_repository_names(ide)
        # if identifier in names:
        if self.check_remote_repository_exists(identifier):
            # make sure also in the database
            self.db.add_repository(identifier, principal_investigator)

            if inform:
                self.warning_dialog('Repository "{}" already exists'.format(identifier))
            return True

        else:
            if os.path.isdir(root):
                self.db.add_repository(identifier, principal_investigator)
                if inform:
                    self.warning_dialog("{} already exists.".format(root))
            else:
                self.db.add_repository(identifier, principal_investigator)
                ret = True
                gs = self.application.get_services(IGitHost)
                if gs:
                    ret = False
                    for i, gi in enumerate(gs):
                        self.info(
                            "Creating repository at {}. {}".format(gi.name, identifier)
                        )

                        if gi.create_repo(
                            identifier,
                            organization=self.organization,
                            license_template=license_template,
                            private=private,
                        ):
                            ret = True
                            if isinstance(gi, LocalGitHostService):
                                if i == 0:
                                    self.db.add_repository(
                                        identifier, principal_investigator
                                    )
                            else:
                                if self.default_team:
                                    gi.set_team(
                                        self.default_team,
                                        self.organization,
                                        identifier,
                                        permission="push",
                                    )

                                url = gi.make_url(identifier, self.organization)
                                if i == 0:
                                    try:
                                        repo = Repo.clone_from(url, root)
                                    except BaseException as e:
                                        self.debug("failed cloning repo. {}".format(e))
                                        ret = False

                                    self.db.add_repository(
                                        identifier, principal_investigator
                                    )
                                else:
                                    repo.create_remote(
                                        gi.default_remote_name or "origin", url
                                    )

                return ret

    def add_irradiation(self, name, doses=None, verbose=True):
        if self.db.get_irradiation(name):
            if verbose:
                self.warning("irradiation {} already exists".format(name))
            return

        self.db.add_irradiation(name)

        self.meta_repo.add_irradiation(name)
        self.meta_repo.add_chronology(name, doses)

        root = os.path.join(paths.meta_root, name)
        p = os.path.join(root, "productions")
        if not os.path.isdir(p):
            os.mkdir(p)

        p = os.path.join(root, "productions.json")
        with open(p, "w") as wfile:
            json.dump({}, wfile)
        self.meta_repo.add(p, commit=False)

        return True

    def add_load_holder(self, name, path_or_txt):
        self.db.add_load_holder(name)
        self.meta_repo.add_load_holder(name, path_or_txt)

    def copy_production(self, pr):
        """

        @param pr: irrad_ProductionTable object
        @return:
        """
        pname = pr.name.replace(" ", "_")
        path = os.path.join(paths.meta_root, "productions", "{}.json".format(pname))
        if not os.path.isfile(path):
            obj = {}
            for attr in INTERFERENCE_KEYS + RATIO_KEYS:
                obj[attr] = [getattr(pr, attr), getattr(pr, "{}_err".format(attr))]
            dvc_dump(obj, path)

    # def save_tag_subgroup_items(self, items):
    #
    #     for expid, ans in groupby_repo(items):
    #         self.sync_repo(expid)
    #         ps = []
    #         for it in ans:
    #             tag = Tag.from_analysis(it)
    #             tag.dump()
    #
    #             ps.append(tag.path)
    #
    #         if self.repository_add_paths(expid, ps):
    #             self._commit_tags(ans, expid, '<SUBGROUP>', refresh=False)

    def tag_items(self, tag, items, note=""):
        self.debug('tag items with "{}"'.format(tag))

        with self.db.session_ctx() as sess:
            for expid, ans in groupby_repo(items):
                if USE_GIT_TAGGING:
                    self.sync_repo(expid)

                cs = []
                ps = []
                for it in ans:
                    if not isinstance(it, (InterpretedAge, DVCAnalysis)):
                        oit = self.make_analysis(it, quick=True)
                        if oit is None:
                            self.warning(
                                "Failed preparing analysis. Cannot tag: {}".format(it)
                            )
                        it = oit

                    if it:
                        self.debug("setting {} tag= {}".format(it.record_id, tag))
                        if not isinstance(it, InterpretedAge):
                            self.set_analysis_tag(it, tag)

                        it.set_tag({"name": tag, "note": note or ""})

                        if USE_GIT_TAGGING:
                            path = self.update_tag(it, add=False)
                            ps.append(path)
                            cs.append(it)

                sess.commit()
                if USE_GIT_TAGGING and ps:
                    if self.repository_add_paths(expid, ps):
                        self._commit_tags(cs, expid, "<TAG> {:<6s}".format(tag))

    def get_repository(self, repo):
        return self._get_repository(repo, as_current=False)

    def clear_cache(self):
        if self.use_cache:
            self._cache.clear()

    # private
    def _update_current_blanks(
        self, ai, keys=None, dban=None, force=False, update_age=True, commit=True
    ):
        if self.update_currents_enabled:
            db = self.db
            if dban is None:
                dban = db.get_analysis_uuid(ai.uuid)
            if keys is None:
                keys = ai.isotope_keys

            if dban:
                for k in keys:
                    iso = ai.get_isotope(k)
                    if iso:
                        iso = iso.blank
                        db.update_current(
                            dban,
                            "{}_blank".format(k),
                            iso.value,
                            iso.error,
                            iso.units,
                            force=force,
                        )
                if update_age:
                    self._update_current_age(ai, dban, force=force)
                if commit:
                    db.commit()
            else:
                self.warning(
                    "Failed to update current values. "
                    "Could not located RunID={}, UUID={}".format(ai.runid, ai.uuid)
                )

    def _update_current_age(self, ai, dban=None, force=False):
        if self.update_currents_enabled:
            if dban is None:
                db = self.db
                dban = db.get_analysis_uuid(ai.uuid)

            if dban:
                age_units = ai.arar_constants.age_units
                self.db.update_current(
                    dban, "age", ai.age, ai.age_err, age_units, force=force
                )
                self.db.update_current(
                    dban,
                    "age_wo_j_error",
                    ai.age,
                    ai.age_err_wo_j,
                    age_units,
                    force=force,
                )

    def _update_current(
        self, ai, keys=None, dban=None, force=False, update_age=True, commit=True
    ):
        if self.update_currents_enabled:
            db = self.db
            if dban is None:
                dban = db.get_analysis_uuid(ai.uuid)

            if dban:
                if keys is None:
                    keys = ai.isotope_keys
                    keys += [iso.detector for iso in ai.iter_isotopes()]

                for k in keys:
                    iso = ai.get_isotope(k)
                    if iso is None:
                        iso = ai.get_isotope(detector=k)
                        bs = iso.baseline
                        db.update_current(
                            dban,
                            "{}_baseline".format(k),
                            bs.value,
                            bs.error,
                            bs.units,
                            force=force,
                        )
                        db.update_current(
                            dban,
                            "{}_baseline_n".format(k),
                            bs.n,
                            None,
                            "int",
                            force=force,
                        )
                    else:
                        db.update_current(
                            dban, "{}_n".format(k), iso.n, None, "int", force=force
                        )
                        db.update_current(
                            dban,
                            "{}_intercept".format(k),
                            iso.value,
                            iso.error,
                            iso.units,
                            force=force,
                        )

                        v = iso.get_ic_corrected_value()
                        db.update_current(
                            dban,
                            "{}_ic_corrected".format(k),
                            nominal_value(v),
                            std_dev(v),
                            iso.units,
                            force=force,
                        )

                        v = iso.get_baseline_corrected_value()
                        db.update_current(
                            dban,
                            "{}_bs_corrected".format(k),
                            nominal_value(v),
                            std_dev(v),
                            iso.units,
                            force=force,
                        )

                        v = iso.get_non_detector_corrected_value()
                        db.update_current(
                            dban,
                            k,
                            nominal_value(v),
                            std_dev(v),
                            iso.units,
                            force=force,
                        )
                if update_age:
                    self._update_current_age(ai, dban, force=force)
                if commit:
                    db.commit()
            else:
                self.warning(
                    "Failed to update current values. "
                    "Could not located RunID={}, UUID={}".format(ai.runid, ai.uuid)
                )

    def _transfer_analysis_to(self, dest, src, rid):
        p = analysis_path(rid, src)
        np = analysis_path(rid, dest)

        obj = dvc_load(p)
        obj["repository_identifier"] = dest
        dvc_dump(obj, p)

        ops = [p]
        nps = [np]

        shutil.move(p, np)

        for modifier in PATH_MODIFIERS:
            if modifier:
                p = analysis_path(rid, src, modifier=modifier)
                np = analysis_path(rid, dest, modifier=modifier)
                shutil.move(p, np)
                ops.append(p)
                nps.append(np)

        return ops, nps

    def _commit_freeze(self, added, msg):
        for repo, ps in groupby_key(added, key=itemgetter(0)):
            rm = GitRepoManager()
            rm.open_repo(repo, paths.repository_dataset_dir)
            rm.add_paths(ps)
            rm.smart_pull()
            rm.commit(msg)

    def _commit_tags(self, cs, expid, msg, refresh=True):
        if cs:
            cc = [c.record_id for c in cs]
            if len(cc) > 1:
                cstr = "{} - {}".format(cc[0], cc[-1])
            else:
                cstr = cc[0]

            self.repository_commit(expid, "{} {}".format(msg, cstr))
            if refresh:
                for ci in cs:
                    ci.refresh_view()

    # def _save_j(self, irradiation, level, pos, identifier, j, e, mj, me, position_jerr, decay_constants, analyses,
    #             options, add, save_predicted):

    def _add_interpreted_age(self, ia, d):
        rid = ia.repository_identifier

        ia_path_name = ia.identifier.replace(":", "_")

        i = 0
        while 1:
            p = analysis_path(
                "{}_{:05d}".format(ia_path_name, i), rid, modifier="ia", mode="w"
            )
            i += 1
            if not os.path.isfile(p):
                break

        self.debug("saving interpreted age. {}".format(p))
        dvc_dump(d, p)
        return rid, p

    def _load_repository(self, expid, prog, i, n):
        if prog:
            prog.change_message("Loading repository {}. {}/{}".format(expid, i, n))
        self.sync_repo(expid)

    def _make_record(
        self,
        record,
        prog,
        i,
        n,
        productions=None,
        chronos=None,
        branches=None,
        fluxes=None,
        sens=None,
        frozen_fluxes=None,
        frozen_productions=None,
        flux_histories=None,
        sample_prep=None,
        calculate_f_only=False,
        reload=False,
        quick=False,
        warn=True,
    ):
        meta_repo = self.meta_repo
        if prog:
            # this accounts for ~85% of the time!!!
            prog.change_message(
                "Loading analysis {}. {}/{}".format(record.record_id, i, n)
            )

        expid = record.repository_identifier
        if not expid:
            exps = record.repository_ids
            self.debug(
                "Analysis {} is associated multiple repositories "
                "{}".format(record.record_id, ",".join(exps))
            )
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

        if isinstance(record, DVCAnalysis) and not reload:
            a = record
        else:
            if isinstance(record, DVCAnalysis):
                record = self.db.get_analysis_uuid(record.uuid)

            # self.debug('use_repo_suffix={} record_id={}'.format(record.use_repository_suffix, record.record_id))
            rid = record.record_id
            uuid = record.uuid

            try:
                a = DVCAnalysis(uuid, rid, expid)
            except AnalysisNotAnvailableError:
                self.debug("uuid={}, rid={}, expid={}".format(uuid, rid, expid))
                if warn:
                    self.warning_dialog(
                        "Analysis {} not in local repository {}. "
                        "You may need to pull changes. If local repository is up to date you may "
                        "need to push changes from the data collection computer".format(
                            rid, expid
                        )
                    )
                return

            a.group_id = record.group_id
            a.set_tag(record.tag)

            if sample_prep:
                a.sample_prep_comment = sample_prep.get(
                    record.irradiation_position.sample.id
                )
            try:
                a.sample_note = record.irradiation_position.sample.note or ""
            except AttributeError as e:
                self.debug("unable to set sample note. Error={}".format(e))

            if not quick:
                a.load_name = record.load_name
                a.load_holder = record.load_holder
                # get repository branch
                a.branch = branches.get(expid, "")

                # load sample_prep

                # load irradiation
                if sens:
                    sens = sens.get(a.mass_spectrometer.lower(), [])
                    a.set_sensitivity(sens)

                if a.analysis_type == "cocktail" and "cocktail" in chronos:
                    a.set_chronology(chronos["cocktail"])
                    a.j = fluxes["cocktail"]

                elif a.irradiation:  # and a.irradiation not in ('NoIrradiation',):
                    if chronos:
                        chronology = chronos.get(a.irradiation, None)
                    else:
                        chronology = meta_repo.get_chronology(a.irradiation)

                    if chronology:
                        a.set_chronology(chronology)

                    pname, prod = None, None

                    if frozen_productions:
                        try:
                            prod = frozen_productions[
                                "{}.{}".format(a.irradiation, a.irradiation_level)
                            ]
                            pname = prod.name
                        except KeyError:
                            pass

                    if not prod:
                        if a.irradiation != "NoIrradiation":
                            try:
                                pname, prod = productions[a.irradiation][
                                    a.irradiation_level
                                ]
                            except KeyError:
                                pname, prod = meta_repo.get_production(
                                    a.irradiation, a.irradiation_level
                                )
                                self.warning(
                                    "production key error name={} "
                                    "irrad={}, level={}, productions={}".format(
                                        pname,
                                        a.irradiation,
                                        a.irradiation_level,
                                        productions,
                                    )
                                )
                    if prod is not None:
                        a.set_production(pname, prod)

                    fd = None
                    if frozen_fluxes:
                        try:
                            fd = frozen_fluxes[a.irradiation][a.identifier]
                        except KeyError:
                            pass

                    if not fd:
                        if fluxes:
                            try:
                                level_flux = fluxes[a.irradiation][a.irradiation_level]
                                fd = meta_repo.get_flux_from_positions(
                                    a.irradiation_position, level_flux
                                )
                            except KeyError:
                                fd = {"j": ufloat(0, 0)}
                        else:
                            fd = meta_repo.get_flux(
                                a.irradiation,
                                a.irradiation_level,
                                a.irradiation_position_position,
                            )

                    if flux_histories:
                        a.flux_history = flux_histories.get(
                            "{}{}".format(a.irradiation, a.irradiation_level), ""
                        )

                    a.j = fd.get("j", ufloat(0, 0))
                    a.position_jerr = fd.get("position_jerr", 0)

                    j_options = fd.get("options")
                    if j_options:
                        a.model_j_kind = fd.get("model_kind")

                    lk = fd.get("lambda_k")
                    if lk:
                        a.arar_constants.lambda_k = lk

                    for attr in ("age", "name", "material", "reference"):
                        skey = "monitor_{}".format(attr)
                        try:
                            setattr(a, skey, fd[skey])
                        except KeyError as e:
                            try:
                                key = "standard_{}".format(attr)
                                setattr(a, skey, fd[key])
                            except KeyError:
                                pass

                if calculate_f_only:
                    a.calculate_f()
                else:
                    a.calculate_age()

        if self._cache:
            self._cache.update(record.uuid, a)
        return a

    def _get_repository(self, repository_identifier, as_current=True):
        if isinstance(repository_identifier, GitRepoManager):
            repo = repository_identifier
        else:
            repo = None
            if as_current:
                repo = self.current_repository
            path = repository_path(repository_identifier)

            if repo is None or repo.path != path:
                self.debug("make new repomanager for {}".format(path))
                repo = GitRepoManager()
                repo.path = path
                repo.open_repo(path)

        if as_current:
            self.current_repository = repo

        return repo

    def _bind_preferences(self):
        prefid = "pychron.dvc.connection"
        bind_preference(self, "favorites", "{}.favorites".format(prefid))
        self._favorites_changed(self.favorites)
        self._set_meta_repo_name()
        self._repository_root_changed()

        prefid = "pychron.dvc"
        bind_preference(
            self,
            "use_cocktail_irradiation",
            "{}.use_cocktail_irradiation".format(prefid),
        )
        bind_preference(self, "use_cache", "{}.use_cache".format(prefid))
        bind_preference(self, "max_cache_size", "{}.max_cache_size".format(prefid))
        bind_preference(
            self, "update_currents_enabled", "{}.update_currents_enabled".format(prefid)
        )
        bind_preference(self, "use_auto_pull", "{}.use_auto_pull".format(prefid))
        bind_preference(self, "use_auto_push", "{}.use_auto_push".format(prefid))
        bind_preference(
            self,
            "use_default_commit_author",
            "{}.use_default_commit_author".format(prefid),
        )

        prefid = "pychron.entry"
        bind_preference(
            self, "irradiation_prefix", "{}.irradiation_prefix".format(prefid)
        )

        bind_preference(
            self,
            "irradiation_project_prefix",
            "{}.irradiation_project_prefix".format(prefid),
        )
        if self.use_cache:
            self._use_cache_changed()

    def _max_cache_size_changed(self, new):
        if new:
            if self._cache:
                self._cache.max_size = self.max_cache_size
            else:
                self._use_cache_changed()
        else:
            self.use_cache = False

    def _use_cache_changed(self):
        if self.use_cache:
            self._cache = DVCCache(max_size=self.max_cache_size)
        else:
            self._cache = None

    def _favorites_changed(self, items):
        try:
            ds = [DVCConnectionItem(attrs=f, load_names=False) for f in items]
            self.data_sources = [d for d in ds if d.enabled]

        except BaseException:
            pass

        if self.data_sources:
            self.data_source = next(
                (d for d in self.data_sources if d.default and d.enabled), None
            )

    def _data_source_changed(self, old, new):
        self.debug("data source changed. {}, db={}".format(new, id(self.db)))
        if new is not None:
            for attr in ("username", "password", "host", "kind", "path", "timeout"):
                setattr(self.db, attr, getattr(new, attr))

            self.db.name = new.dbname
            self.organization = new.organization
            self.meta_repo_name = new.meta_repo_name
            self.meta_repo_dirname = new.meta_repo_dir
            self.repository_root = new.repository_root
            self.db.reset_connection()
            if old:
                self.db.connect()
                self.db.create_session()

    def _repository_root_changed(self):
        if self.repository_root:
            paths.repository_dataset_dir = os.path.join(
                paths.dvc_dir, self.repository_root
            )

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
        self.debug("writing defaults")
        self.db.add_save_user()
        for tag, func in (
            ("irradiation holders", self._add_default_irradiation_holders),
            ("productions", self._add_default_irradiation_productions),
            ("load holders", self._add_default_load_holders),
        ):
            d = os.path.join(self.meta_repo.path, tag.replace(" ", "_"))
            if not os.path.isdir(d):
                os.mkdir(d)

            if self.auto_add:
                func()
            elif self.confirmation_dialog(
                "You have no {}. Would you like to add some defaults?".format(tag)
            ):
                func()

    def _add_default_irradiation_productions(self):
        ds = (("TRIGA.txt", TRIGA),)
        self._add_defaults(ds, "productions")

    def _add_default_irradiation_holders(self):
        ds = (("24Spokes.txt", HOLDER_24_SPOKES),)
        self._add_defaults(
            ds,
            "irradiation_holders",
        )

    def _add_default_load_holders(self):
        ds = (("221.txt", LASER221), ("65.txt", LASER65))
        self._add_defaults(ds, "load_holders", self.db.add_load_holder)

    def _add_defaults(self, defaults, root, dbfunc=None):
        commit = False
        repo = self.meta_repo
        for name, txt in defaults:
            p = os.path.join(repo.path, root, name)
            if not os.path.isfile(p):
                with open(p, "w") as wfile:
                    wfile.write(txt)
                repo.add(p, commit=False)
                commit = True
                if dbfunc:
                    name = remove_extension(name)
                    dbfunc(name)

        if commit:
            repo.commit("added default {}".format(root.replace("_", " ")))

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
        return DVCDatabase(
            kind="mysql",
            username="root",
            password="Argon",
            host="localhost",
            name="pychronmeta",
        )

    def _meta_repo_default(self):
        return MetaRepo(application=self.application)


if __name__ == "__main__":
    paths.build("_dev")
    idn = "24138"
    exps = ["Irradiation-NM-272"]
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
