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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from __future__ import absolute_import

import json
import os

import requests
from requests.exceptions import SSLError

from pychron.git.hosts import GitHostService
from pychron.paths import paths

BASE_URL = "github.com"
API_URL = "https://api.github.com"


class GitHubService(GitHostService):
    preference_path = "pychron.github"
    name = "GitHub"
    _has_access = True
    protocol = "https"

    def _set_authentication_windows_hook(self):
        if not self.disable_authentication_message:
            self.information_dialog(
                "Please follow the directions at https://github.com/NMGRL/pychron/wiki/Windows-Setup "
                "to ensure you can share your changes to github. Use Preferences/Github to hide "
                "this message"
            )

    @property
    def remote_url(self):
        return "{}://{}".format(self.protocol, BASE_URL)

    def up_to_date(self, organization, name, sha, branch="master"):
        cmd = "{}/repos/{}/{}/commits/{}".format(API_URL, organization, name, branch)
        close_at_end = False
        if not self._session:
            self.new_session()
            close_at_end = True

        self._session.headers.update(
            ETag=sha, Accept="application/vnd.github.VERSION.sha"
        )

        r = self._session.get(cmd)
        rsha = r.text
        ret = rsha != sha

        if close_at_end:
            self.close_session()
        return ret, rsha

    def post_file(self, remote, path, content, committer_name, committer_email=None):
        if committer_email is None:
            cn = committer_name.replace(" ", "_")
            committer_email = f"{cn}@gmail.com"

        url = f"{API_URL}/repos/{remote}/contents/{path}"

        try:
            self._put(
                url,
                message="Created shareable archive",
                commiter={"name": committer_name, "email": committer_email},
                content=content,
            )
        except BaseException:
            self.debug_exception()

    def post_issue(self, remote, issue):
        url = "{}/repos/{}/issues".format(API_URL, remote)
        return self._post(url, issue)

    def get_labels(self, remote):
        cmd = "{}/repos/{}/labels".format(API_URL, remote)
        return self._get(cmd)

    def get_repo(self, organization, name):
        cmd = "{}/repos/{}/{}".format(API_URL, organization, name)
        resp = self._get(cmd)
        try:
            return resp[0]
        except IndexError:
            pass

    def test_api(self):
        ret, err = True, ""
        try:
            self._get(API_URL)
        except BaseException as e:
            ret = False
            err = str(e)

        return ret, err

    def set_team(self, team, organization, repo, permission=None):
        if permission is None:
            permission = "pull"

        team_id = self.get_team_id(team, organization)
        if team_id:
            cmd = "{}/teams/{}/repos/{}/{}".format(API_URL, team_id, organization, repo)
            self._put(cmd, permission=permission)

    def get_team_id(self, name, organization):
        for td in self._get("{}/orgs/{}/teams".format(API_URL, organization)):
            if td["name"] == name:
                return td["id"]

    def create_repo(self, name, organization, **kw):
        if self._has_access:
            try:
                cmd = "{}/orgs/{}/repos".format(API_URL, organization)
                resp = self._post(cmd, name=name, **kw)
                if resp:
                    self.debug("Create repo response {}".format(resp.status_code))
                    self._cached_repos = []
                    return resp.status_code == 201
            except SSLError as e:
                self.warning("SSL Error. {}".format(e))
                self._has_access = False
        else:
            return True

    def make_url(self, name, organization, protocol=None):
        if protocol is None:
            protocol = self.protocol

        auth = ""
        # including the authenitcation when cloning presents an issue when cloning a repository
        # you only have read-only access to
        if organization == self.organization:
            p = paths.oauth_file
            if os.path.isfile(p):
                with open(p, "r") as rfile:
                    obj = json.load(rfile)
                    obj = obj["installed"]
                    token = obj["token"]
                    auth = "{}@".format(token)
            elif self.oauth_token:
                auth = "{}@".format(self.oauth_token)
            elif self.username and self.password:
                auth = "{}:{}@".format(self.username, self.password)

        url = "{}://{}{}/{}/{}.git".format(protocol, auth, BASE_URL, organization, name)
        return url

    def get_repos(self, organization):
        if self._has_access:
            if not self._cached_repos:
                try:
                    cmd = "{}/orgs/{}/repos".format(API_URL, organization)
                    repos = self._get(cmd)
                    self._cached_repos = repos
                    return repos
                except SSLError as e:
                    self.warning("SSL Error. {}".format(e))
                    self._has_access = False
                    return []
            else:
                return self._cached_repos
        else:
            return []

    def get_info(self, organization):
        cmd = "{}/{}".format(API_URL, organization)
        return self._get(cmd)

    # private
    def _get_oauth_token(self):
        return "token {}".format(self.oauth_token)


# ============= EOF =============================================
