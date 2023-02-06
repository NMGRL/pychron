# ===============================================================================
# Copyright 2016 Jake Ross
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
import os
import time
from operator import attrgetter

import yaml
from apptools.preferences.preference_binding import bind_preference
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import Str, Button, List, Instance
from traitsui.api import View, UItem, VGroup, SetEditor, Item
from traitsui.menu import Action, ToolBar
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.core.progress import progress_iterator, open_progress
from pychron.core.pychron_traits import BorderVGroup
from pychron.dvc.dvc import DVC

# from pychron.envisage.browser.record_views import RepositoryRecordView
from pychron.git.hosts import IGitHost
from pychron.git.hosts.github import GitHubService
from pychron.loggable import Loggable
from pychron.paths import paths


def database_path():
    return os.path.join(paths.offline_db_dir, "index.sqlite3")


def switch_to_offline_database(preferences):
    prefid = "pychron.dvc.connection"
    kind = "{}.kind".format(prefid)
    path = "{}.path".format(prefid)

    preferences.set(kind, "sqlite")
    preferences.set(path, database_path())
    preferences.save()


# class RepositoryTabularAdapter(TabularAdapter):
#     columns = [
#         ("Name", "name"),
#         ("Create Date", "created_at"),
#         ("Last Change", "pushed_at"),
#     ]


