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

from traits.api import Str, Button, List
from traitsui.api import View, UItem, VGroup
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.filetools import unique_path2
from pychron.core.progress import progress_iterator, open_progress
from pychron.envisage.browser.record_views import RepositoryRecordView
from pychron.loggable import Loggable
from pychron.paths import paths


def database_path():
    return '/Users/ross/Desktop/index.sqlite3'
    return os.path.join(paths.dvc_dir, 'index.sqlite3')


def switch_to_offline_database(preferences):
    prefid = 'pychron.dvc.db'
    kind = '{}.kind'.format(prefid)
    path = '{}.path'.format(prefid)

    preferences.set(kind, 'sqlite')
    preferences.set(path, database_path())
    preferences.save()


class RepositoryTabularAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Create Date', 'created_at'),
               ('Last Change', 'pushed_at')]


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

    work_offline_button = Button('Work Offline')

    def initialize(self):
        """
        check internet connection.
            a. check database
            b. check github
        """

        if self._load_preferences():
            if self._check_database_connection():
                if self._check_githost_connection():
                    # attributes = ('name',
                    #               'created_at',
                    #               'pushed_at')
                    repos = self.dvc.remote_repositories()
                    repos = [RepositoryRecordView(name=r['name'],
                                                  created_at=r['created_at'],
                                                  pushed_at=r['pushed_at']) for r in repos]

                    metaname = os.path.basename(paths.meta_root)
                    repos = sorted([ri for ri in repos if ri.name != metaname])
                    self.repositories = repos
                    return True

    # private
    def _load_preferences(self):
        # prefs = self.application.preferences
        # prefid = 'pychron.dvc'

        # for label in ('host', 'user', 'password'):
        #     attr = 'work_offline_{}'.format(label)
        #     v = prefs.get('{}.{}'.format(prefid, attr))
        #     if not v:
        #         self.warning_dialog('No WorkOffline {} set in preferences'.format(label))
        #         return
        #     setattr(self, attr, v)

        return True

    def _check_database_connection(self):
        return self.dvc.connect()

    def _check_githost_connection(self):
        return self.dvc.check_githost_connection()

    def _work_offline(self):
        self.debug('work offline')

        # clone repositories
        if not self._clone_repositories():
            return

        # update meta
        self.dvc.open_meta_repo()
        self.dvc.meta_pull()

        # clone central db

        repos = [ri.name for ri in self.selected_repositories]
        if not self._clone_central_db(repos):
            return

        msg = 'Would you like to switch to the offline database?'
        if self.confirmation_dialog(msg):
            # update DVC preferences
            self._update_preferences()

    def _clone_repositories(self):
        self.debug('clone repositories')

        # check for selected repositories
        if not self.selected_repositories:
            return

        # clone the repositories
        def func(x, prog, i, n):
            if prog is not None:
                prog.change_message('Cloning {}'.format(x.name))
            self.dvc.clone_repository(x.name)

        progress_iterator(self.selected_repositories, func, threshold=0)

        return True

    def _get_new_path(self):
        return unique_path2(paths.dvc_dir, 'index', extension='.sqlite3')[0]

    def _clone_central_db(self, repositories, analyses=None, principal_investigators=None, projects=None):

        self.info('--------- Clone DB -----------')
        # create an a sqlite database
        from pychron.dvc.dvc_orm import Base
        metadata = Base.metadata
        from pychron.dvc.dvc_database import DVCDatabase

        path = database_path()
        if os.path.isfile(path):
            if not self.confirmation_dialog('The database "{}" already exists. '
                                            'Do you want to overwrite it. If "NO" you will be prompted to '
                                            'enter and new database name'.format(path)):

                path = self._get_new_path()
            else:
                os.remove(path)

        if path:
            progress = open_progress(n=20)
            self.debug('--------- Starting db clone to {}'.format(path))
            src = self.dvc
            db = DVCDatabase(path=path, kind='sqlite')
            db.connect()
            with db.session_ctx(use_parent_session=False) as sess:
                metadata.create_all(sess.bind)

            tables = ['ProductionTbl', 'MassSpectrometerTbl', 'ExtractDeviceTbl', 'VersionTbl', 'UserTbl']

            for table in tables:
                mod = __import__('pychron.dvc.dvc_orm', fromlist=[table])
                progress.change_message('Cloning {}'.format(table))
                self._copy_table(db, getattr(mod, table))

            with src.session_ctx(use_parent_session=False):
                from pychron.dvc.dvc_orm import RepositoryTbl
                from pychron.dvc.dvc_orm import AnalysisTbl
                from pychron.dvc.dvc_orm import AnalysisChangeTbl
                from pychron.dvc.dvc_orm import RepositoryAssociationTbl
                from pychron.dvc.dvc_orm import AnalysisGroupTbl
                from pychron.dvc.dvc_orm import AnalysisGroupSetTbl

                repos = [src.db.get_repository(reponame) for reponame in repositories]

                progress.change_message('Assembling Analyses 0/5')
                st = time.time()
                if analyses:
                    ans = analyses
                    ras = [rai for ai in ans
                           for rai in ai.repository_associations]
                else:

                    at = time.time()
                    ras = [ra for repo in repos for ra in repo.repository_associations]
                    self.debug('association time={}'.format(time.time()-at))
                    progress.change_message('Assembling Analyses 1/5')

                    at = time.time()
                    ans = [ri.analysis for ri in ras]
                    self.debug('analysis time={}'.format(time.time()-at))

                    progress.change_message('Assembling Analyses 2/5')

                at = time.time()
                ans_c = [ai.change for ai in ans]
                self.debug('change time={}'.format(time.time()-at))
                progress.change_message('Assembling Analyses 3/5')

                at = time.time()
                agss = [gi for ai in ans for gi in ai.group_sets]
                self.debug('agss time={}'.format(time.time()-at))
                progress.change_message('Assembling Analyses 4/5')

                at = time.time()
                ags = {gi.group for gi in agss}
                self.debug('ags time={}'.format(time.time()-at))
                progress.change_message('Assembling Analyses 5/5')

                self.debug('total analysis assembly time={}'.format(time.time()-st))

                self._copy_records(progress, db, RepositoryTbl, repos)
                self._copy_records(progress, db, RepositoryAssociationTbl, ras)
                self._copy_records(progress, db, AnalysisTbl, ans)
                self._copy_records(progress, db, AnalysisChangeTbl, ans_c)
                self._copy_records(progress, db, AnalysisGroupTbl, ags)
                self._copy_records(progress, db, AnalysisGroupSetTbl, agss)

                from pychron.dvc.dvc_orm import PrincipalInvestigatorTbl
                if principal_investigators:
                    pis = [src.get_principal_investigator(pp.name) for pp in principal_investigators]
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
                from pychron.dvc.dvc_orm import IrradiationPositionTbl
                self._copy_records(progress, db, IrradiationPositionTbl, ips)

                from pychron.dvc.dvc_orm import LevelTbl
                ls = {ip.level for ip in ips}
                self._copy_records(progress, db, LevelTbl, ls)

                from pychron.dvc.dvc_orm import IrradiationTbl
                irs = {l.irradiation for l in ls}
                self._copy_records(progress, db, IrradiationTbl, irs)

                from pychron.dvc.dvc_orm import SampleTbl
                sams = {ip.sample for ip in ips}
                self._copy_records(progress, db, SampleTbl, sams)

                from pychron.dvc.dvc_orm import MaterialTbl
                mats = {si.material for si in sams}
                self._copy_records(progress, db, MaterialTbl, mats)
                self.debug('--------- db clone finished')
                progress.close()
                return True

    def _copy_records(self, progress, dest, table, records):

        st = time.time()
        msg = 'Copying records from {}. n={}'.format(table.__tablename__, len(records))
        self.debug(msg)
        progress.change_message(msg)

        with dest.session_ctx(use_parent_session=False) as dest_sess:
            keys = table.__table__.columns.keys()
            mappings = ({k: getattr(row, k) for k in keys} for row in records)
            dest_sess.bulk_insert_mappings(table, mappings)
            dest_sess.commit()
        self.debug('copy finished et={:0.5f}'.format(time.time()-st))

    def _copy_table(self, dest, table, filter_criterion=None):
        src = self.dvc
        with src.session_ctx(use_parent_session=False) as src_sess:
            query = src_sess.query(table)
            if filter_criterion:
                query = query.filter(filter_criterion)

            with dest.session_ctx(use_parent_session=False) as dest_sess:
                keys = table.__table__.columns.keys()
                mappings = [{k: getattr(row, k) for k in keys} for row in query]
                dest_sess.bulk_insert_mappings(table, mappings)
                dest_sess.commit()

    def _update_preferences(self):
        self.debug('update dvc preferences')

        switch_to_offline_database(self.application.preferences)

    # handlers
    def _work_offline_button_fired(self):
        self.debug('work offline fired')
        self._work_offline()

    def traits_view(self):
        v = View(VGroup(UItem('repositories',
                              editor=TabularEditor(adapter=RepositoryTabularAdapter(),
                                                   selected='selected_repositories',
                                                   multi_select=True)),
                        UItem('work_offline_button',
                              enabled_when='selected_repositories')),
                 title='Work Offline',
                 resizable=True,
                 width=500, height=500)
        return v

# ============= EOF =============================================
# """
# use mysql2sqlite.sh. this script requires mysqldump so maybe not the
# best option.
#
# another solution is to have the server convert the database to sqlite
# then grab the sqlite file from the server
#
# use ssh to run mysql2sqlite.sh
# use ftp to grab the file
# """
# self.debug('clone central db')
#
# # dump the mysql database to sqlite
# ssh = paramiko.SSHClient()
# ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#
# ssh.connect(self.work_offline_host,
#             username=self.work_offline_user,
#             password=self.work_offline_password,
#             allow_agent=False,
#             look_for_keys=False)
#
# cmd = '/Users/{}/workoffline/workoffline.sh'.format(self.work_offline_user)
# stdin, stdout, stderr = ssh.exec_command(cmd)
# self.debug('============ Output ============')
# for line in stdout:
#     self.debug(line)
# self.debug('============ Output ============')
#
# self.debug('============ Error ============')
# for line in stderr:
#     self.debug('****** {}'.format(line))
# self.debug('============ Error ============')
#
# # fetch the sqlite file
# ftp = ssh.open_sftp()
# rp = '/Users/{}/workoffline/database.sqlite3'.format(self.work_offline_user)
#
# ftp.get(rp, database_path())