class WorkOffline(Loggable):
    """
    1. Select set of repositories
    2. clone repositories
    3. update the meta repo
    4. copy the central db to a sqlite db
    5. set DVC db preferences to sqlite
    """

    work_offline_user = Str
    work_offline_password = Str

    repositories = List
    selected_repositories = List

    work_offline_button = Button("Work Offline")
    dvc = Instance(DVC)

    lab_name = Str
    username = Str
    description = Str
    tags = Str

    def load_repos(self):
        if self.dvc:
            repos = self.dvc.remote_repositories()
        else:
            repos = [
                {"name": "Foo", "created_at": "2021-10-28 13:23:05,286 "},
                {"name": "Basdfarefasdasdc", "created_at": "2021-10-28 13:23:05,286 "},
            ]

        repos = [r["name"] for r in repos]

        metaname = "MetaData"
        if paths.meta_root:
            metaname = os.path.basename(paths.meta_root)

        repos = sorted([ri for ri in repos if ri != metaname])
        self.repositories = repos

    def initialize(self):
        """
        check internet connection.
            a. check database
            b. check github
        """
        bind_preference(self, "lab_name", "pychron.general.lab_name")
        bind_preference(self, "username", "pychron.general.username")

        if self._check_database_connection():
            if self._check_githost_connection():
                self.load_repos()
                return True

    # private
    def _check_database_connection(self):
        return self.dvc.connect()

    def _check_githost_connection(self):
        return self.dvc.check_githost_connection()

    def _work_offline(self):
        self.debug("work offline")

        # clone repositories
        if not self._clone_repositories():
            return

        # update meta
        self.dvc.open_meta_repo()
        self.dvc.meta_pull()

        # clone central db
        repos = [ri for ri in self.selected_repositories]
        path = self._clone_central_db(repos)
        if not path:
            return

        apath = None
        # create dvc archive
        if self.confirmation_dialog("Create shareable archive"):
            dialog = FileDialog(action="save as", default_directory=paths.data_dir)
            if dialog.open() == OK:
                apath = dialog.path

        if apath:
            apath = add_extension(apath, ".pz")
            with open(apath, "wb") as wfile:
                with open(path, "rb") as dbfile:
                    ctx = {
                        "meta_repo_name": self.dvc.meta_repo_name,
                        "meta_repo_dirname": self.dvc.meta_repo_dirname,
                        "organization": self.dvc.organization,
                        "database": dbfile.read(),
                        "metadata": {
                            "tags": self.tags.split(","),
                            "description": self.description,
                        },
                    }
                yaml.dump(ctx, wfile, encoding="utf-8")
                content = yaml.dump(ctx, encoding="utf-8")

                # try to share with PychronLabsLLC/pzdata
                gh = self.application.get_services(GitHubService)
                if gh is not None:
                    upath = os.path.join(
                        self.lab_name or "NoLab", os.path.basename(apath)
                    )
                    gh.post_file(
                        "PychronLabsLLC/pzdata",
                        upath,
                        content,
                        committer_name=self.username,
                    )

        # msg = 'Would you like to switch to the offline database?'
        # if self.confirmation_dialog(msg):
        #     # update DVC preferences
        #     self._update_preferences()

    def _clone_repositories(self):
        self.debug("clone repositories")

        # check for selected repositories
        if not self.selected_repositories:
            return

        # clone the repositories
        def func(x, prog, i, n):
            if prog is not None:
                prog.change_message("Cloning {} {}/{}".format(x, i, n))
            self.dvc.clone_repository(x)

        progress_iterator(self.selected_repositories, func, threshold=0)

        return True

    def _get_new_path(self):
        return unique_path2(paths.dvc_dir, "index", extension=".sqlite3")[0]

    def _clone_central_db(
        self, repositories, analyses=None, principal_investigators=None, projects=None
    ):
        self.info("--------- Clone DB -----------")
        # create an a sqlite database
        from pychron.dvc.dvc_orm import Base

        metadata = Base.metadata
        from pychron.dvc.dvc_database import DVCDatabase

        path = database_path()
        if os.path.isfile(path):
            if not self.confirmation_dialog(
                'The database "{}" already exists. '
                "Do you want to overwrite it".format(os.path.basename(path))
            ):
                path = self._get_new_path()
            else:
                os.remove(path)

        if path:
            progress = open_progress(n=20)
            self.debug("--------- Starting db clone to {}".format(path))
            src = self.dvc
            db = DVCDatabase(path=path, kind="sqlite")
            db.connect()
            with db.session_ctx(use_parent_session=False) as sess:
                metadata.create_all(sess.bind)

            tables = [
                "MassSpectrometerTbl",
                "ExtractDeviceTbl",
                "VersionTbl",
                "UserTbl",
            ]

            for table in tables:
                mod = __import__("pychron.dvc.dvc_orm", fromlist=[table])
                progress.change_message("Cloning {}".format(table))
                self._copy_table(db, getattr(mod, table))

            with src.session_ctx(use_parent_session=False):
                from pychron.dvc.dvc_orm import (
                    RepositoryTbl,
                    AnalysisTbl,
                    AnalysisChangeTbl,
                    RepositoryAssociationTbl,
                    AnalysisGroupTbl,
                    AnalysisGroupSetTbl,
                    MaterialTbl,
                    SampleTbl,
                    IrradiationTbl,
                    LevelTbl,
                    IrradiationPositionTbl,
                    PrincipalInvestigatorTbl,
                    MeasuredPositionTbl,
                    LoadTbl,
                )

                repos = [src.db.get_repository(reponame) for reponame in repositories]

                progress.change_message("Assembling Analyses 0/5")
                st = time.time()
                if analyses:
                    ans = analyses
                    ras = [rai for ai in ans for rai in ai.repository_associations]
                else:
                    # at = time.time()
                    ras = [ra for repo in repos for ra in repo.repository_associations]
                    # self.debug('association time={}'.format(time.time()-at))
                    progress.change_message("Assembling Analyses 1/5")

                    # at = time.time()
                    ans = [ri.analysis for ri in ras]
                    # self.debug('analysis time={}'.format(time.time()-at))

                    progress.change_message("Assembling Analyses 2/5")

                # at = time.time()
                ans = [ai for ai in ans if ai is not None]
                mps = [mp for ai in ans for mp in ai.measured_positions]

                seen = set()
                mps = [seen.add(mp.id) or mp for mp in mps if mp.id not in seen]
                ls = {mp.load for mp in mps}

                ans_c = [ai.change for ai in ans]
                # self.debug('change time={}'.format(time.time()-at))
                progress.change_message("Assembling Analyses 3/5")

                # at = time.time()
                agss = [gi for ai in ans for gi in ai.group_sets]
                # self.debug('agss time={}'.format(time.time()-at))
                progress.change_message("Assembling Analyses 4/5")

                # at = time.time()
                ags = {gi.group for gi in agss}
                # self.debug('ags time={}'.format(time.time()-at))
                progress.change_message("Assembling Analyses 5/5")

                self.debug("total analysis assembly time={}".format(time.time() - st))

                self._copy_records(progress, db, RepositoryTbl, repos)
                self._copy_records(progress, db, RepositoryAssociationTbl, ras)
                self._copy_records(progress, db, AnalysisTbl, ans)
                self._copy_records(progress, db, AnalysisChangeTbl, ans_c)
                self._copy_records(progress, db, AnalysisGroupTbl, ags)
                self._copy_records(progress, db, AnalysisGroupSetTbl, agss)
                self._copy_records(progress, db, LoadTbl, ls)
                self._copy_records(progress, db, MeasuredPositionTbl, mps)

                if principal_investigators:
                    pis = [
                        src.get_principal_investigator(pp.name)
                        for pp in principal_investigators
                    ]
                else:
                    pis = {repo.principal_investigator for repo in repos}
                self._copy_records(progress, db, PrincipalInvestigatorTbl, pis)

                from pychron.dvc.dvc_orm import ProjectTbl

                if projects:
                    prjs = [src.get_project(pp) for pp in projects]
                else:
                    prjs = {ai.irradiation_position.sample.project for ai in ans}
                self._copy_records(progress, db, ProjectTbl, prjs)

                ips = {ai.irradiation_position for ai in ans}
                sams = {ip.sample for ip in ips}
                mats = {si.material for si in sams}

                self._copy_records(progress, db, MaterialTbl, mats)

                self._copy_records(progress, db, SampleTbl, sams)

                ls = {ip.level for ip in ips}
                irs = {l.irradiation for l in ls}

                self._copy_records(progress, db, IrradiationTbl, irs)

                self._copy_records(progress, db, LevelTbl, ls)

                self._copy_records(progress, db, IrradiationPositionTbl, ips)

                self.debug("--------- db clone finished")
                progress.close()
                self.information_dialog('Database saved to "{}"'.format(path))
                return path

    def _copy_records(self, progress, dest, table, records):
        st = time.time()
        msg = "Copying records from {}. n={}".format(table.__tablename__, len(records))
        self.debug(msg)
        progress.change_message(msg)

        with dest.session_ctx(use_parent_session=False) as dest_sess:
            keys = list(table.__table__.columns.keys())
            mappings = (
                {k: getattr(row, k) for k in keys} for row in records if row is not None
            )
            dest_sess.bulk_insert_mappings(table, mappings)
            dest_sess.commit()
        self.debug("copy finished et={:0.5f}".format(time.time() - st))

    def _copy_table(self, dest, table, filter_criterion=None):
        src = self.dvc
        with src.session_ctx(use_parent_session=False) as src_sess:
            query = src_sess.query(table)
            if filter_criterion:
                query = query.filter(filter_criterion)

            with dest.session_ctx(use_parent_session=False) as dest_sess:
                keys = list(table.__table__.columns.keys())
                mappings = [{k: getattr(row, k) for k in keys} for row in query]
                dest_sess.bulk_insert_mappings(table, mappings)
                dest_sess.commit()

    def _update_preferences(self):
        self.debug("update dvc preferences")

        switch_to_offline_database(self.application.preferences)

    # handlers
    def select_references(self):
        self.debug("select references for {}".format(self.selected_repositories))
        nrepos = []
        for repo in self.selected_repositories:
            arepos = self.dvc.find_reference_repos(repo)
            self.debug("found {} for {}".format(arepos, repo))
            nrepos.extend(arepos)
        nrepos = list(set(nrepos))

        self.selected_repositories.extend(nrepos)

    def _work_offline_button_fired(self):
        self.debug("work offline fired")
        self._work_offline()

    def traits_view(self):
        v = View(
            VGroup(
                # UItem(
                #     "repositories",
                #     editor=TabularEditor(
                #         adapter=RepositoryTabularAdapter(),
                #         selected="selected_repositories",
                #         multi_select=True,
                #     ),
                # ),
                UItem(
                    "selected_repositories",
                    editor=SetEditor(name="repositories", can_move_all=False),
                ),
                BorderVGroup(
                    UItem(
                        "description",
                        style="custom",
                        tooltip="Provide a description of this dataset to "
                        "make it easier to identifier ",
                    ),
                    label="Description",
                ),
                BorderVGroup(
                    UItem(
                        "tags",
                        tooltip="Provide a list of tags for this dataset, e.g. sanidine,"
                        "san juan volcanic field.   Use commas (,) to add multiple tags",
                    ),
                    label="Tags",
                ),
                UItem("work_offline_button", enabled_when="selected_repositories"),
            ),
            toolbar=ToolBar(
                Action(name="Select References", action="select_references")
            ),
            title="Work Offline",
            resizable=True,
            width=500,
            height=500,
        )
        return v


if __name__ == "__main__":
    w = WorkOffline()

    w.load_repos()
    w.configure_traits()
# ============= EOF =============================================
